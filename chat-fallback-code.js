// Chat localStorage fallback functions
// Add these to chat.html after line 747 (after conversationHistory declaration)

function getLocalChatKey() {
    const uid = localStorage.getItem('partnerai_user_id') || 'guest';
    return `partnerai_chat_history_${uid}`;
}

function loadLocalChat() {
    try {
        return JSON.parse(localStorage.getItem(getLocalChatKey()) || '[]');
    } catch (_) {
        return [];
    }
}

function saveLocalChat(history) {
    localStorage.setItem(getLocalChatKey(), JSON.stringify(history || []));
}

// Modified loadFreshHistory() - replace existing function
async function loadFreshHistory() {
    try {
        const res = await fetch('/api/init', { method: 'GET' });
        if (res.ok) {
            const data = await res.json();
            if (data.history && Array.isArray(data.history)) {
                conversationHistory = data.history;
                saveLocalChat(conversationHistory);  // Save to browser
                console.log('✅ Fresh history loaded from /api/init:', conversationHistory.length, 'messages');
                renderInitialHistory();
            }
        }
    } catch (e) {
        console.warn('Could not load fresh history from /api/init:', e);
        // Fallback to browser-saved history
        conversationHistory = loadLocalChat();
        console.log('📱 Loaded from browser cache:', conversationHistory.length, 'messages');
        renderInitialHistory();
    }
}

// Modified addUserMsg() - add this line after saving to server
// (Find where it saves message and add: conversationHistory.push(...); saveLocalChat(...);)

// Modified addAiMsgStatic() and streaming message handlers
// (Add saveLocalChat(conversationHistory) after each message is added)
