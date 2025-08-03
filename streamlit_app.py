import streamlit as st
import os
import tempfile
import zipfile
from datetime import datetime

# Fix for Streamlit Cloud SQLite3 issue
try:
    import sqlite3
    # Check if we need to use pysqlite3-binary
    if sqlite3.sqlite_version_info < (3, 35, 0):
        import pysqlite3
        import sys
        sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
import re
import requests
from typing import Type
from pydantic import BaseModel, Field

# ======================
# Google Scholar Tool (Same as researcherkilo.py)
# ======================
class GoogleScholarSearchInput(BaseModel):
    """Input schema for Google Scholar search via Serper.dev."""
    query: str = Field(..., description="Search query for Google Scholar")
    years_back: int = Field(default=3, description="Number of years back to search (default: 3)")

class GoogleScholarTool(BaseTool):
    name: str = "google_scholar_search"
    description: str = "Search Google Scholar for academic papers and research publications using Serper.dev API."
    args_schema: Type[BaseModel] = GoogleScholarSearchInput
    
    def __init__(self, serper_api_key):
        super().__init__()
        self.serper_api_key = serper_api_key
    
    def _run(self, query: str, years_back: int = 3) -> str:
        """Search Google Scholar using Serper.dev API"""
        try:
            if not self.serper_api_key:
                return "❌ SERPER_API_KEY not provided"
            
            # Calculate year range
            current_year = datetime.now().year
            start_year = current_year - years_back
            
            # Serper.dev API endpoint for Google Scholar
            url = "https://google.serper.dev/scholar"
            
            # Headers for Serper.dev
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            # Payload for Serper.dev Scholar API
            payload = {
                "q": query,
                "num": 6,  # Number of results
                "hl": "en"  # Language
            }
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code != 200:
                return f"❌ API request failed with status {response.status_code}: {response.text}"
            
            data = response.json()
            
            # Check if we have results
            if "organic" not in data or not data["organic"]:
                return f"🔬 No Google Scholar results found for '{query}'. Try a different search term."
            
            # Format results
            formatted_results = []
            for result in data["organic"][:6]:  # Top 6 results
                title = result.get("title", "")
                link = result.get("link", "")
                snippet = result.get("snippet", "")
                
                # Extract publication info if available
                publication_info = result.get("publicationInfo", {})
                authors = publication_info.get("authors", "")
                
                # Extract year from snippet or publication info
                year = ""
                if publication_info and "year" in publication_info:
                    year = str(publication_info["year"])
                elif snippet:
                    # Try to extract year from snippet (common format: "- 2023 - ...")
                    year_match = re.search(r'\b(20\d{2})\b', snippet)
                    if year_match:
                        year = year_match.group(1)
                
                # Get citation count if available
                citations = 0
                if "citedBy" in result:
                    citations = result["citedBy"].get("total", 0)
                
                # Format result
                result_text = f"📄 **{title}**\n"
                if link:
                    result_text += f"   Link: {link}\n"
                if authors:
                    result_text += f"   Authors: {authors}\n"
                if year:
                    result_text += f"   Year: {year}\n"
                if citations > 0:
                    result_text += f"   Citations: {citations}\n"
                if snippet:
                    result_text += f"   Abstract: {snippet}\n"
                result_text += "\n"
                
                # Filter by year if specified and we found a year
                if year and year.isdigit() and int(year) >= start_year:
                    formatted_results.append(result_text)
                elif not year:  # Include results without clear year info
                    formatted_results.append(result_text)
            
            if formatted_results:
                return f"🔬 **Google Scholar Results for '{query}' (via Serper.dev):**\n\n" + "\n".join(formatted_results)
            else:
                return f"🔬 No recent Google Scholar results found for '{query}' from the last {years_back} years."
                
        except requests.exceptions.Timeout:
            return "❌ Google Scholar search timed out. Try again."
        except requests.exceptions.RequestException as e:
            return f"❌ Network error during Google Scholar search: {str(e)}"
        except Exception as e:
            return f"❌ Google Scholar search failed: {str(e)}"

# ======================
# Streamlit Multi-Agent Content Creator
# ======================
class StreamlitMultiAgentContentCreator:
    """Streamlit version of multi-agent content creator"""
    
    def __init__(self, groq_api_key, serper_api_key):
        # LLM Configurations
        self.research_llm = LLM(
            model="groq/qwen/qwen3-32b",
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=3000
        )
        
        self.content_llm = LLM(
            model="groq/deepseek-r1-distill-llama-70b",
            api_key=groq_api_key,
            temperature=0.6,
            max_tokens=4000
        )
        
        self.social_llm = LLM(
            model="groq/deepseek-r1-distill-llama-70b",
            api_key=groq_api_key,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Initialize tools
        self.scholar_tool = GoogleScholarTool(serper_api_key)
        self.serper_tool = SerperDevTool(api_key=serper_api_key)
        self.scraper_tool = ScrapeWebsiteTool()
        
        # Initialize agents
        self._create_agents()
    
    def _create_agents(self):
        """Create the three specialized agents"""
        
        # Research Agent
        self.researcher = Agent(
            role="Senior Research Analyst",
            goal="Conduct comprehensive research on '{topic}' using academic sources, web search, and content scraping to gather factual, up-to-date information.",
            backstory="""You are a meticulous research analyst with expertise in finding and synthesizing 
            information from multiple sources. You excel at:
            
            - Finding relevant academic papers and research studies
            - Gathering current industry data and statistics
            - Identifying credible sources and fact-checking information
            - Extracting key insights from complex documents
            - Organizing research findings in a structured manner
            - Distinguishing between reliable and unreliable sources
            
            You use Google Scholar for academic research, web search for current trends, 
            and content scraping for detailed information extraction. Your research forms 
            the foundation for all content creation.""",
            tools=[self.scholar_tool, self.serper_tool, self.scraper_tool],
            llm=self.research_llm,
            verbose=True,
            max_iter=4,
            max_rpm=6,
            allow_delegation=False
        )
        
        # Content Writer Agent
        self.content_writer = Agent(
            role="Senior Technical Content Writer",
            goal="Create comprehensive, engaging technical blog posts about '{topic}' based on research findings, with a focus on practical implementation and real-world applications.",
            backstory="""You are an experienced technical writer with 10+ years in data science 
            and technology. You specialize in:
            
            - Transforming complex research into accessible technical content
            - Writing comprehensive blog posts (1000-1500 words)
            - Including code examples and practical implementations
            - Explaining technical concepts with real-world analogies
            - Creating engaging introductions and compelling conclusions
            - Structuring content for maximum readability and impact
            - Balancing technical depth with accessibility
            
            You take research findings and craft them into compelling, informative 
            blog posts that provide genuine value to technical professionals. You write 
            from personal experience and include practical insights.""",
            tools=[],
            llm=self.content_llm,
            verbose=True,
            max_iter=3,
            max_rpm=4,
            allow_delegation=False
        )
        
        # Social Media Specialist
        self.social_media_specialist = Agent(
            role="Social Media Content Specialist",
            goal="Create engaging social media content for LinkedIn and Twitter in both English and Turkish, plus generate detailed MidJourney prompts for visual content about '{topic}'.",
            backstory="""You are a social media expert who specializes in technical content 
            for professional audiences. You excel at:
            
            - Adapting technical content for social media platforms
            - Creating engaging LinkedIn posts for professional networks
            - Crafting Twitter threads that capture attention
            - Translating content culturally for Turkish audiences
            - Generating detailed prompts for AI image generation
            - Using appropriate hashtags and calls-to-action
            - Maintaining brand voice across different platforms
            
            You take comprehensive blog content and transform it into bite-sized, 
            shareable content that drives engagement while maintaining technical accuracy. 
            You understand the nuances of different social platforms and cultural adaptation.""",
            tools=[],
            llm=self.social_llm,
            verbose=True,
            max_iter=2,
            max_rpm=4,
            allow_delegation=False
        )

    def create_research_task(self, topic):
        """Task for the research agent"""
        return Task(
            description=f"""
            Conduct comprehensive research on the topic: '{topic}'
            
            🔬 RESEARCH OBJECTIVES:
            
            1. ACADEMIC RESEARCH:
            - Use Google Scholar to find recent academic papers (last 3 years)
            - Look for research studies, whitepapers, and scientific publications
            - Focus on peer-reviewed sources and credible academic institutions
            - Extract key findings, methodologies, and conclusions
            
            2. INDUSTRY RESEARCH:
            - Use web search to find current industry trends and applications
            - Look for case studies, implementation examples, and best practices
            - Find statistics, market data, and recent developments
            - Identify leading companies and their approaches
            
            3. TECHNICAL RESEARCH:
            - Search for technical implementations, code repositories, and tutorials
            - Find practical examples and real-world applications
            - Look for tools, frameworks, and methodologies
            - Identify common challenges and solutions
            
            4. CONTENT SCRAPING:
            - Extract detailed information from relevant websites and articles
            - Gather specific examples, quotes, and technical details
            - Find supporting data and evidence
            
            DELIVERABLE FORMAT:
            Provide a comprehensive research report with:
            - Academic findings with citations
            - Industry trends and statistics
            - Technical implementations and examples
            - Key insights and takeaways
            - Credible sources and references
            
            Focus on factual, up-to-date information that will serve as the foundation 
            for creating high-quality technical content.
            """,
            expected_output="Comprehensive research report with academic sources, industry data, technical examples, and key insights about the topic",
            agent=self.researcher
        )

    def create_content_writing_task(self, topic):
        """Task for the content writer agent"""
        return Task(
            description=f"""
            Create a comprehensive technical blog post about '{topic}' based on the research findings.
            
            📝 CONTENT CREATION OBJECTIVES:
            
            1. BLOG POST STRUCTURE (1000-1500 words):
            - Compelling title and introduction
            - 3-4 main sections with clear subheadings
            - Technical depth with practical examples
            - Code snippets or pseudocode where relevant
            - Real-world applications and use cases
            - Challenges and solutions
            - Conclusion with key takeaways
            
            2. WRITING STYLE:
            - Technical but accessible to professionals
            - First-person perspective with personal insights
            - Include mathematical concepts or statistical methods if applicable
            - Reference specific tools, libraries, or frameworks
            - Share lessons learned and practical tips
            - Avoid marketing language - focus on substance
            
            3. CONTENT REQUIREMENTS:
            - Use research findings as the foundation
            - Include current statistics and data
            - Reference academic sources and industry examples
            - Provide actionable insights
            - Ensure technical accuracy
            - Make it engaging and valuable for readers
            
            4. FORMAT:
            - Use proper markdown formatting
            - Include clear headings and subheadings
            - Add code blocks where appropriate
            - Structure for easy reading and scanning
            
            Write as a practicing data scientist/technologist sharing genuine insights 
            and practical knowledge with fellow professionals.
            """,
            expected_output="Comprehensive technical blog post (1000-1500 words) with practical insights, code examples, and real-world applications",
            agent=self.content_writer
        )

    def create_social_media_task(self, topic):
        """Task for the social media specialist"""
        return Task(
            description=f"""
            Create engaging social media content and visual prompts for '{topic}' based on the blog post content.
            
            📱 SOCIAL MEDIA OBJECTIVES:
            
            1. LINKEDIN POSTS:
            - English: Professional post (250-300 words) for data science/tech professionals
            - Turkish: Culturally adapted version for Turkish business audience
            - Include key insights from the blog post
            - Add relevant hashtags (#DataScience #MachineLearning #AI #Technology)
            - Include call-to-action for engagement
            
            2. X/TWITTER POSTS:
            - English: Create 3-4 tweet thread with key insights and technical highlights
            - Turkish: Adapt the thread for Turkish tech community
            - Keep each tweet under 280 characters
            - Include code snippets or technical examples where possible
            - Use relevant hashtags and mentions
            
            3. MIDJOURNEY PROMPTS:
            - Create 3 detailed MidJourney prompts for technical blog visuals
            - Include technical elements (code, diagrams, data flows, AI concepts)
            - Specify aspect ratios (--ar 16:9 for blog headers, --ar 1:1 for social media)
            - Use professional tech aesthetics (dark themes, neon accents, clean minimal)
            - Include version and style parameters (--v 6 --style modern tech)
            
            4. CONTENT ADAPTATION:
            - Extract key points from the blog post
            - Adapt technical content for social media consumption
            - Maintain accuracy while making it engaging
            - Consider platform-specific best practices
            - Ensure cultural sensitivity for Turkish content
            
            Format your response:
            # LINKEDIN POSTS
            ## English
            [LinkedIn content]
            ## Turkish  
            [Turkish LinkedIn content]
            
            # X/TWITTER POSTS
            ## English
            [Twitter thread]
            ## Turkish
            [Turkish Twitter thread]
            
            # MIDJOURNEY PROMPTS
            [3 detailed MidJourney prompts with parameters]
            """,
            expected_output="Complete social media package with LinkedIn posts, Twitter threads (English & Turkish), and MidJourney prompts for visual content",
            agent=self.social_media_specialist
        )

    def create_content(self, topic, progress_callback=None):
        """Main function to create content using multi-agent system"""
        try:
            if progress_callback:
                progress_callback("Creating tasks for agents...")
            
            # Create tasks for each agent
            research_task = self.create_research_task(topic)
            content_task = self.create_content_writing_task(topic)
            social_task = self.create_social_media_task(topic)
            
            if progress_callback:
                progress_callback("Initializing multi-agent crew...")
            
            # Create multi-agent crew with sequential process
            crew = Crew(
                agents=[self.researcher, self.content_writer, self.social_media_specialist],
                tasks=[research_task, content_task, social_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=3
            )
            
            if progress_callback:
                progress_callback("Starting content creation process...")
            
            # Execute the multi-agent workflow
            results = crew.kickoff(inputs={"topic": topic})
            
            if progress_callback:
                progress_callback("Content creation completed! Preparing results...")
            
            # Extract individual results
            research_result = results.tasks_output[0] if hasattr(results, 'tasks_output') else "Research completed"
            content_result = results.tasks_output[1] if hasattr(results, 'tasks_output') else "Content completed"
            social_result = results.tasks_output[2] if hasattr(results, 'tasks_output') else "Social media completed"
            
            return {
                "research": research_result,
                "content": content_result,
                "social": social_result,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

# ======================
# Streamlit App
# ======================
def main():
    st.set_page_config(
        page_title="AI Content Creator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    /* Style the main title */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-title h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-title p {
        margin: 10px 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Enhance sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Style content sections */
    .content-section {
        background: white;
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    
    /* Style buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the background image at the top
    try:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.image("forstreamlit.png", use_column_width=True, caption="AI-Powered Content Creation")
    except:
        pass  # If image not found, continue without it
    
    # Header with styled container
    st.markdown("""
    <div class="main-title">
        <h1>🤖 AI-Powered Multi-Agent Content Creator</h1>
        <p>Transform single prompts into comprehensive, research-backed content packages</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for API Keys
    st.sidebar.header("🔑 API Configuration")
    st.sidebar.markdown("Enter your API keys to use the system:")
    
    groq_api_key = st.sidebar.text_input(
        "Groq API Key",
        type="password",
        help="Get your API key from https://console.groq.com/keys"
    )
    
    serper_api_key = st.sidebar.text_input(
        "Serper.dev API Key",
        type="password",
        help="Get your API key from https://serper.dev/api-key"
    )
    
    # Agent Information
    st.sidebar.header("🤖 Agent Architecture")
    st.sidebar.markdown("""
    **Research Agent**: Qwen/Qwen3-32B  
    *Academic research & data gathering*
    
    **Content Writer**: DeepSeek R1 70B  
    *Technical blog post creation*
    
    **Social Specialist**: DeepSeek R1 70B  
    *Social media content adaptation*
    """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Content Creation")
        
        # Topic input
        topic = st.text_area(
            "What do you want to write about?",
            placeholder="Enter your topic here... (e.g., 'Advanced RAG Techniques: From Basic Retrieval to Agentic RAG Systems')",
            height=100
        )
        
        # Example topics
        st.markdown("**🎯 Example Topics:**")
        example_topics = [
            "Advanced RAG Techniques: From Basic Retrieval to Agentic RAG Systems",
            "Understanding Transformer Architecture Through Implementation",
            "MLOps Best Practices: From Model Training to Production Deployment",
            "Vector Databases: The Foundation of Modern AI Applications",
            "What is Model Context Protocol (MCP)?"
        ]
        
        selected_example = st.selectbox("Or choose an example:", [""] + example_topics)
        if selected_example:
            topic = selected_example
            st.rerun()
        
        # Create content button
        if st.button("🚀 Create Content", type="primary", disabled=not (groq_api_key and serper_api_key and topic)):
            if not groq_api_key:
                st.error("Please enter your Groq API key")
            elif not serper_api_key:
                st.error("Please enter your Serper.dev API key")
            elif not topic or len(topic.strip()) < 5:
                st.error("Please enter a topic (minimum 5 characters)")
            else:
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(message):
                    status_text.text(message)
                
                # Initialize creator and run
                try:
                    creator = StreamlitMultiAgentContentCreator(groq_api_key, serper_api_key)
                    
                    progress_bar.progress(25)
                    update_progress("🔬 Research Agent gathering information...")
                    
                    result = creator.create_content(topic, update_progress)
                    
                    progress_bar.progress(100)
                    
                    if result["success"]:
                        st.success("✅ Content creation completed!")
                        
                        # Display results in tabs
                        tab1, tab2, tab3, tab4 = st.tabs(["📊 Research", "📝 Blog Post", "📱 Social Media", "📦 Download"])
                        
                        with tab1:
                            st.header("🔬 Research Findings")
                            st.markdown(str(result["research"]))
                        
                        with tab2:
                            st.header("📝 Technical Blog Post")
                            st.markdown(str(result["content"]))
                        
                        with tab3:
                            st.header("📱 Social Media Content")
                            st.markdown(str(result["social"]))
                        
                        with tab4:
                            st.header("📦 Download Content")
                            
                            # Create downloadable files
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
                            
                            # Create zip file with all content
                            zip_buffer = create_download_zip(topic, result, timestamp, safe_topic)
                            
                            st.download_button(
                                label="📥 Download Complete Package (ZIP)",
                                data=zip_buffer,
                                file_name=f"{safe_topic}_{timestamp}.zip",
                                mime="application/zip"
                            )
                            
                            # Individual downloads
                            st.download_button(
                                label="📊 Download Research Findings",
                                data=str(result["research"]),
                                file_name=f"research_findings_{timestamp}.md",
                                mime="text/markdown"
                            )
                            
                            st.download_button(
                                label="📝 Download Blog Post",
                                data=str(result["content"]),
                                file_name=f"blog_post_{timestamp}.md",
                                mime="text/markdown"
                            )
                            
                            st.download_button(
                                label="📱 Download Social Media Content",
                                data=str(result["social"]),
                                file_name=f"social_media_{timestamp}.md",
                                mime="text/markdown"
                            )
                    
                    else:
                        st.error(f"❌ Error: {result['error']}")
                        st.info("💡 Please check your API keys and try again.")
                
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    st.info("💡 Please check your API keys and internet connection.")
    
    with col2:
        st.header("ℹ️ How It Works")
        st.markdown("""
        **1. Research Phase**  
        🔬 Research Agent uses Qwen/Qwen3-32B to gather academic papers, industry data, and technical examples
        
        **2. Content Creation**  
        ✍️ Content Writer uses DeepSeek R1 to create comprehensive blog posts with practical insights
        
        **3. Social Adaptation**  
        📱 Social Specialist uses DeepSeek R1 to create engaging social media content
        
        **4. Output Generation**  
        📦 All content is packaged and ready for download
        """)
        
        st.header("🎯 What You Get")
        st.markdown("""
        - **📊 Research Report**: Academic sources & industry data
        - **📝 Blog Post**: 1000-1500 words with code examples
        - **💼 LinkedIn Posts**: Professional content (English & Turkish)
        - **🐦 Twitter Threads**: Engaging technical threads
        - **🎨 MidJourney Prompts**: Professional visual content prompts
        """)
        
        st.header("🔗 Get API Keys")
        st.markdown("""
        **Groq API** (Free tier available)  
        [Get API Key →](https://console.groq.com/keys)
        
        **Serper.dev** (Free 2500 searches)  
        [Get API Key →](https://serper.dev/api-key)
        """)

def create_download_zip(topic, result, timestamp, safe_topic):
    """Create a ZIP file with all content"""
    import io
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Research findings
        zip_file.writestr(
            f"01_research_findings.md",
            f"# Research Findings: {topic}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n{str(result['research'])}"
        )
        
        # Blog post
        zip_file.writestr(
            f"02_technical_blog_post.md",
            f"# {topic}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n{str(result['content'])}"
        )
        
        # Social media
        zip_file.writestr(
            f"03_social_media_content.md",
            f"# Social Media Content: {topic}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n{str(result['social'])}"
        )
        
        # Complete package
        zip_file.writestr(
            f"complete_content_package.md",
            f"""# Complete Multi-Agent Content Package: {topic}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Architecture:** Multi-Agent System
**Research Model:** Qwen/Qwen3-32B
**Content Model:** DeepSeek R1 Distill Llama 70B
**Social Model:** DeepSeek R1 Distill Llama 70B

---

# RESEARCH FINDINGS

{str(result['research'])}

---

# TECHNICAL BLOG POST

{str(result['content'])}

---

# SOCIAL MEDIA CONTENT

{str(result['social'])}
"""
        )
        
        # README
        zip_file.writestr(
            "README.md",
            f"""# Content Package: {topic}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files:
- `01_research_findings.md` - Research findings
- `02_technical_blog_post.md` - Main blog post
- `03_social_media_content.md` - Social media content
- `complete_content_package.md` - Everything combined

## Generated by:
AI-Powered Multi-Agent Content Creator
https://github.com/elandil2/blog-poster
"""
        )
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()