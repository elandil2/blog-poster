# 🌐 Streamlit Web App - AI Content Creator

A user-friendly web interface for the AI-Powered Multi-Agent Content Creator that allows users to input their own API keys and create content through a browser.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit App
```bash
streamlit run streamlit_app.py
```

### 3. Open in Browser
The app will automatically open at `http://localhost:8501`

## 🔑 Required API Keys

Users need to provide their own API keys through the web interface:

### Groq API Key
- **Purpose**: Powers all 3 AI agents (Research, Content Writer, Social Media)
- **Models Used**: Qwen/Qwen3-32B, DeepSeek R1 Distill Llama 70B
- **Get Key**: [https://console.groq.com/keys](https://console.groq.com/keys)
- **Free Tier**: Available with generous limits

### Serper.dev API Key
- **Purpose**: Web search and Google Scholar access
- **Get Key**: [https://serper.dev/api-key](https://serper.dev/api-key)
- **Free Tier**: 2,500 free searches per month

## 🎯 Features

### 🔒 **Secure API Key Input**
- API keys entered through secure password fields
- Keys are not stored or logged
- Session-based usage only

### 🤖 **Multi-Agent System**
- **Research Agent**: Qwen/Qwen3-32B for efficient research
- **Content Writer**: DeepSeek R1 for technical blog posts
- **Social Specialist**: DeepSeek R1 for engaging social content

### 📱 **User-Friendly Interface**
- Clean, intuitive web interface
- Real-time progress tracking
- Example topics provided
- Responsive design

### 📊 **Comprehensive Output**
- Research findings with academic sources
- Technical blog posts (1000-1500 words)
- Social media content (LinkedIn & Twitter)
- MidJourney prompts for visuals
- Bilingual support (English & Turkish)

### 📥 **Easy Downloads**
- Individual file downloads (Markdown format)
- Complete ZIP package with all content
- Organized file structure
- README included in downloads

## 🎨 **Interface Overview**

### Sidebar
- **API Configuration**: Secure input for API keys
- **Agent Architecture**: Overview of the 3-agent system
- **API Key Links**: Direct links to get API keys

### Main Area
- **Topic Input**: Large text area for content topics
- **Example Topics**: Dropdown with sample topics
- **Create Button**: Starts the content generation process
- **Progress Tracking**: Real-time status updates
- **Results Tabs**: Organized display of all generated content

### Results Display
- **📊 Research Tab**: Academic findings and industry data
- **📝 Blog Post Tab**: Complete technical article
- **📱 Social Media Tab**: LinkedIn posts, Twitter threads, MidJourney prompts
- **📦 Download Tab**: All download options

## 🔧 **Technical Details**

### Architecture
- Built with Streamlit for rapid web app development
- Same multi-agent system as `researcherkilo.py`
- Session-based API key management
- Real-time progress updates
- ZIP file generation for downloads

### Security
- API keys handled securely (password input type)
- No server-side storage of sensitive data
- Session-based operation
- HTTPS recommended for production

### Performance
- Efficient multi-agent processing
- Progress callbacks for user feedback
- Optimized file generation
- Responsive UI updates

## 🚀 **Deployment Options**

### Local Development
```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud (Free)
1. Push to GitHub repository
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy directly from repository
4. Share public URL with users

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY streamlit_app.py .
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Heroku/Railway/Render
- Compatible with most cloud platforms
- Include `streamlit_app.py` as main application file
- Set port configuration for platform requirements

## 🎯 **Usage Examples**

### Sample Topics That Work Well:
- "Advanced RAG Techniques: From Basic Retrieval to Agentic RAG Systems"
- "Understanding Transformer Architecture Through Implementation"
- "MLOps Best Practices: From Model Training to Production Deployment"
- "Vector Databases: The Foundation of Modern AI Applications"
- "What is Model Context Protocol (MCP)?"

### Expected Processing Time:
- **Research Phase**: 2-3 minutes
- **Content Creation**: 1-2 minutes
- **Social Media Generation**: 1 minute
- **Total**: 4-6 minutes per topic

## 🔍 **Troubleshooting**

### Common Issues:

1. **API Key Errors**
   - Verify API keys are correct
   - Check API key permissions
   - Ensure sufficient credits/quota

2. **Slow Performance**
   - Normal for comprehensive content generation
   - Progress bar shows current status
   - Allow 4-6 minutes for completion

3. **Content Quality Issues**
   - Provide more specific, detailed topics
   - Use technical terminology for better results
   - Try different topic formulations

4. **Download Issues**
   - Ensure content generation completed successfully
   - Try individual file downloads if ZIP fails
   - Check browser download settings

## 🌟 **Benefits Over CLI Version**

- **Accessibility**: No technical setup required
- **User-Friendly**: Intuitive web interface
- **Secure**: API keys handled safely
- **Organized**: Tabbed results display
- **Portable**: Works on any device with a browser
- **Shareable**: Easy to deploy and share with others

## 👨‍💻 **Author**

**Safi Cengiz**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/safi-cengiz/)

---

**🌐 Ready to create amazing content through your browser? Run `streamlit run streamlit_app.py`!**