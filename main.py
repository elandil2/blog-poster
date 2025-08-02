from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from dotenv import load_dotenv
import os
import requests
import time
import json
import base64
from datetime import datetime

load_dotenv()

# Simple, reliable LLM configuration
llm = LLM(
    model="groq/deepseek-r1-distill-llama-70b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.6,
    max_tokens=2500  # Reduced token limit for stability
)

class ImageGenerator:
    """Custom tool for generating images using Stability AI API"""
    
    def __init__(self):
        self.stability_api_key = os.getenv("STABILITY_API_KEY")
        self.api_url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    
    def generate_image(self, prompt: str, output_dir: str = "generated_images") -> str:
        """Generate image using Stability AI Stable Diffusion 3.5"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"🎨 Generating image with Stability AI: {prompt[:50]}...")
            
            # Prepare headers
            headers = {
                "authorization": f"Bearer {self.stability_api_key}",
                "accept": "image/*"
            }
            
            # Prepare data
            data = {
                "prompt": prompt,
                "model": "sd3.5-large",  # or "sd3.5-medium" for cheaper option
                "aspect_ratio": "1:1",   # Square format
                "output_format": "png"
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                files={"none": ""},
                data=data
            )
            
            if response.status_code == 200:
                # Generate filename
                filename = f"{output_dir}/stability_image_{hash(prompt) % 10000}.png"
                
                # Save the image
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                return f"✅ Stability AI image saved: {filename}"
            else:
                return f"❌ Stability AI error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"❌ Error generating Stability AI image: {str(e)}"

class SimpleSocialCreator:
    """Single-agent social media content creator - more reliable!"""
    
    def __init__(self):
        self.image_generator = ImageGenerator()
        
        # Single agent that does everything - BLOG FOCUSED
        self.content_creator = Agent(
            role="Senior Content Writer & Researcher",
            goal="Create comprehensive blog posts (800-1200 words) for Medium.com about '{topic}', backed by thorough research, plus social media adaptations in English and Turkish.",
            backstory="You are a senior content writer specializing in creating in-depth, well-researched blog posts for Medium.com. You excel at turning complex topics into engaging, accessible articles that provide real value to readers. You conduct thorough research using web search and create comprehensive content that serves as the foundation for all other marketing materials. You also adapt content for social media in both English and Turkish.",
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
            llm=llm,
            verbose=True,
            max_iter=2,  # Keep it simple
            max_rpm=3    # Conservative rate limiting
        )

    def create_complete_content(self, topic):
        """Single task that creates all content - BLOG FIRST approach"""
        
        task = Task(
            description=f"""
            Create a complete content package for the topic: '{topic}'
            
            🎯 PRIMARY DELIVERABLE - BLOG POST (MOST IMPORTANT):
            
            1. MAIN BLOG POST (800-1200 words for Medium.com):
            - Write a comprehensive, engaging blog post about {topic}
            - Target: 5-minute read for Medium.com
            - Structure: Title, Introduction, 3-4 main sections with subheadings, conclusion
            - Include current research, statistics, and real-world examples
            - Use web search to find latest trends and data about {topic}
            - Professional but accessible tone
            - Include actionable insights and takeaways
            - Format with proper markdown headers (# ## ###)
            
            2. RESEARCH FOUNDATION:
            - Use web search extensively to find current facts about {topic}
            - Include specific statistics, market data, company examples
            - Reference credible sources and recent developments
            
            3. SOCIAL MEDIA ADAPTATIONS (Secondary):
            
            LINKEDIN POSTS:
            - English: Professional 250-300 words, extract key insights from blog
            - Turkish: Culturally adapted translation for Turkish business audience
            - Include relevant hashtags and call-to-action
            
            X/TWITTER POSTS:
            - English: Create 3-5 tweet thread summarizing blog key points
            - Turkish: Adapt the thread for Turkish audience
            - Keep tweets under 280 characters each
            
            4. IMAGE CONCEPTS:
            - Suggest 2 specific image ideas for the blog post
            - Describe each in detail for AI image generation
            
            CRITICAL: Start with the blog post. Make it comprehensive, well-researched, and Medium-ready. 
            The blog post should be the main focus - at least 70% of your effort.
            
            Format your response clearly:
            # BLOG POST
            [Full 800-1200 word blog post here]
            
            # LINKEDIN POSTS
            ## English
            [LinkedIn content]
            ## Turkish  
            [LinkedIn content]
            
            # X/TWITTER POSTS
            ## English
            [Twitter thread]
            ## Turkish
            [Twitter thread]
            
            # IMAGE CONCEPTS
            [Image descriptions]
            """,
            expected_output="Complete package with PRIORITY on comprehensive 800-1200 word blog post for Medium, plus social media adaptations",
            agent=self.content_creator
        )
        
        return task

    def save_content_to_files(self, topic, content, images):
        """Save all content to organized files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        output_dir = f"outputs/{safe_topic}_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n💾 Saving content to: {output_dir}")
        
        # Save complete content with better blog extraction
        with open(f"{output_dir}/01_BLOG_POST_MEDIUM.md", "w", encoding="utf-8") as f:
            f.write(f"# {topic}\n\n")
            f.write(f"*Ready for Medium.com - Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Try to extract blog section from content
            content_str = str(content)
            if "# BLOG POST" in content_str:
                blog_start = content_str.find("# BLOG POST") + len("# BLOG POST")
                blog_end = content_str.find("# LINKEDIN POSTS")
                if blog_end == -1:
                    blog_end = content_str.find("# X/TWITTER POSTS") 
                if blog_end == -1:
                    blog_end = len(content_str)
                blog_content = content_str[blog_start:blog_end].strip()
                f.write(blog_content)
            else:
                f.write("⚠️ Blog content extraction failed. Check complete_content.md for full output.\n\n")
                f.write(str(content))
        
        # Save complete content
        with open(f"{output_dir}/complete_content.md", "w", encoding="utf-8") as f:
            f.write(f"# Complete Content Package: {topic}\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(str(content))
        
        # Save image info
        with open(f"{output_dir}/images_generated.txt", "w", encoding="utf-8") as f:
            f.write(f"GENERATED IMAGES - {topic}\n")
            f.write("="*50 + "\n\n")
            for i, img_result in enumerate(images, 1):
                f.write(f"Image {i}:\n{img_result}\n\n")
        
        # Create README
        with open(f"{output_dir}/README.md", "w", encoding="utf-8") as f:
            f.write(f"# Content Package: {topic}\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 📁 Files:\n\n")
            f.write("- `01_BLOG_POST_MEDIUM.md` - **MAIN BLOG POST** (800-1200 words for Medium.com)\n")
            f.write("- `complete_content.md` - All content in one file\n")
            f.write("- `images_generated.txt` - Image generation results\n")
            f.write("- `generated_images/` - Actual image files\n\n")
            f.write("## 🎯 Priority Content:\n\n")
            f.write("🔥 **MAIN DELIVERABLE**: `01_BLOG_POST_MEDIUM.md`\n\n")
            f.write("📱 **Social Media**: Check `complete_content.md` for LinkedIn & Twitter posts\n\n")
            f.write("## 📊 What's included:\n\n")
            f.write("✅ Comprehensive blog post (800-1200 words) - READY FOR MEDIUM\n")
            f.write("✅ LinkedIn posts (English + Turkish)\n")
            f.write("✅ X/Twitter posts (English + Turkish)\n")
            f.write("✅ AI-generated images\n")
            f.write("✅ Research-backed content with current data\n")
        
        return output_dir

    def generate_images(self, topic):
        """Generate images for the content using Stability AI"""
        
        print("\n🎨 Generating images with Stability AI...")
        
        # Optimized prompts for Stability AI
        prompts = [
            f"Professional business infographic about {topic}, modern clean design, blue and white color scheme, corporate style, high quality",
            f"Social media post graphic about {topic}, engaging visual design, vibrant colors, professional illustration, marketing style"
        ]
        
        results = []
        for i, prompt in enumerate(prompts, 1):
            print(f"\n🖼️  Generating Stability AI image {i}/{len(prompts)}...")
            result = self.image_generator.generate_image(prompt)
            results.append(result)
            
            # Delay between generations (Stability AI rate limits)
            if i < len(prompts):
                print("⏱️  Waiting 3 seconds...")
                time.sleep(3)
        
        return results

    def create_content(self, topic):
        """Main function to create all content"""
        
        print(f"\n🚀 Creating content for: '{topic}'")
        print("🔄 Using simplified single-agent approach...")
        print("="*60)
        
        try:
            # Create the task
            task = self.create_complete_content(topic)
            
            # Create simple crew with one agent and one task
            crew = Crew(
                agents=[self.content_creator],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
                max_rpm=2  # Very conservative
            )
            
            # Execute content creation
            print("⏱️  Starting content creation...")
            time.sleep(2)  # Initial delay
            
            result = crew.kickoff(inputs={"topic": topic})
            
            print("\n✅ Content creation completed!")
            
            # Generate images
            print("\n⏱️  Waiting 5 seconds before image generation...")
            time.sleep(5)
            
            images = self.generate_images(topic)
            
            # Save everything
            output_dir = self.save_content_to_files(topic, result, images)
            
            return {
                "content": result,
                "images": images,
                "output_directory": output_dir
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("💡 Try again in a few minutes or check your API keys")
            raise e

# Usage
if __name__ == "__main__":
    # Create simple content creator
    creator = SimpleSocialCreator()
    
    # Your topic
    topic = "Agentic AI Workflows: Turning a Single Prompt into Multi-Channel Content"
    
    # Create content
    result = creator.create_content(topic)
    
    print("\n" + "="*70)
    print("🎉 BLOG-FOCUSED CONTENT CREATION COMPLETED!")
    print("="*70)
    print(f"\n📁 All content saved to: {result['output_directory']}")
    print("\n📝 Priority Content:")
    print("🔥 **MAIN**: 01_BLOG_POST_MEDIUM.md (800-1200 words for Medium)")
    print("\n📱 Additional Content:")
    print("✅ LinkedIn posts (English + Turkish)")
    print("✅ X/Twitter posts (English + Turkish)")
    print("✅ Generated images (if Replicate credits available)")
    print("✅ Research-backed, current data")
    print("="*70)
    print("\n💡 For Medium: Copy content from '01_BLOG_POST_MEDIUM.md'")