document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const fileUpload = document.getElementById('file-upload');
    const uploadButton = document.getElementById('upload-button');
    const uploadStatus = document.getElementById('upload-status');

    function createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            indicator.appendChild(dot);
        }
        return indicator;
    }

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'} animate__animated animate__fadeInUp`;
        
        // Add icon to messages
        const icon = document.createElement('i');
        icon.className = isUser ? 'fas fa-user' : 'fas fa-robot';
        icon.style.marginRight = '8px';
        
        const textSpan = document.createElement('span');
        // Clean the message text and ensure proper spacing
        const cleanedMessage = message
            .replace(/\*/g, '') // Remove asterisks
            .replace(/\s+/g, ' ') // Remove extra spaces
            .trim(); // Remove leading/trailing spaces
        textSpan.textContent = cleanedMessage;
        
        messageDiv.appendChild(icon);
        messageDiv.appendChild(textSpan);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        uploadStatus.textContent = 'Uploading...';
        uploadButton.disabled = true;

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                uploadStatus.textContent = 'Document uploaded successfully!';
                uploadStatus.style.color = '#4CAF50';
                addMessage('Document uploaded successfully. You can now ask questions about it!', false);
            } else {
                uploadStatus.textContent = data.error || 'Upload failed';
                uploadStatus.style.color = '#f44336';
            }
        } catch (error) {
            uploadStatus.textContent = 'Upload failed';
            uploadStatus.style.color = '#f44336';
            console.error('Error:', error);
        } finally {
            uploadButton.disabled = false;
            setTimeout(() => {
                uploadStatus.textContent = '';
            }, 5000);
        }
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, true);
        userInput.value = '';

        // Add typing indicator
        const typingIndicator = createTypingIndicator();
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            // Send message to server
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remove typing indicator
            typingIndicator.remove();

            if (response.ok) {
                // Add bot response to chat
                addMessage(data.response);
            } else {
                // Handle error
                addMessage('Error occurred. Please try again.');
                console.error('Error:', data.error);
            }
        } catch (error) {
            // Remove typing indicator
            typingIndicator.remove();
            addMessage('Error occurred. Please try again.');
            console.error('Error:', error);
        }
    }

    // Handle file upload
    uploadButton.addEventListener('click', () => {
        fileUpload.click();
    });

    fileUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    // Animate send button on hover
    sendButton.addEventListener('mouseenter', () => {
        sendButton.querySelector('i').classList.add('animate__animated', 'animate__rubberBand');
    });

    sendButton.addEventListener('mouseleave', () => {
        sendButton.querySelector('i').classList.remove('animate__animated', 'animate__rubberBand');
    });

    // Send message on button click
    sendButton.addEventListener('click', sendMessage);

    // Send message on Enter key press
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Add initial greeting message with typing animation
    setTimeout(() => {
        addMessage('👋 Hi! I\'m Linda Laga Sangamaya. How can I help you today?');
    }, 1000);
}); 