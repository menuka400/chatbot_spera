import streamlit as st
from chatbot import SmartChatBot
import os

# Set page configuration
st.set_page_config(
    page_title="SmartChatBot",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        align-self: flex-end;
    }
    .bot-message {
        background-color: #f5f5f5;
        align-self: flex-start;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = SmartChatBot()
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def display_chat_messages():
    """Display chat messages from history."""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message">👤 You: {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message bot-message">🤖 AI: {message["content"]}</div>', unsafe_allow_html=True)

def main():
    st.title("🤖 SmartChatBot")
    st.subheader("Your AI Assistant")
    
    # Initialize session state
    initialize_session_state()
    
    # Chat interface
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        display_chat_messages()
    
    # User input
    user_input = st.text_input("Type your message here...")
    
    # Handle user input
    if st.button("Send") or (user_input and len(user_input.strip()) > 0):
        if user_input.strip():
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get bot response
            try:
                response = st.session_state.chatbot.get_response(user_input)
                # Add bot response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            
            # Rerun to update chat display
            st.rerun()

    # Add a clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main() 