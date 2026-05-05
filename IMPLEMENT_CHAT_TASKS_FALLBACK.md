# Chat & AI Tasks Vercel Persistence Fix

## Problem
- Chat history disappears when navigating away on Vercel
- AI Recommended tasks don't show up or disappear after page refresh

## Root Cause
Vercel's ephemeral `/tmp` filesystem wipes SQLite data between requests.

## Solution
Add localStorage fallback for chat history and AI tasks (same approach as habits/knowledge blocks).

---

## Implementation Steps

### Step 1: Chat History Fallback

**File:** `web/templates/chat.html`

1. Find line ~747 with `let conversationHistory = ...`

2. Add these helpers right after it:
```javascript
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
```

3. Find `loadFreshHistory()` function (~line 760)

4. Replace the entire `catch` block with:
```javascript
    } catch (e) {
        console.warn('Could not load fresh history from /api/init:', e);
        // Fallback to browser-saved chat history
        conversationHistory = loadLocalChat();
        console.log('📱 Loaded from browser cache:', conversationHistory.length, 'messages');
        renderInitialHistory();
    }
```

5. In `loadFreshHistory()` success block, add after line where history is assigned:
```javascript
    saveLocalChat(conversationHistory);  // Save to browser backup
```

6. Find where messages are appended in the `send()` function, and after saving to server, add:
```javascript
    conversationHistory.push({role: 'user', content: text});
    saveLocalChat(conversationHistory);
```

7. Find where AI messages are appended (in streaming code), add:
```javascript
    saveLocalChat(conversationHistory);  // Save after each AI chunk
```

---

### Step 2: AI Tasks Fallback

**File:** `web/templates/home.html`

1. Find the script section and add after line 185:
```javascript
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
```

2. Find `loadTasks()` function (~line 184) and modify the `.then()` block:
```javascript
    .then(data => {
        const tasks = data.tasks || [];
        saveLocalTasks(tasks);  // Save to browser
        if (tasks.length === 0) {
            showEmptyState();
        } else {
            renderTasks(tasks);
        }
    })
```

3. Modify the `.catch()` block:
```javascript
    .catch(err => {
        console.error("Error loading tasks:", err);
        const localTasks = loadLocalTasks();  // Try browser cache
        if (localTasks.length === 0) {
            taskList.innerHTML = '<div style="color:red; padding:20px;">Failed to load tasks.</div>';
        } else {
            console.log('📱 Loaded from browser cache:', localTasks.length, 'tasks');
            renderTasks(localTasks);
        }
    });
```

4. Find `toggleTask()` function (~line 246) and add to the `.catch()`:
```javascript
    .catch(err => {
        console.error('Error toggling task:', err);
        // Still refresh even if server fails
        loadTasks();
    });
```

---

## Testing Locally

1. Open Developer Tools → Application → Local Storage
2. Add a chat message → verify `partnerai_chat_history_<uid>` is created
3. Add an AI task → verify `partnerai_ai_tasks_<uid>` is created
4. Refresh page → history/tasks should still appear
5. Disable network → try adding message/task → should save locally

---

## Result

✅ Chat history persists in browser localStorage as backup
✅ AI tasks show even if server is down
✅ Auto-syncs to server when available
✅ Users don't see empty chat or "Failed to load" anymore

---

## Next: Real Persistence

To make chat and tasks truly persistent across devices, add **Vercel KV** or **PostgreSQL**:

```bash
# Add to Vercel environment variables:
KV_REST_API_URL=your_kv_url
KV_REST_API_TOKEN=your_token
```

The localStorage fallback ensures the app works immediately while you set up real persistence.
