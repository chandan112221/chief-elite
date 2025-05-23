// Global theme handling
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggler
    const themeSwitch = document.getElementById('themeSwitch');
    if (themeSwitch) {
        themeSwitch.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.setAttribute('data-bs-theme', 'dark');
                document.cookie = "theme=dark; path=/; SameSite=Lax";
                
                // Notify server about theme change if user is logged in
                if (typeof fetch !== 'undefined') {
                    fetch('/toggle-theme', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ theme: 'dark' }),
                    });
                }
            } else {
                document.documentElement.setAttribute('data-bs-theme', 'light');
                document.cookie = "theme=light; path=/; SameSite=Lax";
                
                // Notify server about theme change if user is logged in
                if (typeof fetch !== 'undefined') {
                    fetch('/toggle-theme', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ theme: 'light' }),
                    });
                }
            }
        });
    }
    
    // Sidebar toggler
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
            const mainContent = document.querySelector('.main-content');
            if (document.querySelector('.sidebar').classList.contains('show')) {
                mainContent.style.marginLeft = '200px';
            } else {
                mainContent.style.marginLeft = '0';
            }
        });
    }
    
    // Chat icon toggle
    const chatToggle = document.getElementById('chatToggle');
    if (chatToggle) {
        chatToggle.addEventListener('click', function() {
            window.location.href = '/chat';
        });
    }
    
    // Enable all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Handle mobile view
    function handleMobileView() {
        if (window.innerWidth < 768) {
            document.querySelector('.sidebar').classList.remove('show');
            document.querySelector('.main-content').style.marginLeft = '0';
        }
    }
    
    // Call on page load
    handleMobileView();
    
    // Call on window resize
    window.addEventListener('resize', handleMobileView);
});

// Function to scroll to bottom of a container
function scrollToBottom(elementId = 'chatContainer') {
    const container = document.getElementById(elementId);
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Format timestamp function
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    
    // Format: YYYY-MM-DD HH:MM:SS
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// Format currency function
function formatCurrency(amount) {
    return parseFloat(amount).toFixed(2) + ' BDT';
}

// Display error function
function displayError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>${message}
            </div>
        `;
    }
}

// Display success function
function displaySuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>${message}
            </div>
        `;
        
        // Auto dismiss after 3 seconds
        setTimeout(() => {
            element.innerHTML = '';
        }, 3000);
    }
}

// Copy to clipboard function
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                // Success message could be shown here
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
            });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
}
