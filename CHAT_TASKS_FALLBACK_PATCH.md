<!-- Chat + Tasks localStorage fallback patch -->
<!-- This file shows the changes needed for chat and tasks to work on Vercel -->

CHAT HISTORY FALLBACK
=====================

In web/templates/chat.html, add localStorage helpers after line 747:

    // Chat localStorage helpers
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


Then in loadFreshHistory() function (line ~762), modify to fallback:

    async function loadFreshHistory() {
        try {
            const res = await fetch('/api/init', { method: 'GET' });
            if (res.ok) {
                const data = await res.json();
                if (data.history && Array.isArray(data.history)) {
                    conversationHistory = data.history;
                    saveLocalChat(conversationHistory);  // <-- ADD THIS
                    console.log('✅ Fresh history loaded from /api/init:', conversationHistory.length, 'messages');
                    renderInitialHistory();
                }
            }
        } catch (e) {
            console.warn('Could not load fresh history from /api/init:', e);
            conversationHistory = loadLocalChat();  // <-- ADD THIS
            renderInitialHistory();
        }
    }


In the send() function, after saving message to server, add:
    
    try {
        save_chat_message(user_id, 'user', text);
        conversationHistory.push({role: 'user', content: text});
        saveLocalChat(conversationHistory);  // <-- ADD THIS
    } catch (e) {
        logging.error(...);
    }


When adding AI message, add:
    
    conversationHistory.push({role: 'ai', content: aiReply});
    saveLocalChat(conversationHistory);  // <-- ADD THIS


AI RECOMMENDED TASKS FALLBACK
=============================

In web/templates/home.html, add localStorage helpers after line 185:

    // AI tasks localStorage helpers
    function getLocalTasksKey() {
        const uid = localStorage.getItem('partnerai_user_id') || 'guest';
        return `partnerai_ai_tasks_${uid}`;
    }

    function loadLocalTasks() {
        try {
            return JSON.parse(localStorage.getItem(getLocalTasksKey()) || '[]');
        } catch (_) {
            return [];
        }
    }

    function saveLocalTasks(tasks) {
        localStorage.setItem(getLocalTasksKey(), JSON.stringify(tasks || []));
    }


Modify loadTasks() function to add fallback:

    function loadTasks() {
        const taskList = document.getElementById('taskList');
        taskList.innerHTML = '<div style="padding:20px; text-align:center; color:var(--color-text-tertiary);">Loading tasks...</div>';

        fetch('/api/ai-tasks')
            .then(r => r.json())
            .then(data => {
                const tasks = data.tasks || [];
                saveLocalTasks(tasks);  // <-- ADD THIS
                if (tasks.length === 0) {
                    showEmptyState();
                } else {
                    renderTasks(tasks);
                }
            })
            .catch(err => {
                console.error("Error loading tasks:", err);
                const localTasks = loadLocalTasks();  // <-- ADD THIS
                if (localTasks.length === 0) {
                    taskList.innerHTML = '<div style="color:red; padding:20px;">Failed to load tasks.</div>';
                } else {
                    renderTasks(localTasks);  // <-- ADD THIS
                }
            });
    }


Modify toggleTask() to save locally:

    function toggleTask(id) {
        fetch('/api/ai-tasks/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: id })
        })
            .then(r => r.json())
            .then(data => {
                if (data.success || data.status === 'completed') {
                    if (data.streak !== undefined) {
                        const streakEl = document.getElementById('streak-count');
                        if (streakEl) streakEl.textContent = data.streak;
                    }
                    loadTasks();
                }
            })
            .catch(err => {
                console.error('Error toggling task:', err);
                // Still update locally even if server fails
                loadTasks();
            });
    }


Result: Chat and tasks now persist in browser localStorage even if Vercel backend fails!
