// Admin-specific JavaScript functions

// Initialize admin dashboard
function initAdminDashboard() {
    // This function will be called on admin dashboard page load
    console.log('Admin dashboard initialized');
    
    // Set up any dashboard-specific functionality here
}

// Handle bulk import of stock items
function setupBulkImport() {
    const serviceSelect = document.getElementById('service_id');
    const isOldCheckbox = document.getElementById('is_old');
    const rateInput = document.getElementById('rate');
    const itemsTextarea = document.getElementById('items_text');
    const previewButton = document.getElementById('previewImport');
    const previewContainer = document.getElementById('importPreview');
    
    if (!serviceSelect || !itemsTextarea || !previewButton || !previewContainer) {
        return; // Elements not found, likely not on the import page
    }
    
    previewButton.addEventListener('click', function() {
        const serviceName = serviceSelect.options[serviceSelect.selectedIndex].text;
        const isOld = isOldCheckbox.checked;
        const rate = rateInput.value;
        const itemsText = itemsTextarea.value.trim();
        
        if (!serviceName || !rate || !itemsText) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Parse the items text to preview
        const lines = itemsText.split('\n');
        let previewHTML = `
            <h5>Import Preview - ${serviceName} (${isOld ? 'Old' : 'New'})</h5>
            <p><strong>Rate:</strong> ${rate} BDT per item</p>
            <p><strong>Total Items:</strong> ${lines.length}</p>
            <div class="table-responsive">
                <table class="table table-sm table-bordered">
                    <thead>
                        <tr>
        `;
        
        // Determine headers based on service
        let headers = [];
        if (serviceName.toLowerCase().includes('facebook') || serviceName.toLowerCase().includes('linkedin')) {
            headers = ['Name', 'Email', 'Password', 'Profile Link', '2FA'];
        } else if (serviceName.toLowerCase().includes('gmail') || serviceName.toLowerCase().includes('outlook')) {
            headers = ['Email', 'Password', 'Recovery Email'];
        } else {
            headers = ['Email', 'Password'];
        }
        
        // Add headers to preview
        headers.forEach(header => {
            previewHTML += `<th>${header}</th>`;
        });
        
        previewHTML += `
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add sample rows (max 5)
        const maxLines = Math.min(lines.length, 5);
        for (let i = 0; i < maxLines; i++) {
            if (!lines[i].trim()) continue;
            
            const parts = lines[i].split(',').map(part => part.trim());
            previewHTML += '<tr>';
            
            // Add appropriate cells based on service
            if (serviceName.toLowerCase().includes('facebook') || serviceName.toLowerCase().includes('linkedin')) {
                previewHTML += `<td>${parts[0] || 'N/A'}</td>`; // Name
                previewHTML += `<td>${parts[1] || 'N/A'}</td>`; // Email
                previewHTML += `<td>${parts[2] || 'N/A'}</td>`; // Password
                previewHTML += `<td>${parts[3] || 'N/A'}</td>`; // Profile Link
                previewHTML += `<td>${parts[4] || 'N/A'}</td>`; // 2FA
            } else if (serviceName.toLowerCase().includes('gmail') || serviceName.toLowerCase().includes('outlook')) {
                previewHTML += `<td>${parts[0] || 'N/A'}</td>`; // Email
                previewHTML += `<td>${parts[1] || 'N/A'}</td>`; // Password
                previewHTML += `<td>${parts[2] || 'N/A'}</td>`; // Recovery Email
            } else {
                previewHTML += `<td>${parts[0] || 'N/A'}</td>`; // Email
                previewHTML += `<td>${parts[1] || 'N/A'}</td>`; // Password
            }
            
            previewHTML += '</tr>';
        }
        
        // Finish the table
        previewHTML += `
                    </tbody>
                </table>
            </div>
        `;
        
        // Show the preview
        previewContainer.innerHTML = previewHTML;
        previewContainer.style.display = 'block';
    });
}

// Handle other order type fields management
function setupOrderTypeFields() {
    const fieldsTextarea = document.getElementById('required_fields');
    const fieldsPreview = document.getElementById('fieldsPreview');
    
    if (!fieldsTextarea || !fieldsPreview) {
        return; // Elements not found, likely not on the order type edit page
    }
    
    // Update preview when textarea changes
    fieldsTextarea.addEventListener('input', updateFieldsPreview);
    
    // Initial update
    updateFieldsPreview();
    
    function updateFieldsPreview() {
        try {
            const fieldsJson = fieldsTextarea.value.trim();
            if (!fieldsJson) {
                fieldsPreview.innerHTML = '<div class="alert alert-info">No fields defined</div>';
                return;
            }
            
            const fields = JSON.parse(fieldsJson);
            if (!Array.isArray(fields) || fields.length === 0) {
                fieldsPreview.innerHTML = '<div class="alert alert-warning">Invalid fields format or empty array</div>';
                return;
            }
            
            let previewHTML = '<h5>Fields Preview</h5>';
            
            fields.forEach((field, index) => {
                previewHTML += `
                    <div class="mb-3">
                        <label class="form-label">${field.label || `Field ${index + 1}`}</label>
                        <input type="${field.type || 'text'}" class="form-control" placeholder="${field.placeholder || ''}" ${field.required ? 'required' : ''}>
                        ${field.description ? `<small class="form-text text-muted">${field.description}</small>` : ''}
                    </div>
                `;
            });
            
            fieldsPreview.innerHTML = previewHTML;
            
        } catch (e) {
            fieldsPreview.innerHTML = `
                <div class="alert alert-danger">
                    <strong>JSON Error:</strong> ${e.message}
                </div>
                <div class="alert alert-info">
                    <strong>Example format:</strong><br>
                    <pre>[
  {
    "label": "Account Username",
    "type": "text",
    "placeholder": "Enter username",
    "required": true
  },
  {
    "label": "Account Password",
    "type": "password",
    "description": "Minimum 8 characters",
    "required": true
  }
]</pre>
                </div>
            `;
        }
    }
}

// Initialize support chat for admin
function initAdminChat() {
    const userId = document.querySelector('[data-user-id]')?.getAttribute('data-user-id');
    if (!userId) return;
    
    const messageInput = document.getElementById('adminMessageInput');
    const sendButton = document.getElementById('sendAdminMessageBtn');
    const chatContainer = document.getElementById('adminChatContainer');
    
    if (!messageInput || !sendButton || !chatContainer) return;
    
    // Last message ID for polling
    let lastMessageId = parseInt(document.querySelector('[data-last-message-id]')?.getAttribute('data-last-message-id') || '0');
    
    // Poll for new messages
    function pollMessages() {
        fetch(`/admin/support/${userId}/messages?last_id=${lastMessageId}`)
            .then(response => response.json())
            .then(data => {
                if (data.messages && data.messages.length > 0) {
                    // Update chat with new messages
                    data.messages.forEach(message => {
                        appendMessage(message);
                        lastMessageId = Math.max(lastMessageId, message.id);
                    });
                    
                    // Scroll to bottom
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            })
            .catch(error => console.error('Error polling messages:', error));
    }
    
    // Send message function
    function sendMessage() {
        const content = messageInput.value.trim();
        if (!content) return;
        
        fetch(`/admin/support/${userId}/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: content }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear input
                messageInput.value = '';
                
                // Add message to chat
                appendMessage(data.message);
                
                // Update last message ID
                lastMessageId = Math.max(lastMessageId, data.message.id);
                
                // Scroll to bottom
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        })
        .catch(error => console.error('Error sending message:', error));
    }
    
    // Append message to chat
    function appendMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.is_admin ? 'admin-message' : 'user-message'}`;
        messageElement.innerHTML = `
            ${message.content}
            <div class="chat-timestamp">${formatTimestamp(message.timestamp)}</div>
        `;
        chatContainer.appendChild(messageElement);
    }
    
    // Send button click handler
    sendButton.addEventListener('click', sendMessage);
    
    // Enter key handler
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Start polling for new messages
    setInterval(pollMessages, 5000);
    
    // Initial poll
    pollMessages();
}

// Document ready event
document.addEventListener('DOMContentLoaded', function() {
    // Initialize functions based on page
    if (window.location.pathname.includes('/admin/dashboard')) {
        initAdminDashboard();
    } else if (window.location.pathname.includes('/admin/stock/import')) {
        setupBulkImport();
    } else if (window.location.pathname.includes('/admin/other-order-type')) {
        setupOrderTypeFields();
    } else if (window.location.pathname.includes('/admin/support/')) {
        initAdminChat();
    }
});
