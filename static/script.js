document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Hide welcome message after first interaction
    let hasInteracted = false;

    function hideWelcomeMessage() {
        if (!hasInteracted) {
            const welcomeMessage = document.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
                welcomeMessage.style.opacity = '0';
                welcomeMessage.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    welcomeMessage.style.display = 'none';
                }, 500);
            }
            hasInteracted = true;
        }
    }

    function createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="typing-text">AI is analyzing...</span>
            </div>
        `;
        return indicator;
    }

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'} animate__animated animate__fadeInUp`;
        
        // Add icon to messages
        const iconContainer = document.createElement('div');
        iconContainer.className = 'message-icon';
        const icon = document.createElement('i');
        icon.className = isUser ? 'fas fa-user' : 'fas fa-brain';
        iconContainer.appendChild(icon);
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format the message with better handling for AI/ML content
        const formattedMessage = formatAIMLMessage(message);
        messageContent.innerHTML = formattedMessage;
        
        messageDiv.appendChild(iconContainer);
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatAIMLMessage(message) {
        // Clean and format AI/ML messages
        let formatted = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic text
            .replace(/\n\n/g, '<br><br>') // Double line breaks
            .replace(/\n/g, '<br>') // Single line breaks
            .replace(/(\d+\.)\s/g, '<br>$1 ') // Numbered lists
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener" class="message-link">🔗 View Source</a>'); // Links
        
        return formatted;
    }

    // Function to fill input with suggestion
    window.fillInput = function(text) {
        userInput.value = text;
        userInput.focus();
    };

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        hideWelcomeMessage();

        // Add user message
        addMessage(message, true);
        userInput.value = '';
        sendButton.disabled = true;

        // Add typing indicator
        const typingIndicator = createTypingIndicator();
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Remove typing indicator
            if (typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add bot response
            addMessage(data.response, false);

        } catch (error) {
            console.error('Error:', error);
            if (typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            addMessage('I apologize, but I encountered an error processing your AI/ML query. Please check your connection and try again.', false);
        } finally {
            sendButton.disabled = false;
            userInput.focus();
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Add initial focus to input
    userInput.focus();

    // Add some example interactions when page loads
    setTimeout(() => {
        const examples = [
            "💡 Try: 'What are the latest AI news today?'",
            "🔬 Try: 'Tell me about recent ML research'",
            "🛠️ Try: 'What are trending AI tools?'"
        ];
        
        const randomExample = examples[Math.floor(Math.random() * examples.length)];
        userInput.placeholder = randomExample;
    }, 3000);
});

// Add CSS for new elements
const style = document.createElement('style');
style.textContent = `
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 15px 20px;
        margin: 10px 0;
        background: #f8fafc;
        border-radius: 18px;
        border-top-left-radius: 4px;
        max-width: 200px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .typing-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .typing-dots {
        display: flex;
        gap: 4px;
    }

    .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #3b82f6;
        animation: typing 1.5s ease-in-out infinite;
    }

    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }

    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes typing {
        0%, 60%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        30% {
            transform: scale(1.2);
            opacity: 1;
        }
    }

    .typing-text {
        font-size: 12px;
        color: #64748b;
        font-style: italic;
    }

    .message {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin: 15px 20px;
        animation-duration: 0.5s;
    }

    .message-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        flex-shrink: 0;
    }

    .user-message .message-icon {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
    }

    .bot-message .message-icon {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed);
        color: white;
    }

    .message-content {
        flex: 1;
        padding: 12px 16px;
        border-radius: 18px;
        line-height: 1.5;
        font-size: 14px;
    }

    .user-message .message-content {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border-bottom-right-radius: 4px;
        margin-left: auto;
        max-width: 70%;
    }

    .bot-message .message-content {
        background: white;
        color: #1e293b;
        border-top-left-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        max-width: 85%;
    }

    .message-link {
        color: #3b82f6;
        text-decoration: none;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-left: 8px;
        padding: 2px 8px;
        background: #eff6ff;
        border-radius: 12px;
        font-size: 12px;
    }

    .message-link:hover {
        background: #dbeafe;
        text-decoration: underline;
    }
`;
document.head.appendChild(style);
