
// Auto-discover backend URL based on frontend port
function getBackendUrl() {
    const currentPort = window.location.port;
    if (currentPort) {
        // Frontend is typically on port+1, so backend is port-1
        const backendPort = parseInt(currentPort) - 1;
        return `http://localhost:${backendPort}`;
    }
    // Fallback to provided port
    return 'http://localhost:8002';
}

const BACKEND_URL = getBackendUrl();

class AgentChat {
    constructor() {
        this.messages = document.getElementById('messages');
        this.form = document.getElementById('chatForm');
        this.input = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.status = document.getElementById('status');
        
        this.initializeEventListeners();
        this.loadFiles();
        this.checkBackendStatus();
    }
    
    initializeEventListeners() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    async checkBackendStatus() {
        try {
            console.log('Checking backend health at:', BACKEND_URL + '/health');
            const response = await fetch(BACKEND_URL + '/health');
            if (response.ok) {
                const data = await response.json();
                this.updateStatus('🟢 Connected', 'connected');
                console.log('Backend health check passed:', data);
            } else {
                this.updateStatus('🔴 Backend Error', 'error');
                console.error('Backend health check failed:', response.status);
            }
        } catch (error) {
            console.error('Backend connection error:', error);
            this.updateStatus('🔴 Disconnected', 'error');
            // Try alternative ports
            await this.tryAlternativePorts();
        }
    }
    
    async tryAlternativePorts() {
        const currentPort = parseInt(window.location.port);
        const portsToTry = [
            currentPort - 1,  // Most likely (frontend = backend + 1)
            currentPort + 1,  // Alternative  
            8002,    // Fallback to generated port
            8002, 8003, 8004, 8005, 8006, 8007, 8008  // Common ports
        ];
        
        for (const port of portsToTry) {
            try {
                const testUrl = `http://localhost:${port}`;
                console.log('Trying backend at:', testUrl);
                const response = await fetch(testUrl + '/health');
                if (response.ok) {
                    console.log('Found backend at port:', port);
                    // Update BACKEND_URL globally
                    window.BACKEND_URL = testUrl;
                    this.updateStatus('🟢 Connected', 'connected');
                    return;
                }
            } catch (e) {
                // Port not available, continue trying
            }
        }
        
        this.updateStatus('🔴 No Backend Found', 'error');
    }
    
    getBackendUrl() {
        return window.BACKEND_URL || BACKEND_URL;
    }
    
    updateStatus(text, className) {
        this.status.textContent = text;
        this.status.className = `status ${className}`;
    }
    
    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;
        
        this.addMessage(message, 'user');
        this.input.value = '';
        this.setLoading(true);
        
        try {
            const backendUrl = this.getBackendUrl();
            console.log('Sending message to:', backendUrl + '/query');
            const response = await fetch(`${backendUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: message,
                    max_turns: 20
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.addMessage(result.response, 'assistant');
                // Refresh files after each query in case new files were generated
                setTimeout(() => this.loadFiles(), 2000);
            } else {
                this.addMessage(`Error: ${result.error || 'Unknown error'}`, 'assistant error');
            }
        } catch (error) {
            this.addMessage(`Connection error: ${error.message}`, 'assistant error');
            this.updateStatus('🔴 Connection Error', 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.messages.appendChild(messageDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }
    
    setLoading(loading) {
        this.sendButton.disabled = loading;
        const sendText = this.sendButton.querySelector('.send-text');
        const loadingSpan = this.sendButton.querySelector('.loading');
        
        if (loading) {
            sendText.style.display = 'none';
            loadingSpan.style.display = 'inline';
        } else {
            sendText.style.display = 'inline';
            loadingSpan.style.display = 'none';
        }
    }
    
    async loadFiles() {
        try {
            const backendUrl = this.getBackendUrl();
            console.log('Loading files from:', backendUrl + '/files');
            const response = await fetch(`${backendUrl}/files`);
            const result = await response.json();
            
            this.displayFiles(result.files || []);
        } catch (error) {
            console.error('Error loading files:', error);
        }
    }
    
    displayFiles(files) {
        const filesList = document.getElementById('filesList');
        
        if (files.length === 0) {
            filesList.innerHTML = '<p class="no-files">No files generated yet</p>';
            return;
        }
        
        const backendUrl = this.getBackendUrl();
        filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <span class="file-name" title="${file.filename}">${file.filename}</span>
                <a href="${backendUrl}/files/${file.filename}" 
                   class="download-btn" 
                   download="${file.filename}"
                   target="_blank">
                   ⬇️ Download
                </a>
            </div>
        `).join('');
    }
}

// Global function for refresh button
function loadFiles() {
    if (window.agentChat) {
        window.agentChat.loadFiles();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.agentChat = new AgentChat();
});