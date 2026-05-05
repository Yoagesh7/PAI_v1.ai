// Home page AI tasks localStorage fallback functions
// Add these to home.html after line 185 (in the script section)

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

// Modified loadTasks() - REPLACE the existing function
function loadTasks() {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '<div style="padding:20px; text-align:center; color:var(--color-text-tertiary);">Loading tasks...</div>';

    fetch('/api/ai-tasks')
        .then(r => r.json())
        .then(data => {
            const tasks = data.tasks || [];
            saveLocalTasks(tasks);  // Save to browser
            if (tasks.length === 0) {
                showEmptyState();
            } else {
                renderTasks(tasks);
            }
        })
        .catch(err => {
            console.error("Error loading tasks:", err);
            const localTasks = loadLocalTasks();  // Try browser cache
            if (localTasks.length === 0) {
                taskList.innerHTML = '<div style="color:red; padding:20px;">Failed to load tasks.</div>';
            } else {
                console.log('📱 Loaded tasks from browser cache:', localTasks.length);
                renderTasks(localTasks);
            }
        });
}

// Modified toggleTask() - REPLACE the existing function
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
                loadTasks(); // Reload to reflect state
            }
        })
        .catch(err => {
            console.error('Error toggling task:', err);
            // Still refresh even if server fails
            loadTasks();
        });
}

// No changes needed to clearAllTasks() - it already handles fallback in loadTasks()
