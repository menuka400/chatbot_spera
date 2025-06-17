import os
import sys
import re
from typing import List, Dict, Optional, Any
import yaml
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from tavily import TavilyClient
import feedparser
from gnews import GNews

class AIMLNewsRetriever:
    """Retrieves AI/ML related news from various sources"""
    
    def __init__(self, config: Dict):
        self.config = config['news']
        self.gnews = GNews(language='en', country='US', period='1d', max_results=10)
        
    def get_ai_ml_news(self, query: str = None, limit: int = 5) -> List[Dict]:
        """Get latest AI/ML news"""
        try:
            if query:
                # Search for specific AI/ML topics
                news_items = self.gnews.get_news(f"{query} AI OR ML OR artificial intelligence OR machine learning")
            else:
                # Get general AI/ML news
                ai_news = self.gnews.get_news('artificial intelligence')
                ml_news = self.gnews.get_news('machine learning')
                news_items = ai_news + ml_news
            
            # Format news items
            formatted_news = []
            for item in news_items[:limit]:
                formatted_news.append({
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('url', ''),
                    'published': item.get('published date', ''),
                    'source': item.get('publisher', {}).get('title', 'Unknown')
                })
            
            return formatted_news
        except Exception as e:
            print(f"Error retrieving news: {e}")
            return []
    
    def search_arxiv(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search arXiv for AI/ML research papers"""
        try:
            # Format query for arXiv API
            arxiv_query = f"cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV AND ({query})"
            url = f"http://export.arxiv.org/api/query?search_query={arxiv_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
            
            response = requests.get(url)
            if response.status_code == 200:
                # Parse the XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                papers = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                    summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                    link = entry.find('{http://www.w3.org/2005/Atom}id').text
                    published = entry.find('{http://www.w3.org/2005/Atom}published').text
                    
                    papers.append({
                        'title': title,
                        'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                        'url': link,
                        'published': published,
                        'source': 'arXiv'
                    })
                
                return papers
        except Exception as e:
            print(f"Error searching arXiv: {e}")
            return []

class AIMLChatbot:
    """AI/ML specialized chatbot with LangChain native decision-making"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.memory = {"chat_history": [], "user_name": None}
        self.news_retriever = AIMLNewsRetriever(self.config)
        self._setup_agent()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configurations from yaml file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _create_ai_ml_news_tool(self):
        """Create AI/ML news search tool"""
        def search_ai_ml_news(query: str) -> str:
            try:
                news_items = self.news_retriever.get_ai_ml_news(query, limit=3)
                if not news_items:
                    return "No recent AI/ML news found for your query."
                
                result = "Latest AI/ML News:\n\n"
                for i, item in enumerate(news_items, 1):
                    result += f"{i}. **{item['title']}**\n"
                    result += f"   Source: {item['source']}\n"
                    if item['description']:
                        result += f"   Summary: {item['description'][:150]}...\n"
                    result += f"   URL: {item['url']}\n\n"
                
                return result
            except Exception as e:
                return f"Error retrieving AI/ML news: {str(e)}"
        
        return search_ai_ml_news
    
    def _create_arxiv_search_tool(self):
        """Create arXiv research paper search tool"""
        def search_arxiv_papers(query: str) -> str:
            try:
                papers = self.news_retriever.search_arxiv(query, max_results=3)
                if not papers:
                    return "No recent AI/ML research papers found for your query."
                
                result = "Recent AI/ML Research Papers:\n\n"
                for i, paper in enumerate(papers, 1):
                    result += f"{i}. **{paper['title']}**\n"
                    result += f"   Summary: {paper['summary']}\n"
                    result += f"   Published: {paper['published'][:10]}\n"
                    result += f"   URL: {paper['url']}\n\n"
                
                return result
            except Exception as e:
                return f"Error searching research papers: {str(e)}"
        
        return search_arxiv_papers
    
    def _setup_agent(self):
        """Setup the AI/ML specialized agent with LangChain native decision-making"""
        try:
            # Initialize LLM
            self.llm = ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name=self.config['llm']['model'],
                temperature=self.config['llm']['temperature'],
                max_tokens=self.config['llm']['max_tokens']
            )
            
            # Initialize tools
            tools = []
            
            # AI/ML News Tool
            ai_ml_news_tool = Tool(
                name="AI_ML_News_Search",
                func=self._create_ai_ml_news_tool(),
                description="Search for the latest AI and ML news, trends, and developments. Use this when users ask for current events, recent news, or latest developments in AI/ML."
            )
            tools.append(ai_ml_news_tool)
            
            # arXiv Research Tool
            arxiv_tool = Tool(
                name="ArXiv_Research_Search",
                func=self._create_arxiv_search_tool(),
                description="Search for recent AI/ML research papers on arXiv. Use this when users ask about recent research, new papers, or academic developments in AI/ML."
            )
            tools.append(arxiv_tool)
            
            # Enhanced Web Search for AI/ML
            try:
                tavily_api_key = os.getenv("TAVILY_API_KEY")
                if tavily_api_key:
                    self.tavily_client = TavilyClient(api_key=tavily_api_key)
                    def ai_ml_web_search(query: str) -> str:
                        enhanced_query = f"{query} AI ML artificial intelligence machine learning"
                        results = self.tavily_client.search(enhanced_query, search_depth="advanced", max_results=3)
                        return str(results)
                    
                    web_search_tool = Tool(
                        name="AI_ML_Web_Search",
                        func=ai_ml_web_search,
                        description="Search the web for AI/ML related information, tutorials, tools, and resources. Use when you need current information not available in your knowledge base."
                    )
                else:
                    def ai_ml_ddg_search(query: str) -> str:
                        ddg = DuckDuckGoSearchRun()
                        enhanced_query = f"{query} AI ML artificial intelligence machine learning"
                        return ddg.run(enhanced_query)
                    
                    web_search_tool = Tool(
                        name="AI_ML_Web_Search",
                        func=ai_ml_ddg_search,
                        description="Search the web for AI/ML related information, tutorials, tools, and resources. Use when you need current information not available in your knowledge base."
                    )
                
                tools.append(web_search_tool)
            except Exception as e:
                print(f"Warning: Could not initialize web search: {e}")
            
            # Wikipedia for AI/ML topics
            try:
                wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
                
                def ai_ml_wikipedia_search(query: str) -> str:
                    # Enhance query with AI/ML context
                    enhanced_query = f"{query} artificial intelligence machine learning"
                    return wikipedia.run(enhanced_query)
                
                wikipedia_tool = Tool(
                    name="AI_ML_Wikipedia",
                    func=ai_ml_wikipedia_search,
                    description="Search Wikipedia for detailed information about AI/ML concepts, history, people, and companies. Use for comprehensive background information."
                )
                tools.append(wikipedia_tool)
            except Exception as e:
                print(f"Warning: Could not initialize Wikipedia: {e}")
            
            # Create intelligent AI/ML prompt that leverages LangChain's decision-making
            prompt = PromptTemplate.from_template(
                """You are an AI/ML specialized chatbot assistant with extensive knowledge about artificial intelligence, machine learning, and data science.

CORE PRINCIPLES:
1. You specialize ONLY in AI/ML topics. For non-AI/ML questions, politely redirect: "I'm specialized in AI and ML topics only. Please ask questions related to artificial intelligence, machine learning, data science, deep learning, neural networks, or AI/ML research and trends."

2. INTELLIGENT TOOL USAGE - Use your existing knowledge first, then tools only when needed:
   
   ANSWER DIRECTLY (no tools) when you have sufficient knowledge about:
   ✓ Greetings and general conversation
   ✓ AI/ML definitions and basic concepts (what is AI, ML, neural networks, etc.)
   ✓ Algorithm explanations (backpropagation, gradient descent, CNNs, RNNs, etc.)
   ✓ General AI/ML techniques and methodologies
   ✓ Historical AI/ML information and well-established facts
   ✓ Programming concepts related to AI/ML (Python libraries, frameworks)
   ✓ Mathematical foundations (linear algebra, statistics for ML)
   
   USE TOOLS when you need current or specific information about:
   ✓ Latest news: "recent AI developments", "current AI trends", "AI news today"
   ✓ Research papers: "new research on...", "recent papers about...", "latest studies"
   ✓ Company updates: "OpenAI latest", "Google AI news", "Microsoft AI updates"
   ✓ Current events in the AI/ML field
   ✓ Specific information you don't have in your knowledge base
   ✓ Real-time developments and breaking news

3. DECISION PROCESS:
   - First evaluate if the question is AI/ML related
   - Then assess if you can answer confidently with your existing knowledge
   - Only use tools if you genuinely need current/additional information
   - If answering directly, skip straight to Final Answer immediately

Available tools: {tools}
Tool names: {tool_names}

FORMAT:
Question: the input question you received
Thought: I need to think about whether this is AI/ML related and if I can answer with my knowledge or need tools
Action: [tool name] (ONLY if you need current/additional information)
Action Input: [search query] (ONLY if using Action)
Observation: [tool result] (ONLY if using Action)
Thought: I now have the information needed to provide a comprehensive answer
Final Answer: [your response to the user]

Previous conversation context:
{history}

Question: {input}
{agent_scratchpad}"""
            )
            
            # Initialize the agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
            
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=tools,
                verbose=True,  # Enable to see agent decision-making process
                max_iterations=self.config.get('agent', {}).get('max_iterations', 5),
                handle_parsing_errors=True,
                return_intermediate_steps=False,
                max_execution_time=self.config.get('agent', {}).get('max_execution_time', 30)
            )
            
        except Exception as e:
            print(f"Error setting up agent: {e}")
            raise
    
    def get_response(self, user_input: str) -> str:
        """Get response from the AI/ML chatbot using LangChain's intelligent decision-making"""
        try:
            # Update chat history
            self.memory["chat_history"].append({"role": "user", "content": user_input})
            
            # Check for name introduction
            lower_input = user_input.lower()
            if "my name is" in lower_input or "i am" in lower_input or "i'm" in lower_input:
                name = user_input.split("is" if "is" in lower_input else "am", 1)[1].strip()
                self.memory["user_name"] = name
            
            # Format chat history for context
            history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.memory["chat_history"][-10:]])
            
            # Let LangChain agent decide whether to use tools or answer directly
            response = self.agent_executor.invoke({
                "input": user_input,
                "history": history
            })
            
            final_response = response["output"].strip()
            
            # Update chat history with response
            self.memory["chat_history"].append({"role": "assistant", "content": final_response})
            
            # Maintain history size
            if len(self.memory["chat_history"]) > 20:
                self.memory["chat_history"] = self.memory["chat_history"][-20:]
            
            return final_response
            
        except Exception as e:
            print(f"Error getting response: {e}")
            return "I encountered an error processing your query. Could you please try again?"

def main():
    """Main function to run the AI/ML chatbot"""
    try:
        # Load environment variables
        load_dotenv()
        
        if not os.getenv("GROQ_API_KEY"):
            print("Error: GROQ_API_KEY not found in environment variables.")
            sys.exit(1)
        
        print("Initializing AI/ML Chatbot...")
        chatbot = AIMLChatbot()
        
        print("\n🤖 Welcome to the AI/ML Intelligent Chatbot!")
        print("I specialize in artificial intelligence, machine learning, and related technologies.")
        print("I use my knowledge when possible and search for current information when needed!")
        print("Ask me about AI/ML topics, news, research, tools, trends, or concepts!")
        print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye! Stay updated with AI/ML developments! 🚀")
                break
            
            if not user_input:
                continue
            
            response = chatbot.get_response(user_input)
            print(f"\nAI/ML Bot: {response}\n")
    
    except KeyboardInterrupt:
        print("\n\nGoodbye! Stay updated with AI/ML developments! 🚀")
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()
