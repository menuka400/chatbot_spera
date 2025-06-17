# 🤖 AI/ML News Chatbot

A specialized chatbot focused exclusively on **Artificial Intelligence**, **Machine Learning**, and related technologies. Get the latest news, research papers, trends, and insights from the AI/ML world.

## ✨ Features

### 🎯 AI/ML Specialization
- **Strict Topic Filtering**: Only responds to AI/ML related queries
- **Intelligent Query Validation**: Automatically detects and filters non-AI/ML topics
- **Specialized Knowledge Base**: Focused on AI, ML, data science, and related fields

### 📰 Real-time News & Research
- **Latest AI/ML News**: Get current news from top tech sources
- **arXiv Research Papers**: Access recent AI/ML research publications
- **Industry Trends**: Stay updated with AI/ML developments
- **Company Updates**: News about AI startups and major tech companies

### 🛠️ Advanced Tools Integration
- **Web Search**: AI/ML focused search results
- **Wikipedia Integration**: Detailed information about AI/ML concepts
- **News Aggregation**: Multiple news sources for comprehensive coverage
- **Research Paper Search**: Direct access to academic publications

### 🌐 Modern Web Interface
- **Responsive Design**: Works on desktop and mobile
- **Real-time Chat**: Instant responses with typing indicators
- **Message Formatting**: Rich text formatting for better readability
- **Suggestion System**: Quick-start questions for users

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- GROQ API Key (required)
- Tavily API Key (optional, for enhanced search)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd chatbot_spera
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

4. **Run the application**
   ```bash
   # For web interface
   python app.py
   
   # For command line interface
   python ai_ml_chatbot.py
   ```

5. **Access the chatbot**
   - Web interface: http://localhost:5000
   - Command line: Direct interaction in terminal

Run the chatbot using:
```bash
python chatbot.py
```

The chatbot will:
- Remember your conversation history
- Automatically search the web when it needs current information
- Provide detailed responses using both its knowledge and web search results

To exit the chat, simply type 'quit'.

## Features

1. **Conversation Memory**: The chatbot maintains context throughout the conversation using LangChain's ConversationBufferMemory.

2. **Web Search Integration**: When the chatbot encounters questions requiring current information, it automatically searches the web using DuckDuckGo.

3. **Token Usage Tracking**: The chatbot displays token usage information for each interaction.

## Note

Make sure to keep your API key secure and never commit it to version control. The `.env` file should be included in your `.gitignore`. 