import os
import sys
from typing import List, Dict, Optional, Any
import yaml
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.memory import BaseMemory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun, YouTubeSearchTool
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import HuggingFaceHub
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import WikipediaAPIWrapper
from tavily import TavilyClient
import time
from datetime import datetime, timedelta

def load_environment() -> None:
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        print("Error: .env file not found. Please create one with your GROQ_API_KEY.")
        sys.exit(1)
    
    load_dotenv()
    
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in .env file.")
        sys.exit(1)

def load_config() -> Dict:
    """Load configuration from config.yaml file"""
    config_path = Path('config.yaml')
    if not config_path.exists():
        print("Error: config.yaml file not found.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            
        # Validate required configuration fields
        required_fields = {
            'llm': ['provider', 'model', 'temperature', 'max_tokens'],
            'memory': ['type', 'max_token_limit'],
            'tools.web_search': ['enabled', 'provider']
        }
        
        for section, fields in required_fields.items():
            section_parts = section.split('.')
            current = config
            for part in section_parts:
                if part not in current:
                    print(f"Error: Missing '{section}' section in config.yaml")
                    sys.exit(1)
                current = current[part]
            
            for field in fields:
                if field not in current:
                    print(f"Error: Missing '{field}' in {section} configuration")
                    sys.exit(1)
        
        return config
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

class Chatbot:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the chatbot with configurations."""
        self.config = self._load_config(config_path)
        self.memory = {"chat_history": [], "user_name": None}
        self._setup_agent()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configurations from yaml file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _get_user_name(self) -> Optional[str]:
        """Get the user's name from memory."""
        try:
            return self.memory.get("user_name")
        except Exception as e:
            print(f"Error getting user name: {e}")
            return None

    def _format_response(self, template: str, **kwargs) -> str:
        """Format a response template with the given kwargs."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"Missing template parameter: {e}")
            return self.config["responses"]["error"]
        except Exception as e:
            print(f"Error formatting response: {e}")
            return self.config["responses"]["error"]

    def get_response(self, user_input: str) -> str:
        """Get a response from the chatbot for the given user input."""
        try:
            # Update chat history with user input
            self.memory["chat_history"].append({"role": "user", "content": user_input})

            # Check for name introduction
            lower_input = user_input.lower()
            if "my name is" in lower_input or "i am" in lower_input or "i'm" in lower_input:
                name = user_input.split("is" if "is" in lower_input else "am", 1)[1].strip()
                self.memory["user_name"] = name

            # Format chat history for context
            history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.memory["chat_history"]])

            # Get response from agent
            response = self.agent_executor.invoke(
                {
                    "input": user_input,
                    "history": history
                }
            )

            # Format response
            formatted_response = response["output"].strip()
            if not formatted_response.endswith(('.', '!', '?')):
                formatted_response += '.'

            # Update chat history with response
            self.memory["chat_history"].append({"role": "assistant", "content": formatted_response})

            # Maintain reasonable history size
            if len(self.memory["chat_history"]) > 20:  # Keep last 10 exchanges
                self.memory["chat_history"] = self.memory["chat_history"][-20:]

            return formatted_response

        except Exception as e:
            print(f"Error getting response: {e}")
            return "I encountered an error. Could you please try again?"

    def _format_position_response(self, response: str, query: str) -> str:
        """Format position-related responses."""
        try:
            # Find which position was asked about
            position = next((title for key, title in self.config["position_titles"].items() 
                           if key in query), None)
            
            if position and "is" in response:
                if position.lower() in response.lower():
                    return response
                
                # Try to format it properly
                parts = response.split()
                if len(parts) >= 2:
                    name = " ".join(parts[-2:])
                    location = " ".join(parts[:-2])
                    return self._format_response(
                        self.config["responses"]["position_template"],
                        position=position,
                        location=location,
                        name=name
                    )
            
            return response
        except Exception as e:
            print(f"Error formatting position response: {e}")
            return response

    def _format_final_response(self, response: str) -> str:
        """Apply final formatting to the response."""
        response = response[0].upper() + response[1:]
        if not response.endswith(('.', '!', '?')):
            response += '.'
        return response

    def _update_chat_history(self, user_input: str, response: str) -> None:
        """Update the chat history with the latest interaction."""
        self.memory["chat_history"].append({"role": "user", "content": user_input})
        self.memory["chat_history"].append({"role": "assistant", "content": response})
        
        # Maintain history size limit
        max_history = self.config.get("max_history", 10) * 2  # multiply by 2 for pairs of messages
        if len(self.memory["chat_history"]) > max_history:
            self.memory["chat_history"] = self.memory["chat_history"][-max_history:]

    def _format_chat_history(self) -> str:
        """Format chat history for the agent."""
        return "\n".join([f"{msg['role']}: {msg['content']}" 
                         for msg in self.memory["chat_history"]])

    def _setup_agent(self) -> None:
        """Setup the agent with tools and configurations."""
        try:
            # Initialize LLM
            self.llm = ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name=self.config['llm']['model'],
                temperature=0.7,
                max_tokens=150
            )

            # Initialize tools
            tools = []

            # Web Search Tool
            try:
                tavily_api_key = os.getenv("TAVILY_API_KEY")
                if tavily_api_key:
                    self.tavily_client = TavilyClient(api_key=tavily_api_key)
                    search_tool = lambda query: self.tavily_client.search(query, search_depth="advanced", max_results=3)
                else:
                    search_tool = DuckDuckGoSearchRun()
                
                tools.append(
                    Tool(
                        name="Web Search",
                        func=search_tool,
                        description="Use this for finding current and accurate information about any topic, person, event, or fact that needs verification."
                    )
                )
            except Exception as e:
                print(f"Warning: Could not initialize web search: {e}")

            # Wikipedia Tool
            try:
                wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
                tools.append(
                    Tool(
                        name="Wikipedia",
                        func=wikipedia.run,
                        description="Use this for finding detailed information about topics, history, people, places, and general knowledge."
                    )
                )
            except Exception as e:
                print(f"Warning: Could not initialize Wikipedia: {e}")

            # YouTube Search Tool
            try:
                youtube_search = YouTubeSearchTool()
                tools.append(
                    Tool(
                        name="YouTube Search",
                        func=youtube_search.run,
                        description="Use this for finding relevant videos and video content."
                    )
                )
            except Exception as e:
                print(f"Warning: Could not initialize YouTube search: {e}")

            # Initialize prompt template for the React agent
            prompt = PromptTemplate.from_template(
                """You are a helpful AI assistant that provides accurate and natural responses.
                You have access to various tools to find information:
                {tools}

                IMPORTANT GUIDELINES:

                1. For ANY response, you MUST use at least one tool
                2. For greetings and basic interactions:
                   - Use Web Search to find friendly greeting examples
                   - Keep the response natural and friendly
                3. For name-related interactions:
                   - Use Web Search to find cultural significance or meaning of names
                   - Remember names from conversation history
                4. For questions about people, places, or facts:
                   - Use Web Search for current information
                   - Use Wikipedia for background information
                   - Cross-reference multiple sources when possible
                5. For any uncertainty:
                   - Use tools to verify information
                   - Be transparent about what you find

                Use the following format:

                Question: the input question you must answer
                Thought: think about which tool is most appropriate
                Action: choose a tool from {tool_names}
                Action Input: be specific and concise with your input
                Observation: the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat if needed)
                Thought: I now know the final answer
                Final Answer: give a clear, concise answer (1-2 sentences maximum)

                Previous conversation history:
                {history}

                Current question: {input}
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
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True,
                return_intermediate_steps=False,
                max_execution_time=60
            )

        except Exception as e:
            print(f"Error setting up agent: {e}")
            raise

def main():
    try:
        print("Initializing chatbot...")
        chatbot = Chatbot()
        
        print("\nWelcome! How can I help you today?")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            
            response = chatbot.get_response(user_input)
            print(f"\nAssistant: {response}")
    
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main() 