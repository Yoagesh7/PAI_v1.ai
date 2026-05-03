// Clear Chat History Function
function clearChatHistory() {
    if (!confirm('Clear all chat messages? This cannot be undone.')) {
        return;
    }

    // Remove all message elements
    const chatBox = document.getElementById('chat-box');
    const messages = chatBox.querySelectorAll('.message');
    messages.forEach(msg => msg.remove());

    // Show the intro overlay again
    const intro = document.getElementById('intro-overlay');
    if (intro) {
        intro.style.display = 'flex';
    }

    // Clear chat history on server
    fetch('/api/clear_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(res => res.json())
        .then(data => {
            console.log('Chat history cleared');
        })
        .catch(err => console.error('Error clearing chat:', err));
}
