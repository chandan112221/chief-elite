// Chat-related functionality
let lastMessageId = 0;
let pollInterval;

// Initialize chat
function initChat() {
    // Get DOM elements
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendMessageBtn');
    const chatContainer = document.getElementById('chatContainer');
    
    if (!messageInput || !sendButton || !chatContainer) {
        console.error('Chat elements not found');
        return;
    }
    
    // Send message handler
    sendButton.addEventListener('click', function() {
        sendChatMessage();
    });
    
    // Enter key handler for message input
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    
    // Start polling for new messages
    pollInterval = setInterval(pollNewMessages, 5000);
    
    // Initial poll
    pollNewMessages();
}

// Set last message ID
function setLastMessageId(id) {
    lastMessageId = id;
}

// Send chat message
function sendChatMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Disable input and button while sending
    messageInput.disabled = true;
    document.getElementById('sendMessageBtn').disabled = true;
    
    // Send message to server
    fetch('/chat/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear input
            messageInput.value = '';
            
            // Add message to chat
            addChatMessage(data.message.content, false, data.message.timestamp);
            
            // Update last message ID
            lastMessageId = data.message.id;
            
            // Scroll to bottom
            scrollToBottom();
        } else {
            alert('Failed to send message: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('An error occurred while sending your message. Please try again.');
    })
    .finally(() => {
        // Re-enable input and button
        messageInput.disabled = false;
        document.getElementById('sendMessageBtn').disabled = false;
        messageInput.focus();
    });
}

// Poll for new messages
function pollNewMessages() {
    fetch(`/chat/messages?last_id=${lastMessageId}`)
        .then(response => response.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                // Add each new message to the chat
                data.messages.forEach(message => {
                    addChatMessage(message.content, message.is_admin, message.timestamp);
                    lastMessageId = Math.max(lastMessageId, message.id);
                });
                
                // Scroll to bottom if new messages
                scrollToBottom();
            }
        })
        .catch(error => {
            console.error('Error polling messages:', error);
        });
}

// Add a message to the chat
function addChatMessage(content, isAdmin, timestamp) {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${isAdmin ? 'admin-message' : 'user-message'}`;
    
    // Format timestamp (HH:MM)
    let formattedTime = 'now';
    if (timestamp) {
        const date = new Date(timestamp);
        formattedTime = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
    
    messageElement.innerHTML = `
        ${content}
        <div class="chat-timestamp">${formattedTime}</div>
    `;
    
    chatContainer.appendChild(messageElement);
}

// Clean up when leaving the page
window.addEventListener('beforeunload', function() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
