# Multi-Agent Architecture: ResearcherKilo.py

## System Overview

The new `researcherkilo.py` implements a **3-Agent Specialized System** with different LLMs optimized for specific tasks:

- **Research Agent**: Qwen 3-32B (Fast, efficient research)
- **Content Writer**: DeepSeek R1 Distill Llama 70B (Creative, comprehensive writing)
- **Social Media Specialist**: DeepSeek R1 Distill Llama 70B (Engaging social content)

## Multi-Agent Architecture Diagram

```mermaid
graph TD
    A[User Input: Topic] --> B[MultiAgentContentCreator]
    
    subgraph "Agent 1: Research Phase"
        C[Research Agent<br/>Qwen 3-32B<br/>Temp: 0.3]
        C --> D[Google Scholar Tool]
        C --> E[Serper Dev Tool]
        C --> F[Scrape Website Tool]
        D --> G[Academic Papers]
        E --> H[Industry Data]
        F --> I[Technical Details]
    end
    
    subgraph "Agent 2: Content Creation"
        J[Content Writer Agent<br/>DeepSeek R1 70B<br/>Temp: 0.6]
        G --> J
        H --> J
        I --> J
        J --> K[Technical Blog Post<br/>1000-1500 words]
    end
    
    subgraph "Agent 3: Social Media"
        L[Social Media Specialist<br/>DeepSeek R1 70B<br/>Temp: 0.7]
        K --> L
        L --> M[LinkedIn Posts<br/>English & Turkish]
        L --> N[Twitter Threads<br/>English & Turkish]
        L --> O[MidJourney Prompts]
    end
    
    subgraph "Output System"
        P[File Organization]
        K --> P
        M --> P
        N --> P
        O --> P
        P --> Q[01_research_findings.md]
        P --> R[02_technical_blog_post.md]
        P --> S[03_social_media_content.md]
        P --> T[complete_multi_agent_content.md]
        P --> U[README.md]
    end
    
    B --> C
```

## Sequential Workflow Process

```mermaid
sequenceDiagram
    participant User
    participant System as MultiAgentContentCreator
    participant R as Research Agent (Qwen 3-32B)
    participant W as Content Writer (DeepSeek R1)
    participant S as Social Specialist (DeepSeek R1)
    participant FS as File System

    User->>System: Input topic
    System->>R: Start research task
    
    Note over R: Phase 1: Research
    R->>R: Google Scholar search
    R->>R: Web search (Serper)
    R->>R: Content scraping
    R->>System: Research findings
    
    Note over W: Phase 2: Content Creation
    System->>W: Research findings + content task
    W->>W: Analyze research data
    W->>W: Create technical blog post
    W->>System: Blog post content
    
    Note over S: Phase 3: Social Media
    System->>S: Blog content + social task
    S->>S: Create LinkedIn posts
    S->>S: Create Twitter threads
    S->>S: Generate MidJourney prompts
    S->>System: Social media package
    
    System->>FS: Save all content
    FS->>User: Complete content package
```

## Agent Specialization Matrix

| Agent | LLM Model | Temperature | Max Tokens | Primary Function | Tools |
|-------|-----------|-------------|------------|------------------|-------|
| **Research Agent** | Qwen 3-32B | 0.3 (Focused) | 3000 | Data gathering, fact-finding | Scholar, Serper, Scraper |
| **Content Writer** | DeepSeek R1 70B | 0.6 (Balanced) | 4000 | Technical writing, blog creation | None (uses research) |
| **Social Specialist** | DeepSeek R1 70B | 0.7 (Creative) | 2000 | Social content, engagement | None (uses blog content) |

## Tool Distribution Architecture

```mermaid
mindmap
  root((Multi-Agent System))
    Research Agent
      Google Scholar Tool
        Academic Papers
        Citations
        Recent Research
      Serper Dev Tool
        Web Search
        Industry Trends
        Current Data
      Scrape Website Tool
        Detailed Content
        Technical Examples
        Code Repositories
    
    Content Writer Agent
      Research Processing
        Data Analysis
        Information Synthesis
        Technical Writing
      Blog Creation
        1000-1500 words
        Code Examples
        Practical Insights
        Real-world Applications
    
    Social Media Specialist
      Content Adaptation
        LinkedIn Professional
        Twitter Engagement
        Cultural Translation
      Visual Content
        MidJourney Prompts
        Technical Aesthetics
        Professional Design
```

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph Input
        A[Topic/Prompt]
    end
    
    subgraph "Research Phase (Qwen 3-32B)"
        B[Academic Research]
        C[Industry Research]
        D[Technical Research]
        E[Content Scraping]
    end
    
    subgraph "Content Phase (DeepSeek R1)"
        F[Research Analysis]
        G[Technical Writing]
        H[Blog Post Creation]
        I[Code Examples]
    end
    
    subgraph "Social Phase (DeepSeek R1)"
        J[Content Adaptation]
        K[LinkedIn Posts]
        L[Twitter Threads]
        M[Visual Prompts]
    end
    
    subgraph Output
        N[Research Findings]
        O[Technical Blog]
        P[Social Media]
        Q[Complete Package]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    G --> H
    H --> I
    
    H --> J
    J --> K
    J --> L
    J --> M
    
    B --> N
    H --> O
    K --> P
    L --> P
    M --> P
    N --> Q
    O --> Q
    P --> Q
```

## Key Improvements Over Single-Agent System

### 1. **Specialized LLM Selection**
- **Qwen 3-32B**: Optimized for research tasks (faster, more efficient)
- **DeepSeek R1**: Optimized for creative writing and social content

### 2. **Task-Specific Optimization**
- **Research**: Lower temperature (0.3) for focused, factual gathering
- **Content**: Medium temperature (0.6) for balanced creativity
- **Social**: Higher temperature (0.7) for engaging content

### 3. **Sequential Processing**
- Research findings feed into content creation
- Blog content feeds into social media adaptation
- Each agent builds upon previous work

### 4. **Enhanced Output Structure**
- Separate files for each agent's output
- Complete package combining all results
- Detailed README with architecture information

## File Output Structure

```
multi_agent_content/
├── 01_research_findings.md      # Research Agent output
├── 02_technical_blog_post.md    # Content Writer output  
├── 03_social_media_content.md   # Social Specialist output
├── complete_multi_agent_content.md  # Combined output
└── README.md                    # Architecture & usage info
```

## Performance Benefits

1. **Efficiency**: Qwen 3-32B handles research faster than DeepSeek R1
2. **Quality**: DeepSeek R1 provides superior creative writing
3. **Specialization**: Each agent optimized for specific tasks
4. **Scalability**: Easy to add more specialized agents
5. **Cost Optimization**: Use appropriate model for each task

This multi-agent architecture provides better specialization, improved efficiency, and higher quality output compared to the single-agent approach.