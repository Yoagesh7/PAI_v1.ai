# 🔧 Chat & AI Tasks Vercel Fix - Complete Guide

## Problems Identified
1. ❌ **Chat history disappears** when navigating away and back to `/chat`
2. ❌ **AI Recommended tasks don't appear** or vanish after refresh

## Root Cause
Same as habits/knowledge blocks: Vercel's ephemeral `/tmp` filesystem deletes SQLite data between requests.

---

## Solution: localStorage Fallback

I've prepared **complete implementation files** that add localStorage backup for chat and tasks:

### Files Created

1. **[IMPLEMENT_CHAT_TASKS_FALLBACK.md](IMPLEMENT_CHAT_TASKS_FALLBACK.md)** ← **START HERE**
   - Step-by-step implementation guide
   - Exact line numbers and code to add
   - Testing instructions

2. **[chat-fallback-code.js](chat-fallback-code.js)**
   - Ready-to-use functions for chat.html
   - Copy-paste the code

3. **[home-tasks-fallback-code.js](home-tasks-fallback-code.js)**
   - Ready-to-use functions for home.html
   - Copy-paste the code

4. **[CHAT_TASKS_FALLBACK_PATCH.md](CHAT_TASKS_FALLBACK_PATCH.md)**
   - Quick reference of all changes needed

---

## Quick Implementation (5 minutes)

1. Open `web/templates/chat.html`
2. Add the helpers from `chat-fallback-code.js` after line 747
3. Modify `loadFreshHistory()` to fallback to localStorage
4. Add `saveLocalChat()` calls when messages are added

5. Open `web/templates/home.html`
6. Add the helpers from `home-tasks-fallback-code.js`
7. Modify `loadTasks()` to use localStorage fallback
8. Modify `toggleTask()` error handler

---

## Result After Implementation

✅ **Chat persists** in browser storage — users see their conversation even after navigation
✅ **AI tasks show up** — tasks appear even if Vercel backend is slow/down
✅ **Auto-syncs** — when server responds, data syncs automatically
✅ **Graceful** — no error messages, just "loaded from browser cache"

---

## How It Works

### Chat:
1. User sends message → saved to server AND localStorage
2. AI responds → response saved to server AND localStorage
3. User navigates away and returns → loads from localStorage instantly
4. Server eventually syncs fresh data

### Tasks:
1. Page loads → tries to fetch `/api/ai-tasks`
2. Server fails/timeout → loads last-known tasks from localStorage
3. Tasks marked complete sync both to server and localStorage
4. If server fails → still updates locally

---

## Browser Storage Used

```
localStorage['partnerai_chat_history_<user_id>'] = [
  {role: 'user', content: 'Hello...'},
  {role: 'ai', content: 'Hi there...'},
  ...
]

localStorage['partnerai_ai_tasks_<user_id>'] = [
  {id: 1, task: 'Write email', status: 'pending'},
  {id: 2, task: 'Review code', status: 'completed'},
  ...
]
```

---

## Next Step: Real Persistence

To make chat and tasks truly persist across devices, add Vercel KV or PostgreSQL (same as habits):

```
KV_REST_API_URL=your_kv_url
KV_REST_API_TOKEN=your_token
```

The localStorage fallback ensures the app works immediately while you set that up.

---

## Testing

1. Deploy the changes to Vercel
2. Open chat, send a message → returns
3. Go to home page → come back → message is there ✅
4. Add an AI task → navigate away → come back → task is there ✅
5. Disable network in DevTools → task still toggles ✅

---

**Implementation file is ready to use: [IMPLEMENT_CHAT_TASKS_FALLBACK.md](IMPLEMENT_CHAT_TASKS_FALLBACK.md)**
