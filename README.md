# Smart Chatbot with LangChain

This is an intelligent chatbot implementation using LangChain that features:
- Long-term conversation memory
- Web search capabilities for current information
- Integration with OpenAI's GPT models

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

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