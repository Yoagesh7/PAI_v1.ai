# 🎬 Notion-like Workspace: Visual Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NOTION-LIKE WORKSPACE v1.0                      │
│                                                                       │
│  BLOCK EDITOR (block_editor.html)                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                              │   │
│  │  [← Back]  [💡 Type]       [Search...]  [🤖 AI]  [Save] [X] │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────┐                  │   │
│  │  │ 💡 Untitled Block                    │                  │   │
│  │  │                                      │   AI SIDEBAR     │   │
│  │  │ Type some content here...           │  ┌────────────┐  │   │
│  │  │                                      │  │ 🤖 AI      │  │   │
│  │  │ - [ ] Checkbox item 1                │  │ Assistant  │ X│  │
│  │  │ - [x] Completed item                 │  ├────────────┤  │   │
│  │  │                                      │  │ ✍️ 📋 🔭   │  │   │
│  │  │ **Bold** _italic_ `code`             │  │ ⚡ 🏷️ 🤖   │  │   │
│  │  │                                      │  ├────────────┤  │   │
│  │  │                                      │  │ Chat       │  │   │
│  │  │                                      │  │ history:   │  │   │
│  │  │                                      │  │            │  │   │
│  │  │                                      │  │ User:      │  │   │
│  │  │                                      │  │ "Improve   │  │   │
│  │  │                                      │  │ this"      │  │   │
│  │  │                                      │  │            │  │   │
│  │  │                                      │  │ AI:        │  │   │
│  │  │                                      │  │ "Here's an │  │   │
│  │  │                                      │  │ improved   │  │   │
│  │  │                                      │  │ version"   │  │   │
│  │  │                                      │  │            │  │   │
│  │  │                                      │  │ [✅ Apply] │  │   │
│  │  │                                      │  │ [📋 Copy]  │  │   │
│  │  │                                      │  ├────────────┤  │   │
│  │  │                                      │  │ Ask AI to  │  │   │
│  │  │                                      │  │ edit...    │  │   │
│  │  │                                      │  │      ↗     │  │   │
│  │  │                                      │  └────────────┘  │   │
│  │  └──────────────────────────────────────┘                  │   │
│  │                                                              │   │
│  │                       🏷️ Tags:                              │   │
│  │                    [+ add tag]                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

RIGHT-CLICK CONTEXT MENU:
┌─────────────────┐
│ ✍️ Edit with AI │
│ 💬 Ask AI       │
│ 📋 Copy         │
│ 🗑️ Delete       │
└─────────────────┘
```

## Component Breakdown

### 1. Block Editor (Existing)
- Rich text editing
- Block-based structure
- Markdown support
- Multiple block types

### 2. AI Sidebar (NEW)
```
FILE: web/templates/block_editor_ai_sidebar.html

LAYOUT:
┌────────────────────┐
│ Header             │ ← Close button
├────────────────────┤
│ Mode Tabs (6)      │ ← [✍️][📋][🔭][⚡][🏷️][🤖]
├────────────────────┤
│ Chat Messages      │ ← User & AI messages
│                    │   with apply/copy buttons
├────────────────────┤
│ Prompt Input       │ ← Text area + send button
└────────────────────┘

STYLES:
- Width: 380px (desktop), 320px (tablet), 100% (mobile)
- Position: Fixed right sidebar
- Animation: Slide in/out
- Theme: Dark mode match
- Responsive: Mobile-friendly
```

### 3. Context Menu (NEW)
```
FILE: web/templates/block_editor_ai_sidebar.html

LAYOUT:
┌─────────────────────┐
│ 🎯 Edit with AI     │
│ 💬 Ask AI           │
│ 📋 Copy             │
│ 🗑️  Delete          │
└─────────────────────┘

BEHAVIOR:
- Right-click trigger
- Follows cursor position
- Click outside to close
- Keyboard-accessible
```

## Data Flow Diagram

```
USER INTERACTION
        │
        ▼
    ┌─────────────────────────────────┐
    │ Frontend (HTML/JS)              │
    │ - AI Sidebar                    │
    │ - Context Menu                  │
    │ - Event Listeners               │
    └──────────┬──────────────────────┘
               │
               │ POST /api/block-ai/process
               │ (JSON payload)
               ▼
    ┌─────────────────────────────────┐
    │ Flask Backend (app.py)          │
    │ - Request validation            │
    │ - Auth check                    │
    │ - Route dispatch                │
    └──────────┬──────────────────────┘
               │
               │ BlockAIRoutes
               ▼
    ┌─────────────────────────────────┐
    │ block_ai_routes.py              │
    │ - /process - Main AI endpoint   │
    │ - /stream - Streaming response  │
    │ - /modes - Available modes      │
    │ - /notifications - Alerts       │
    │ - /table/* - Table analysis     │
    └──────────┬──────────────────────┘
               │
               │ Instantiate engines
               ▼
    ┌─────────────────────────────────┐
    │ block_ai_engine.py              │
    │ - BlockAIEngine                 │
    │   - process_block_request()     │
    │   - stream_ai_response()        │
    │ - TableAIEngine                 │
    │   - analyze_table()             │
    │ - NotificationEngine            │
    │   - create_notification()       │
    └──────────┬──────────────────────┘
               │
               │ Call AI API
               ▼
    ┌─────────────────────────────────┐
    │ nvidia_llm.py (or local_llm)    │
    │ - call_ai()                     │
    │ - rag_system                    │
    └──────────┬──────────────────────┘
               │
               │ LLM Response
               ▼
    ┌─────────────────────────────────┐
    │ Response Processing             │
    │ - Format result                 │
    │ - Create metadata               │
    │ - Log usage                     │
    └──────────┬──────────────────────┘
               │
               │ JSON Response
               ▼
    ┌─────────────────────────────────┐
    │ Frontend Handler (JS)           │
    │ - Display message               │
    │ - Show apply button             │
    │ - Copy to clipboard             │
    │ - Apply to block                │
    └─────────────────────────────────┘
```

## AI Modes Flowchart

```
USER SENDS PROMPT
        │
        ▼
    ┌────────────────────┐
    │ Select Mode        │
    │ ┌─────────────────┐│
    │ │ ✍️ Improve     ││
    │ │ 📋 Summarize   ││
    │ │ 🔭 Expand      ││
    │ │ ⚡ Actions     ││
    │ │ 🏷️ Tags       ││
    │ │ 🤖 Custom      ││
    │ └─────────────────┘│
    └────────────┬───────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
    ┌─────────┐     ┌──────────┐
    │Preset   │     │ Custom   │
    │Mode     │     │ Prompt   │
    └────┬────┘     └────┬─────┘
         │               │
         └───────┬───────┘
                 ▼
         ┌──────────────┐
         │Build Prompt  │
         │+ Content     │
         │+ Context     │
         └────┬─────────┘
              │
              ▼
         ┌──────────────┐
         │Call AI API   │
         │(nvidia_llm)  │
         └────┬─────────┘
              │
              ▼
         ┌──────────────┐
         │Get Response  │
         │             │
         └────┬─────────┘
              │
         ┌────┴─────┐
         ▼          ▼
    ┌─────────┐ ┌────────┐
    │ Apply   │ │ Copy   │
    │ to      │ │ to     │
    │ Block   │ │ CB     │
    └─────────┘ └────────┘
```

## Component Interaction

```
block_editor.html
├─ Topbar
│  └─ [🤖 AI Button] ──┐
│                      │
├─ Main Editor         │
│  └─ Block Content    │
│     └─ Right-click   │──┐
│        menu trigger      │
│                          │
└─ AI Sidebar (hidden) ◄──┴──┐
   ├─ Header                 │
   │  └─ Close button        │
   ├─ Mode Tabs              │
   │  └─ 6 AI modes          │
   ├─ Chat Area              │
   │  ├─ Messages            │
   │  └─ Apply/Copy buttons  │
   └─ Input Area             │
      ├─ Prompt textarea     │
      └─ Send button         │
      
Context Menu (hidden)
├─ Edit with AI ─┐
├─ Ask AI        │
├─ Copy          │
└─ Delete        │
                 │
        Opening triggers
        Both sidebar & menu
        with context
```

## Request/Response Flow

### Process Block Request
```json
{
  "block_id": "123",
  "content": "Your block content",
  "mode": "improve",
  "custom_prompt": null,
  "block_type": "text",
  "context": {
    "title": "Block Title",
    "tags": ["tag1", "tag2"]
  }
}
      │
      ▼ POST /api/block-ai/process
     
Response:
{
  "success": true,
  "result": "Improved content from AI",
  "mode": "improve",
  "timestamp": "2026-05-25T10:30:00Z",
  "tokens_used": 142
}
```

### Notification Creation
```json
{
  "block_id": "123",
  "type": "due_date",
  "message": "Review this block",
  "due_date": "2026-05-30T10:00:00Z",
  "metadata": {...}
}
      │
      ▼ POST /api/block-ai/notifications
     
Response:
{
  "success": true,
  "notification": {
    "id": "notif_456",
    "user_id": "user_123",
    "block_id": "123",
    ...
  }
}
```

## Feature Matrix

| Feature | Frontend | Backend | Status |
|---------|----------|---------|--------|
| AI Sidebar | ✅ HTML/CSS/JS | ✅ Routes | Ready |
| Context Menu | ✅ HTML/CSS/JS | ✅ Routes | Ready |
| AI Modes (6) | ✅ UI tabs | ✅ Engines | Ready |
| Block Process | ✅ Form | ✅ API | Ready |
| Message History | ✅ DOM | ✅ Client | Ready |
| Apply/Copy | ✅ Buttons | ✅ JS | Ready |
| Notifications | 🔨 Framework | 🔨 Framework | Planned |
| Due Dates | 🔨 Framework | 🔨 Framework | Planned |
| Calendar View | ⏳ Design | ⏳ Design | Phase 3c |
| Integrations | ⏳ Design | ⏳ Design | Phase 3c |

---

## File Structure

```
e:\PartnerAI
├── block_ai_engine.py                    (NEW - 300 lines)
│   ├── BlockAIEngine class
│   ├── TableAIEngine class
│   └── NotificationEngine class
│
├── web/
│   ├── app.py                            (MODIFIED - +10 lines)
│   │   └── Register block_ai_bp
│   │
│   ├── block_ai_routes.py                (NEW - 400 lines)
│   │   ├── block_ai_bp blueprint
│   │   ├── /process endpoint
│   │   ├── /stream endpoint
│   │   ├── /modes endpoint
│   │   ├── /notifications endpoints
│   │   └── /due-dates endpoint
│   │
│   └── templates/
│       ├── block_editor.html             (MODIFIED - +5 lines)
│       │   ├── AI button in topbar
│       │   └── Include sidebar
│       │
│       └── block_editor_ai_sidebar.html  (NEW - 600 lines)
│           ├── Sidebar styles
│           ├── Context menu styles
│           ├── Sidebar HTML
│           ├── Context menu HTML
│           └── JS logic (900 lines)
│
└── Documentation/
    ├── NOTION_AI_INTEGRATION.md          (Setup guide)
    ├── PHASE_2_COMPLETE.md               (Summary)
    └── QUICK_START_NOTION_AI.md          (This file)
```

---

**Total New Code: ~2,200 lines**
**Setup Time: < 10 minutes**
**Features Added: 15+**
