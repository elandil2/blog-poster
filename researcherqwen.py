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
# Fixed Google Scholar Tool using Serper.dev API
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
# LLM Configuration
# ======================
llm = LLM(
    model="groq/deepseek-r1-distill-llama-70b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,
    max_tokens=4000
)

# ======================
# Main Content Creator Class
# ======================
class DataScienceContentCreator:
    """Content creator for data scientists - technical, personal, practical"""
    
    def __init__(self):
        # Initialize Google Scholar tool
        self.scholar_tool = GoogleScholarTool()
        
        # Data Science focused agent with both Google and Scholar search
        self.content_creator = Agent(
            role="Senior Data Scientist & Technical Writer",
            goal="Create in-depth, technical blog posts about '{topic}' from a data scientist's perspective, using both academic research and practical implementations.",
            backstory="""You are a seasoned data scientist with 10+ years of experience in machine learning, 
            statistical analysis, and data engineering. You write technical blog posts that combine theoretical 
            knowledge with practical implementation. Your writing style is:
            
            - Technical but accessible to fellow data scientists
            - Combines academic research with practical implementation
            - Includes code examples and mathematical concepts
            - Shares real-world challenges and solutions
            - Focuses on practical implementation over marketing hype
            - Uses personal anecdotes from data science projects
            - References both academic papers and industry best practices
            - Explains complex concepts with data-driven examples
            - Discusses tools, frameworks, and methodologies
            
            You have access to both regular web search and Google Scholar search. Use Scholar 
            to find academic research, papers, and theoretical foundations. Use regular web search 
            to find practical implementations, tutorials, and industry applications.
            
            You avoid marketing buzzwords and focus on substance, sharing genuine insights 
            that would help other data scientists in their work.""",
            tools=[SerperDevTool(), ScrapeWebsiteTool()],  # Removed scholar_tool temporarily
            llm=llm,
            verbose=True,
            max_iter=3,  # Allow more iterations to use tools
            max_rpm=5,   # Higher rate limit
            allow_delegation=False,
            step_callback=None
        )

    def create_technical_content(self, topic):
        task = Task(
            description=f"""
            Create a technical content package about: '{topic}' from a data scientist's perspective.
            
            🎯 PRIMARY DELIVERABLE - TECHNICAL BLOG POST:
            
            1. MAIN BLOG POST (1000-1500 words for Medium/personal blog):
            - Write from a data scientist's personal experience and perspective
            - Include technical details, methodologies, and practical insights
            - Add code snippets or pseudocode where relevant
            - Discuss real-world applications and challenges you've encountered
            - Include mathematical concepts or statistical methods if applicable
            - Reference specific tools, libraries, or frameworks (Python, R, TensorFlow, etc.)
            - Share lessons learned and practical tips
            - Use first-person perspective ("In my experience...", "I've found that...")
            - Avoid marketing language - focus on technical substance
            - Structure: Introduction, Technical Deep Dive (2-3 sections), Implementation Details, Lessons Learned, Conclusion
            
            2. RESEARCH FOUNDATION:
            - Use Google Scholar search to find recent academic papers and research (last 3 years)
            - Use regular web search for practical implementations, tutorials, and industry examples
            - Include both theoretical foundations and real-world applications
            - Reference academic sources AND practical blog posts/repositories
            - Find code repositories or technical examples on GitHub/Medium
            - Balance academic rigor with practical utility
            
            3. SOCIAL MEDIA ADAPTATIONS (Technical Community Focus):
            
            LINKEDIN POSTS:
            - English: Technical insights for data science professionals (200-250 words)
            - Turkish: Adapted for Turkish tech community
            - Include relevant technical hashtags (#MachineLearning #DataScience #Python #Statistics)
            - Share key technical takeaways
            
            X/TWITTER POSTS:
            - English: Create 3-4 tweet thread with technical insights and code snippets
            - Turkish: Adapt for Turkish data science community
            - Include code examples or mathematical formulas where possible
            - Use technical hashtags
            
            4. MIDJOURNEY PROMPTS:
            - Create 3 detailed MidJourney prompts for technical visuals
            - Include technical elements (code, diagrams, data flows, AI concepts)
            - Specify aspect ratios (--ar 16:9 for blog headers, --ar 1:1 for social media)
            - Use professional tech aesthetics (dark themes, neon accents, clean minimal)
            - Include version and style parameters (--v 6 --style modern tech)
            
            CRITICAL REQUIREMENTS:
            - Use SerperDevTool for both academic-style searches and practical examples
            - Search multiple times with different queries to gather comprehensive information
            - Start with Scholar search to establish theoretical foundation
            - Follow with regular search for implementations and tutorials
            - Write as a practicing data scientist, not a marketer
            - Include technical depth and practical implementation details
            - Use personal experience and real-world examples
            - Avoid generic business/marketing language
            - Focus on helping other data scientists learn and implement
            
            Format your response:
            # BLOG POST
            [Technical blog post with personal insights and code examples]
            
            # LINKEDIN POSTS
            ## English
            [Technical LinkedIn post for data science professionals]
            ## Turkish  
            [Turkish version for tech community]
            
            # X/TWITTER POSTS
            ## English
            [Technical Twitter thread with code/examples]
            ## Turkish
            [Turkish technical thread]
            
            # MIDJOURNEY PROMPTS
            [3 detailed MidJourney prompts for technical blog visuals with --ar and --v parameters]
            """,
            expected_output="Technical content package written from data scientist's perspective with practical insights and implementation details",
            agent=self.content_creator
        )
        return task

    def save_content_to_files(self, topic, content):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        output_dir = f"technical_content/{safe_topic}_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n💾 Saving technical content to: {output_dir}")
        
        # Get content as string
        content_str = str(content)
        
        # Debug: Show what we're working with
        print(f"🔍 DEBUG: Content length: {len(content_str)} characters")
        print(f"🔍 DEBUG: Looking for '# BLOG POST' in content...")
        print(f"🔍 DEBUG: Contains '# BLOG POST': {'# BLOG POST' in content_str}")
        print(f"🔍 DEBUG: Contains '# LINKEDIN POSTS': {'# LINKEDIN POSTS' in content_str}")
        print(f"🔍 DEBUG: Contains '# MIDJOURNEY PROMPTS': {'# MIDJOURNEY PROMPTS' in content_str}")
        print(f"🔍 DEBUG: First 300 characters:\n{content_str[:300]}")
        
        # Save complete content
        with open(f"{output_dir}/complete_technical_content.md", "w", encoding="utf-8") as f:
            f.write(f"# Technical Content Package: {topic}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Perspective:** Data Scientist Technical Blog\n")
            f.write(f"**Model:** DeepSeek R1 Distill Llama 70B\n\n")
            f.write("---\n\n")
            f.write(content_str)
        print("✅ Saved: complete_technical_content.md")
        
        # Extract blog post with improved logic
        blog_extracted = False
        if "# BLOG POST" in content_str:
            blog_start = content_str.find("# BLOG POST") + len("# BLOG POST")
            
            # Try multiple end markers in order of preference
            end_markers = ["# LINKEDIN POSTS", "# X/TWITTER POSTS", "# MIDJOURNEY PROMPTS"]
            blog_end = len(content_str)  # Default to end of content
            
            for marker in end_markers:
                marker_pos = content_str.find(marker)
                if marker_pos > blog_start:  # Make sure it's after the blog start
                    blog_end = marker_pos
                    break
            
            blog_content = content_str[blog_start:blog_end].strip()
            
            # Only save if we have substantial content
            if len(blog_content) > 100:
                with open(f"{output_dir}/technical_blog_post.md", "w", encoding="utf-8") as f:
                    f.write(f"# {topic}\n\n")
                    f.write(f"*Technical blog post from a data scientist's perspective*\n")
                    f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    f.write(blog_content)
                print("✅ Saved: technical_blog_post.md")
                blog_extracted = True
            else:
                print(f"⚠️  Blog content too short ({len(blog_content)} chars), not saving separate file")
        
        if not blog_extracted:
            print("❌ Could not extract blog post - check complete_technical_content.md for raw output")
        
        # Extract social media content
        social_extracted = False
        if "# LINKEDIN POSTS" in content_str:
            social_start = content_str.find("# LINKEDIN POSTS")
            
            # Find end of social section
            end_markers = ["# X/TWITTER POSTS", "# MIDJOURNEY PROMPTS"]
            social_end = len(content_str)
            
            for marker in end_markers:
                marker_pos = content_str.find(marker, social_start + 1)
                if marker_pos > social_start:
                    social_end = marker_pos
                    break
            
            # If we found X/TWITTER section, include it in social media
            if "# X/TWITTER POSTS" in content_str:
                twitter_start = content_str.find("# X/TWITTER POSTS")
                if twitter_start < social_end or social_end == len(content_str):
                    # Include Twitter section
                    midjourney_start = content_str.find("# MIDJOURNEY PROMPTS")
                    if midjourney_start > twitter_start:
                        social_end = midjourney_start
                    else:
                        social_end = len(content_str)
            
            social_content = content_str[social_start:social_end].strip()
            
            if len(social_content) > 50:
                with open(f"{output_dir}/social_media_posts.md", "w", encoding="utf-8") as f:
                    f.write(f"# Social Media Content: {topic}\n\n")
                    f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    f.write(social_content)
                print("✅ Saved: social_media_posts.md")
                social_extracted = True
        
        if not social_extracted:
            print("⚠️  Could not extract social media content")
        
        # Extract MidJourney prompts
        midjourney_extracted = False
        if "# MIDJOURNEY PROMPTS" in content_str:
            midjourney_start = content_str.find("# MIDJOURNEY PROMPTS")
            midjourney_content = content_str[midjourney_start:].strip()
            
            if len(midjourney_content) > 30:
                with open(f"{output_dir}/midjourney_prompts.md", "w", encoding="utf-8") as f:
                    f.write(f"# MidJourney Prompts: {topic}\n\n")
                    f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    f.write(midjourney_content)
                print("✅ Saved: midjourney_prompts.md")
                midjourney_extracted = True
        
        if not midjourney_extracted:
            print("⚠️  Could not extract MidJourney prompts content")
        
        # Create README for technical content
        files_created = 1  # complete_technical_content.md always created
        if blog_extracted:
            files_created += 1
        if social_extracted:
            files_created += 1
        if midjourney_extracted:
            files_created += 1
        
        with open(f"{output_dir}/README.md", "w", encoding="utf-8") as f:
            f.write(f"# Technical Content: {topic}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Style:** Data Scientist Technical Perspective\n")
            f.write(f"**Success Rate:** {files_created}/5 files created\n\n")
            f.write("## 📁 Files:\n\n")
            
            # List files that were actually created
            if blog_extracted:
                f.write("- ✅ `technical_blog_post.md` - **MAIN TECHNICAL BLOG** (1000-1500 words)\n")
            else:
                f.write("- ❌ `technical_blog_post.md` - Main technical blog (not extracted)\n")
                
            if social_extracted:
                f.write("- ✅ `social_media_posts.md` - LinkedIn & Twitter content\n")
            else:
                f.write("- ❌ `social_media_posts.md` - Social media content (not extracted)\n")
                
            if midjourney_extracted:
                f.write("- ✅ `midjourney_prompts.md` - MidJourney visual prompts\n")
            else:
                f.write("- ❌ `midjourney_prompts.md` - MidJourney prompts (not extracted)\n")
                
            f.write("- ✅ `complete_technical_content.md` - All content including social media\n")
            f.write("- ✅ `README.md` - This file\n\n")
            
            f.write("## 🔬 Content Features:\n\n")
            f.write("✅ Technical depth with practical implementation\n")
            f.write("✅ Code examples and technical details\n")
            f.write("✅ Personal insights from data science experience\n")
            f.write("✅ Real-world applications and challenges\n")
            f.write("✅ Technical social media content\n")
            f.write("✅ MidJourney prompts for professional blog visuals\n")
            
            if files_created < 4:
                f.write(f"\n## ⚠️ Extraction Issues:\n\n")
                f.write("Some content sections couldn't be extracted. Check `complete_technical_content.md` for the full output.\n")
                f.write("The content might be there but not properly formatted with the expected headers.\n")
        
        print("✅ Saved: README.md")
        print(f"📊 Successfully created {files_created}/5 files")
        
        return output_dir

    def create_content(self, topic):
        print(f"\n🔬 Creating technical content for: '{topic}'")
        print("🎯 Data scientist perspective with technical depth...")
        print("="*60)
        
        try:
            task = self.create_technical_content(topic)
            
            crew = Crew(
                agents=[self.content_creator],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
                max_rpm=2
            )
            
            print("⏱️  Starting technical content creation...")
            result = crew.kickoff(inputs={"topic": topic})
            print("\n✅ Technical content creation completed!")
            
            output_dir = self.save_content_to_files(topic, result)
            
            return {
                "content": result,
                "output_directory": output_dir
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            raise e

# ======================
# Usage
# ======================
if __name__ == "__main__":
    creator = DataScienceContentCreator()
    
    # Example technical topics for data scientists
    topic = "What is Model Context Protocol(MCP)?"
    # Other examples:
    # topic = "Why Feature Engineering Still Matters in the Age of AutoML"
    # topic = "Building Robust ML Pipelines: Lessons from Production Failures"
    # topic = "Understanding Transformer Attention Mechanisms Through Code"
    
    result = creator.create_content(topic)
    
    print("\n" + "="*70)
    print("🔬 TECHNICAL CONTENT CREATION COMPLETED!")
    print("="*70)
    print(f"\n📁 Content saved to: {result['output_directory']}")
    print("\n📝 What was created:")
    print("🎯 **TECHNICAL BLOG**: 1000-1500 words with code examples")
    print("💼 **LINKEDIN**: Technical insights for data science professionals")
    print("🐦 **TWITTER**: Technical threads with code snippets")
    print("🎨 **MIDJOURNEY**: Professional AI-generated visual prompts")
    print("🔬 **PERSPECTIVE**: Real data scientist experience, not marketing")
    print("="*70)
    print(f"\n💡 Check 'technical_blog_post.md' for the main technical article!")