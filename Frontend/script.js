const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-backend-url.onrender.com';

let currentConversationId = null;
let isProcessing = false;
let conversations = JSON.parse(localStorage.getItem('conversations') || '{}');

const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const themeToggle = document.getElementById('themeToggle');
const newChatBtn = document.getElementById('newChatBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const welcomeScreen = document.getElementById('welcomeScreen');
const conversationList = document.getElementById('conversationList');

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing RAG Chatbot...');
    initializeTheme();
    setupEventListeners();
    loadConversations();
    checkBackendHealth();
});

async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('✓ Backend connected');
        }
    } catch (error) {
        console.error('✗ Backend not reachable. Make sure it\'s running on port 8000');
        uploadStatus.textContent = '⚠ Backend offline';
        uploadStatus.style.color = '#f44336';
    }
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function setupEventListeners() {
    themeToggle.addEventListener('click', toggleTheme);
    sidebarToggle.addEventListener('click', toggleSidebar);
    
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            sidebar.classList.contains('active') && 
            !sidebar.contains(e.target) && 
            e.target !== sidebarToggle) {
            sidebar.classList.remove('active');
        }
    });
    
    newChatBtn.addEventListener('click', startNewChat);
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    
    setupDragAndDrop();
    
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyDown);
    sendBtn.addEventListener('click', sendMessage);
    
    window.addEventListener('resize', handleResize);
}

function toggleSidebar() {
    sidebar.classList.toggle('active');
}

function handleInputChange() {
    const hasText = messageInput.value.trim() !== '';
    sendBtn.disabled = !hasText || isProcessing;
    autoResizeTextarea();
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) {
            sendMessage();
        }
    }
}

function handleResize() {
    if (window.innerWidth > 768) {
        sidebar.classList.remove('active');
    }
}

function setupDragAndDrop() {
    const dropZones = [chatMessages, welcomeScreen];
    
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.style.backgroundColor = 'var(--bg-tertiary)';
        });
        
        zone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            zone.style.backgroundColor = '';
        });
        
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.style.backgroundColor = '';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileUpload({ target: { files: files } });
            }
        });
    });
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    const newHeight = Math.min(messageInput.scrollHeight, 200);
    messageInput.style.height = newHeight + 'px';
}

function startNewChat() {
    currentConversationId = null;
    chatMessages.innerHTML = '';
    welcomeScreen.classList.remove('hidden');
    chatMessages.classList.add('hidden');
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;
    
    updateConversationListUI();
}

function loadConversations() {
    conversationList.innerHTML = '';
    
    const convArray = Object.entries(conversations)
        .map(([id, conv]) => ({ id, ...conv }))
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    convArray.forEach(conv => {
        addConversationToList(conv.id, conv.first_message, false);
    });
}

function addConversationToList(id, firstMessage, isNew = true) {
    const item = document.createElement('div');
    item.className = 'conversation-item';
    if (currentConversationId === id) {
        item.classList.add('active');
    }
    
    const truncated = firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '');
    item.textContent = truncated;
    item.dataset.conversationId = id;
    item.title = firstMessage;
    
    item.addEventListener('click', () => loadConversation(id));
    
    if (isNew) {
        conversationList.insertBefore(item, conversationList.firstChild);
        
        conversations[id] = {
            first_message: firstMessage,
            created_at: new Date().toISOString()
        };
        localStorage.setItem('conversations', JSON.stringify(conversations));
    } else {
        conversationList.appendChild(item);
    }
}

async function loadConversation(id) {
    currentConversationId = id;
    chatMessages.innerHTML = '';
    welcomeScreen.classList.add('hidden');
    chatMessages.classList.remove('hidden');
    
    updateConversationListUI();
    
    try {
        const response = await fetch(`${API_BASE_URL}/history/${id}`);
        if (!response.ok) throw new Error('Failed to load conversation');
        
        const data = await response.json();
        
        data.messages.forEach(msg => {
            if (msg.role === 'user') {
                addMessage('user', msg.content);
            } else {
                const confidence = msg.metadata?.confidence;
                addMessage('assistant', msg.content, confidence);
            }
        });
        
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
    
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('active');
    }
}

function updateConversationListUI() {
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.conversationId === currentConversationId) {
            item.classList.add('active');
        }
    });
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const validTypes = ['.pdf', '.txt', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        uploadStatus.textContent = '✗ Invalid file type';
        uploadStatus.style.color = '#f44336';
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.style.color = '';
        }, 3000);
        fileInput.value = '';
        return;
    }
    
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        uploadStatus.textContent = '✗ File too large (max 10MB)';
        uploadStatus.style.color = '#f44336';
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.style.color = '';
        }, 3000);
        fileInput.value = '';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadStatus.textContent = `Uploading ${file.name}...`;
    uploadStatus.style.color = 'var(--text-secondary)';
    uploadBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const data = await response.json();
        uploadStatus.textContent = `✓ ${file.name} (${data.chunks_created} chunks)`;
        uploadStatus.style.color = '#10a37f';
        
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.style.color = '';
        }, 5000);
        
    } catch (error) {
        console.error('Upload error:', error);
        uploadStatus.textContent = `✗ ${error.message}`;
        uploadStatus.style.color = '#f44336';
        
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.style.color = '';
        }, 5000);
    } finally {
        uploadBtn.disabled = false;
        fileInput.value = '';
    }
}

async function sendMessage() {
    const query = messageInput.value.trim();
    if (!query || isProcessing) return;
    
    welcomeScreen.classList.add('hidden');
    chatMessages.classList.remove('hidden');
    
    addMessage('user', query);
    
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;
    
    const typingId = addTypingIndicator();
    
    isProcessing = true;
    messageInput.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                conversation_id: currentConversationId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Query failed');
        }
        
        const data = await response.json();
        
        if (!currentConversationId) {
            currentConversationId = data.conversation_id;
            addConversationToList(currentConversationId, query, true);
        }
        
        removeTypingIndicator(typingId);
        
        await addMessageWithTyping('assistant', data.answer, data.confidence, data.sources);
        
    } catch (error) {
        console.error('Query error:', error);
        removeTypingIndicator(typingId);
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}`, 0);
    } finally {
        isProcessing = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

function addMessage(role, content, confidence = null, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'A';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = content;
    
    messageContent.appendChild(messageText);
    
    if (role === 'assistant' && confidence !== null) {
        const meta = createMessageMeta(confidence);
        messageContent.appendChild(meta);
        
        if (sources && sources.length > 0) {
            const sourcesSection = createSourcesSection(sources);
            messageContent.appendChild(sourcesSection);
        }
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

async function addMessageWithTyping(role, content, confidence, sources) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'A';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    
    messageContent.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    let index = 0;
    const speed = 8;
    
    await new Promise(resolve => {
        const typingInterval = setInterval(() => {
            if (index < content.length) {
                messageText.textContent += content[index];
                index++;
                scrollToBottom();
            } else {
                clearInterval(typingInterval);
                resolve();
            }
        }, speed);
    });
    
    if (confidence !== null) {
        const meta = createMessageMeta(confidence);
        messageContent.appendChild(meta);
        
        if (sources && sources.length > 0) {
            const sourcesSection = createSourcesSection(sources);
            messageContent.appendChild(sourcesSection);
        }
    }
    
    scrollToBottom();
}

function createMessageMeta(confidence) {
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    
    const confidenceBadge = document.createElement('span');
    confidenceBadge.className = `confidence-badge ${getConfidenceClass(confidence)}`;
    confidenceBadge.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        Confidence: ${confidence}/10
    `;
    
    meta.appendChild(confidenceBadge);
    return meta;
}

function createSourcesSection(sources) {
    const section = document.createElement('div');
    section.className = 'sources-section';
    
    const header = document.createElement('div');
    header.className = 'sources-header';
    header.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        Sources (${sources.length})
    `;
    section.appendChild(header);
    
    sources.forEach((source, index) => {
        const item = document.createElement('div');
        item.className = 'source-item';
        
        const name = document.createElement('div');
        name.className = 'source-name';
        name.innerHTML = `${index + 1}. ${source.source}`;
        
        const preview = document.createElement('div');
        preview.className = 'source-preview';
        preview.textContent = source.text_preview;
        
        item.appendChild(name);
        item.appendChild(preview);
        
        item.addEventListener('click', () => {
            item.classList.toggle('expanded');
        });
        
        section.appendChild(item);
    });
    
    return section;
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.id = id;
    messageDiv.className = 'message assistant-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'A';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    messageContent.appendChild(typingIndicator);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

function getConfidenceClass(confidence) {
    if (confidence >= 8) return 'confidence-high';
    if (confidence >= 6) return 'confidence-medium';
    return 'confidence-low';
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});

console.log('%cRAG Chatbot', 'font-size: 20px; font-weight: bold; color: #10a37f;');
console.log('%cBackend: ' + API_BASE_URL, 'color: #666;');
console.log('%cSupported files: PDF, TXT, DOCX, PNG, JPG, TIFF', 'color: #666;');
