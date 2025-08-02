from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from dotenv import load_dotenv
import os
import re
import requests
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field

load_dotenv()

# ======================
# Google Scholar Tool (Same as before)
# ======================
class GoogleScholarSearchInput(BaseModel):
    """Input schema for Google Scholar search via Serper.dev."""
    query: str = Field(..., description="Search query for Google Scholar")
    years_back: int = Field(default=3, description="Number of years back to search (default: 3)")

class GoogleScholarTool(BaseTool):
    name: str = "google_scholar_search"
    description: str = "Search Google Scholar for academic papers and research publications using Serper.dev API."
    args_schema: Type[BaseModel] = GoogleScholarSearchInput
    
    def _run(self, query: str, years_back: int = 3) -> str:
        """Search Google Scholar using Serper.dev API"""
        try:
            # Get API key
            api_key = os.getenv("SERPER_API_KEY")
            if not api_key:
                return "❌ SERPER_API_KEY not found in environment variables"
            
            # Calculate year range
            current_year = datetime.now().year
            start_year = current_year - years_back
            
            # Serper.dev API endpoint for Google Scholar
            url = "https://google.serper.dev/scholar"
            
            # Headers for Serper.dev
            headers = {
                'X-API-KEY': api_key,
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
# LLM Configurations - Multi-Model Setup
# ======================

# Qwen 3-32B for Research (Fast and efficient for research tasks)
research_llm = LLM(
    model="groq/qwen/qwen3-32b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,  # Lower temperature for more focused research
    max_tokens=3000
)

# DeepSeek R1 for Content Creation (More creative and comprehensive)
content_llm = LLM(
    model="groq/deepseek-r1-distill-llama-70b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,  # Higher temperature for creative writing
    max_tokens=4000
)

# DeepSeek R1 for Social Media (Creative and engaging)
social_llm = LLM(
    model="groq/deepseek-r1-distill-llama-70b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,  # Higher temperature for engaging social content
    max_tokens=2000
)

# ======================
# Multi-Agent Content Creator Class
# ======================
class MultiAgentContentCreator:
    """Multi-agent content creator with specialized agents for different tasks"""
    
    def __init__(self):
        # Initialize tools
        self.scholar_tool = GoogleScholarTool()
        self.serper_tool = SerperDevTool()
        self.scraper_tool = ScrapeWebsiteTool()
        
        # Research Agent - Uses Qwen 3-32B for efficient research
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
            llm=research_llm,  # Qwen 3-32B for research
            verbose=True,
            max_iter=4,  # More iterations for thorough research
            max_rpm=6,
            allow_delegation=False
        )
        
        # Content Writer Agent - Uses DeepSeek R1 for creative writing
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
            tools=[],  # No tools needed, works with research findings
            llm=content_llm,  # DeepSeek R1 for content creation
            verbose=True,
            max_iter=3,
            max_rpm=4,
            allow_delegation=False
        )
        
        # Social Media Specialist - Uses DeepSeek R1 for engaging content
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
            tools=[],  # No tools needed, works with blog content
            llm=social_llm,  # DeepSeek R1 for social content
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

    def save_content_to_files(self, topic, research_result, content_result, social_result):
        """Save all content to organized files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        output_dir = f"multi_agent_content/{safe_topic}_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n💾 Saving multi-agent content to: {output_dir}")
        
        # Save research findings
        with open(f"{output_dir}/01_research_findings.md", "w", encoding="utf-8") as f:
            f.write(f"# Research Findings: {topic}\n\n")
            f.write(f"*Generated by Research Agent (Qwen 3-32B) on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(str(research_result))
        print("✅ Saved: 01_research_findings.md")
        
        # Save main blog post
        with open(f"{output_dir}/02_technical_blog_post.md", "w", encoding="utf-8") as f:
            f.write(f"# {topic}\n\n")
            f.write(f"*Generated by Content Writer Agent (DeepSeek R1) on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(str(content_result))
        print("✅ Saved: 02_technical_blog_post.md")
        
        # Save social media content
        with open(f"{output_dir}/03_social_media_content.md", "w", encoding="utf-8") as f:
            f.write(f"# Social Media Content: {topic}\n\n")
            f.write(f"*Generated by Social Media Specialist (DeepSeek R1) on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(str(social_result))
        print("✅ Saved: 03_social_media_content.md")
        
        # Save complete package
        with open(f"{output_dir}/complete_multi_agent_content.md", "w", encoding="utf-8") as f:
            f.write(f"# Complete Multi-Agent Content Package: {topic}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Architecture:** Multi-Agent System\n")
            f.write(f"**Research Model:** Qwen 3-32B\n")
            f.write(f"**Content Model:** DeepSeek R1 Distill Llama 70B\n")
            f.write(f"**Social Model:** DeepSeek R1 Distill Llama 70B\n\n")
            f.write("---\n\n")
            f.write("# RESEARCH FINDINGS\n\n")
            f.write(str(research_result))
            f.write("\n\n---\n\n")
            f.write("# TECHNICAL BLOG POST\n\n")
            f.write(str(content_result))
            f.write("\n\n---\n\n")
            f.write("# SOCIAL MEDIA CONTENT\n\n")
            f.write(str(social_result))
        print("✅ Saved: complete_multi_agent_content.md")
        
        # Create comprehensive README
        with open(f"{output_dir}/README.md", "w", encoding="utf-8") as f:
            f.write(f"# Multi-Agent Content Package: {topic}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Architecture:** Multi-Agent System with Specialized LLMs\n\n")
            
            f.write("## 🤖 Agent Architecture:\n\n")
            f.write("- **Research Agent**: Qwen 3-32B (Efficient research and data gathering)\n")
            f.write("- **Content Writer**: DeepSeek R1 Distill Llama 70B (Creative technical writing)\n")
            f.write("- **Social Media Specialist**: DeepSeek R1 Distill Llama 70B (Engaging social content)\n\n")
            
            f.write("## 📁 Files Generated:\n\n")
            f.write("- ✅ `01_research_findings.md` - Comprehensive research by Research Agent\n")
            f.write("- ✅ `02_technical_blog_post.md` - **MAIN TECHNICAL BLOG** (1000-1500 words)\n")
            f.write("- ✅ `03_social_media_content.md` - LinkedIn & Twitter content + MidJourney prompts\n")
            f.write("- ✅ `complete_multi_agent_content.md` - All content in one file\n")
            f.write("- ✅ `README.md` - This file\n\n")
            
            f.write("## 🔬 Multi-Agent Workflow:\n\n")
            f.write("1. **Research Phase**: Research Agent gathers academic papers, industry data, and technical examples\n")
            f.write("2. **Content Creation**: Content Writer transforms research into comprehensive blog post\n")
            f.write("3. **Social Adaptation**: Social Media Specialist creates platform-specific content\n\n")
            
            f.write("## ✨ Content Features:\n\n")
            f.write("✅ **Research-Backed**: Academic sources + industry data\n")
            f.write("✅ **Technical Depth**: Code examples and practical implementation\n")
            f.write("✅ **Multi-Platform**: Blog, LinkedIn, Twitter content\n")
            f.write("✅ **Bilingual**: English and Turkish social media content\n")
            f.write("✅ **Visual Ready**: MidJourney prompts for professional visuals\n")
            f.write("✅ **Specialized LLMs**: Optimized models for each task\n\n")
            
            f.write("## 🎯 Usage:\n\n")
            f.write("- **For Blog**: Use `02_technical_blog_post.md`\n")
            f.write("- **For Social Media**: Use `03_social_media_content.md`\n")
            f.write("- **For Research**: Reference `01_research_findings.md`\n")
        
        print("✅ Saved: README.md")
        print(f"📊 Successfully created 5 files with multi-agent architecture")
        
        return output_dir

    def create_content(self, topic):
        """Main function to create content using multi-agent system"""
        print(f"\n🤖 Creating multi-agent content for: '{topic}'")
        print("🔬 Research Agent: Qwen 3-32B")
        print("✍️  Content Writer: DeepSeek R1 Distill Llama 70B")
        print("📱 Social Media: DeepSeek R1 Distill Llama 70B")
        print("="*70)
        
        try:
            # Create tasks for each agent
            research_task = self.create_research_task(topic)
            content_task = self.create_content_writing_task(topic)
            social_task = self.create_social_media_task(topic)
            
            # Create multi-agent crew with sequential process
            crew = Crew(
                agents=[self.researcher, self.content_writer, self.social_media_specialist],
                tasks=[research_task, content_task, social_task],
                process=Process.sequential,  # Research -> Content -> Social
                verbose=True,
                max_rpm=3  # Conservative rate limiting
            )
            
            print("⏱️  Starting multi-agent content creation...")
            print("🔄 Phase 1: Research Agent gathering information...")
            
            # Execute the multi-agent workflow
            results = crew.kickoff(inputs={"topic": topic})
            
            print("\n✅ Multi-agent content creation completed!")
            
            # Extract individual results (CrewAI returns results for each task)
            research_result = results.tasks_output[0] if hasattr(results, 'tasks_output') else "Research completed"
            content_result = results.tasks_output[1] if hasattr(results, 'tasks_output') else "Content completed"
            social_result = results.tasks_output[2] if hasattr(results, 'tasks_output') else "Social media completed"
            
            # Save all content
            output_dir = self.save_content_to_files(topic, research_result, content_result, social_result)
            
            return {
                "research": research_result,
                "content": content_result,
                "social": social_result,
                "output_directory": output_dir
            }
            
        except Exception as e:
            print(f"\n❌ Error in multi-agent system: {str(e)}")
            raise e

# ======================
# Usage
# ======================
if __name__ == "__main__":
    creator = MultiAgentContentCreator()
    
    # Example topic
    topic = "Advanced RAG Techniques: From Basic Retrieval to Agentic RAG Systems"
    # Other examples:
    # topic = "Understanding Transformer Architecture Through Implementation"
    # topic = "MLOps Best Practices: From Model Training to Production Deployment"
    # topic = "Vector Databases: The Foundation of Modern AI Applications"
    
    result = creator.create_content(topic)
    
    print("\n" + "="*80)
    print("🤖 MULTI-AGENT CONTENT CREATION COMPLETED!")
    print("="*80)
    print(f"\n📁 Content saved to: {result['output_directory']}")
    print("\n🤖 Agent Contributions:")
    print("🔬 **RESEARCH AGENT (Qwen 3-32B)**: Comprehensive research and data gathering")
    print("✍️  **CONTENT WRITER (DeepSeek R1)**: Technical blog post with practical insights")
    print("📱 **SOCIAL SPECIALIST (DeepSeek R1)**: Engaging social media content")
    print("\n📝 What was created:")
    print("📊 **RESEARCH**: Academic papers, industry data, technical examples")
    print("🎯 **BLOG POST**: 1000-1500 words with code examples and real-world applications")
    print("💼 **LINKEDIN**: Professional insights for technical audiences")
    print("🐦 **TWITTER**: Technical threads with code snippets")
    print("🎨 **MIDJOURNEY**: Professional AI-generated visual prompts")
    print("🌍 **BILINGUAL**: English and Turkish social media content")
    print("="*80)
    print(f"\n💡 Check '02_technical_blog_post.md' for the main article!")
    print(f"🔍 Check '01_research_findings.md' for detailed research!")
    print(f"📱 Check '03_social_media_content.md' for social content!")