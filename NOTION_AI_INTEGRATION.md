# Notion-like AI Integration Guide

## What's New

Your PartnerAI workspace now has **Notion-like AI superpowers**:

1. **AI Chat Sidebar** - Right sidebar with AI editing modes
2. **Right-Click Context Menu** - Edit with AI directly on content
3. **Full Backend AI Engine** - Process any block/content with AI
4. **Coming Soon**: Notifications, Due Dates, Automations, Calendar View

## Integration Steps

### Step 1: Register API Routes in Flask (app.py)

Add this after line 75 (after other imports):

```python
# Block AI Routes
from web.block_ai_routes import block_ai_bp

app.register_blueprint(block_ai_bp)
```

### Step 2: Include AI Sidebar HTML in block_editor.html

At the end of `block_editor.html`, before `{% endblock %}`, add:

```html
{% include 'block_editor_ai_sidebar.html' %}
```

### Step 3: Update Block Editor Script

In the `<script>` section of `block_editor.html`, make these additions:

#### A. Add AI button to editor topbar (find `<div class="ed-topbar-right">` around line 1320)

Add this button before the Save button:

```html
<button class="ed-tb-btn" id="aiToggleBtn" onclick="openAISidebar()" title="AI Assistant (Ctrl+Shift+A)">
  🤖 AI
</button>
```

#### B. Add function to get block content (add to JavaScript section)

```javascript
function getSelectedBlockContent() {
  const selection = window.getSelection().toString();
  if (selection) return selection;
  
  const textarea = document.querySelector('.ed-edit-mode');
  if (textarea) return textarea.value;
  
  return '';
}

function serializeBlocksToMarkdown() {
  if (!Array.isArray(blocks)) return '';
  return blocks.map(b => b.content || '').join('\n\n');
}
```

#### C. Link keyboard shortcut (add to existing JavaScript)

The sidebar HTML already includes the Ctrl+Shift+A shortcut, but make sure `openAISidebar()` is globally available.

### Step 4: Database Schema Updates (Optional - for notifications)

Add to your `memory.py` (or use Supabase):

```python
# Add to smart_blocks table
ALTER TABLE smart_blocks ADD COLUMN due_date TIMESTAMP;
ALTER TABLE smart_blocks ADD COLUMN notifications JSONB;

# Create new notifications table
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(256),
  block_id INT,
  type VARCHAR(50),
  message TEXT,
  due_date TIMESTAMP,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  read BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (block_id) REFERENCES smart_blocks(id)
);
```

### Step 5: Test the Integration

1. Go to any block editor
2. Press **Ctrl+Shift+A** to open AI sidebar
3. Or click the **🤖 AI** button in topbar
4. Right-click on any block content to see context menu
5. Select "Edit with AI" → chat opens with context

## API Endpoints Reference

### Process Block Content
```
POST /api/block-ai/process
{
  "block_id": "123",
  "content": "Your content here",
  "mode": "improve|summarize|expand|actions|tags|custom",
  "custom_prompt": "Your prompt (for custom mode)",
  "block_type": "text|table|list"
}
```

### Get Available AI Modes
```
GET /api/block-ai/modes
```

### Analyze Table
```
POST /api/block-ai/table/analyze
{
  "block_id": "123",
  "table_data": [[col1, col2], ...],
  "headers": ["Header 1", "Header 2"]
}
```

### Create Notification
```
POST /api/block-ai/notifications
{
  "block_id": "123",
  "type": "due_date|mention|completion|shared|comment|reminder",
  "message": "Notification text",
  "due_date": "2026-05-30T10:00:00Z",
  "metadata": {...}
}
```

### Get Notifications
```
GET /api/block-ai/notifications
```

### Check Due Dates
```
GET /api/block-ai/due-dates
```

## AI Modes Available

- **✍️ Improve** - Enhance clarity, grammar, and impact
- **📋 Summarize** - Create bullet-point summary
- **🔭 Expand** - Add details and examples
- **⚡ Actions** - Extract action items
- **🏷️ Tags** - Suggest relevant tags
- **🤖 Custom** - User-defined prompt

## Features Enabled

✅ AI Chat Sidebar  
✅ Right-Click AI Menu  
✅ 6 AI Modes (+ Custom)  
✅ Block Content Processing  
✅ Table Analysis (coming)  
✅ Backend API  
✅ Message History  
✅ Apply/Copy Results  

## Coming Soon (Phase 3-4)

- [ ] Notifications & Due Dates
- [ ] Calendar View
- [ ] Recurring Tasks
- [ ] Zapier/Webhook Integrations
- [ ] Mention (@user) System
- [ ] Collaboration & Sharing
- [ ] Mobile App Support

## Keyboard Shortcuts

- **Ctrl+Shift+A** - Toggle AI Sidebar
- **Ctrl+Enter** - Send AI Prompt
- **Escape** - Close Sidebar

## Troubleshooting

**"AI system unavailable"**
- Check if `nvidia_llm.py` is loaded
- Verify API credentials in `config.py`
- Check Flask logs for errors

**Sidebar not appearing**
- Make sure `block_editor_ai_sidebar.html` is included
- Check browser console for JS errors
- Verify CSS is loaded

**API returns 401**
- Check user session is authenticated
- Verify Flask session management

---

Need help? Check the logs at `partnerai.log`
