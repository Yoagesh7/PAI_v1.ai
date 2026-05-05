# Execution Coach - Complete Integration Guide

## 📋 Overview

You now have a complete **Execution Coach** system for PartnerAI with:
- **4 modular backend modules** (planner, metrics, recovery, personalizer)
- **6 database tables** with migrations
- **7 Flask API routes** for all operations
- **Complete UI component** with vanilla JS
- **Integration points** for focus mode, reminders, reports, and chat

This guide provides step-by-step instructions to integrate everything into your existing Flask + SQLite + Jinja + Vanilla JS architecture.

---

## 🎯 What You Have

### Backend Modules (4 files)
```
execution_planner.py          → Generates daily plans with priorities & time blocks
execution_metrics.py          → Computes momentum score & status (On Track/At Risk/Recovery)
execution_recovery.py         → Creates lighter rescue plans for falling behind
execution_personalizer.py     → Tailors plans to user preferences & work style
```

### Database Migration
```
migrate_execution_coach.py    → Creates 6 tables in your SQLite database
```

### Routes Template
```
EXECUTION_COACH_ROUTES.py     → 7 API endpoints (copy into web/app.py)
```

### UI Component
```
EXECUTION_COACH_UI.html       → HTML + vanilla JS (copy into templates)
```

---

## ⚙️ Step-by-Step Integration

### Step 1: Run Database Migration

```bash
cd e:\PartnerAI
python migrate_execution_coach.py
```

**Expected output:**
```
Creating Execution Coach tables...
✅ execution_plans table created
✅ execution_blocks table created
✅ execution_events table created
✅ execution_preferences table created
✅ execution_reflections table created
✅ execution_recovery_plans table created
✅ All Execution Coach tables created successfully!
```

**What this creates:**
- `execution_plans` - Daily plans with priorities and time blocks
- `execution_blocks` - Individual time blocks within a plan
- `execution_events` - User interactions with execution system
- `execution_preferences` - User preferences (chronotype, task style, etc.)
- `execution_reflections` - Daily reflections and feedback
- `execution_recovery_plans` - Recovery plans when falling behind

### Step 2: Add Imports to web/app.py (Top of file, around line 75)

Find this section in `web/app.py`:
```python
from habits_db import init_habits_db, create_habit, get_user_habits, toggle_habit, get_weekly_stats, analyze_habits_ai, delete_habit
```

**Add these lines after it:**
```python
# Execution Coach imports
try:
    from execution_planner import ExecutionPlanner, DailyExecutionPlan
    from execution_metrics import ExecutionMetrics, MomentumStatus
    from execution_recovery import ExecutionRecovery
    from execution_personalizer import ExecutionPersonalizer, UserPreferences
    print("✅ Execution Coach modules loaded successfully")
except ImportError as e:
    print(f"⚠️  Execution Coach modules not available: {e}")
```

### Step 3: Add Routes to web/app.py

**Location:** Find where your other API routes are defined (around line 2500+)

**Copy these routes from EXECUTION_COACH_ROUTES.py and add them to web/app.py:**

The routes include:
1. `GET /api/execution/today` - Get today's execution plan
2. `POST /api/execution/rebuild-day` - Activate recovery mode
3. `GET /api/execution/momentum` - Get momentum status
4. `POST /api/execution/start-block` - Start a focus block
5. `POST /api/execution/complete-block` - Mark block complete
6. `GET/POST /api/execution/preferences` - User preferences
7. `POST /api/execution/reflection` - Save daily reflection
8. `GET /api/execution/summary` - Weekly/monthly summary

**Copy the complete routes section from EXECUTION_COACH_ROUTES.py** (the code between the large comment blocks) into your app.py file.

### Step 4: Add UI to Home Dashboard

**Option A: Add to existing home.html (Recommended)**

Open `web/templates/home.html`

Find where the content ends (before `{% endblock %}`)

**Copy the HTML section from EXECUTION_COACH_UI.html** and paste it after the "Talk to Mentor Button" section, before the closing tag.

**Option B: Create dedicated execution.html template**

If you prefer a separate page:

1. Create `web/templates/execution.html`
2. Copy content from `EXECUTION_COACH_UI.html`
3. Wrap in Jinja template structure:
```html
{% extends "base.html" %}

{% block content %}
<!-- Paste EXECUTION_COACH_UI.html content here -->
{% endblock %}
```

4. Add route to app.py:
```python
@app.route('/execution')
def execution_coach():
    return render_template('execution.html')
```

### Step 5: Helper Functions for Data Collection

Add these helper functions to `memory.py` if they don't exist (for fetching user data):

```python
def get_user_daily_tasks_for_date(user_id, date_str):
    """Get all tasks for a specific date"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, description, priority, type, category, "
            "estimated_duration_minutes, due_date, status FROM ai_daily_tasks "
            "WHERE user_id = ? AND task_date = ?",
            (user_id, date_str)
        )
        return [dict(zip(['id', 'title', 'description', 'priority', 'type', 'category',
                         'estimated_duration_minutes', 'due_date', 'status'], row))
                for row in cursor.fetchall()]

def get_user_habits(user_id):
    """Get all active habits for user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, frequency, scheduled_time, "
            "duration_minutes, is_active FROM habits WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )
        return [dict(zip(['id', 'name', 'description', 'frequency', 'scheduled_time',
                         'duration_minutes', 'is_active'], row))
                for row in cursor.fetchall()]

def get_user_focus_history(user_id, limit=20):
    """Get recent focus sessions"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, duration_minutes, focus_score, feedback FROM focus_sessions "
            "WHERE user_id = ? ORDER BY started_at DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(zip(['id', 'duration_minutes', 'focus_score', 'feedback'], row))
                for row in cursor.fetchall()]
```

### Step 6: Test the Integration

1. **Start Flask:**
```bash
python web/app.py
```

2. **Test API endpoints:**
```bash
# Get execution plan
curl http://localhost:5000/api/execution/today

# Get momentum status
curl http://localhost:5000/api/execution/momentum
```

3. **Visit home page:**
Navigate to `http://localhost:5000/` and you should see:
- Momentum status card with today's score
- Do now task card
- Current block card
- Top 3 priorities
- Time blocks schedule
- Start Focus and Rebuild Day buttons

---

## 🔗 Integration Points

### 1. Focus Mode Integration

When user clicks "Start Focus", connect to your existing focus mode:

**In EXECUTION_COACH_UI.html, modify `startFocusSession()`:**

```javascript
async function startFocusSession() {
    if (!currentPlan || !currentPlan.do_now_task) {
        window.location.href = '/focus';
        return;
    }
    
    // Save task to session
    sessionStorage.setItem('focusTaskId', currentPlan.do_now_task.id);
    sessionStorage.setItem('focusDuration', currentPlan.suggested_focus_duration);
    
    // Redirect to focus mode with task context
    window.location.href = '/focus';
}
```

### 2. Reminders Integration

Optional: Send reminders for upcoming blocks:

```python
# In app.py, add to your reminder job function:

def create_execution_block_reminders(user_id):
    """Create reminders for upcoming time blocks"""
    plan = get_execution_plan_for_today(user_id)  # Your function
    
    if not plan or not plan.get('time_blocks'):
        return
    
    for block in plan['time_blocks']:
        # Create reminder 15 minutes before block
        block_time = datetime.strptime(block['start_time'], '%H:%M')
        reminder_time = block_time - timedelta(minutes=15)
        
        # Add to reminders table
        # INSERT INTO reminders (user_id, content, trigger_at, ...) VALUES (...)
```

### 3. Reports Integration

Add execution insights to weekly report:

```python
# In your reports.py or report generation code:

def add_execution_metrics_to_report(user_id, start_date, end_date, report_dict):
    """Add execution coach data to weekly report"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get execution stats
        cursor.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed "
            "FROM ai_daily_tasks WHERE user_id = ? AND task_date BETWEEN ? AND ?",
            (user_id, start_date, end_date)
        )
        task_stats = cursor.fetchone()
        
        report_dict['execution'] = {
            'tasks_completed': task_stats[1] if task_stats else 0,
            'completion_rate': (task_stats[1] / task_stats[0]) if task_stats[0] > 0 else 0,
            'total_planned': task_stats[0] if task_stats else 0
        }
    
    return report_dict
```

### 4. Chat Integration

Support prompts like "What should I do now?" and "Rebuild my day":

```python
# In your chat handler, detect these prompts:

def handle_execution_coach_chat(user_message, user_id):
    """Handle execution coach related chat prompts"""
    
    lower_msg = user_message.lower()
    
    if any(phrase in lower_msg for phrase in ['what should i do', 'what do i do now', 'do now', 'next task']):
        # Get current plan and return do-now task
        plan = get_execution_plan_for_today(user_id)
        if plan and plan.get('do_now_task'):
            return f"Your next task: {plan['do_now_task']['title']}. Start with this while your energy is high!"
    
    elif any(phrase in lower_msg for phrase in ['rebuild', 'falling behind', 'behind', 'recovery']):
        # Trigger recovery mode
        recovery_plan = generate_recovery_plan(user_id)
        return f"Let's rebuild your day! Focus on: {recovery_plan['must_do_task']['title']}"
    
    elif any(phrase in lower_msg for phrase in ['momentum', 'how am i doing', 'on track']):
        # Get momentum status
        momentum = get_momentum_status(user_id)
        return f"You're {momentum['status']}. {momentum['summary']}"
    
    return None  # Let other handlers process
```

### 5. Dashboard Integration

If you have a main dashboard page, add an execution coach widget:

```html
<!-- In your main dashboard template -->

<div class="dashboard-widget">
    <h2>Execution Coach</h2>
    <div id="executionWidget" style="min-height: 200px;">
        Loading...
    </div>
</div>

<script>
async function loadExecutionWidget() {
    const res = await fetch('/api/execution/momentum');
    const momentum = await res.json();
    
    document.getElementById('executionWidget').innerHTML = `
        <h3>${momentum.status_emoji} ${momentum.status}</h3>
        <p>Score: ${momentum.momentum_score}/100</p>
        <p>${momentum.summary}</p>
    `;
}

loadExecutionWidget();
</script>
```

---

## 🧠 How Each Module Works

### execution_planner.py
**Purpose:** Generates realistic daily plans

**Key class:** `ExecutionPlanner`
```python
planner = ExecutionPlanner(user_profile, all_tasks, habits_today, focus_history, streak_data)
plan = planner.generate_plan(date)
# Returns: DailyExecutionPlan with priorities, time blocks, coaching message
```

**What it does:**
1. Scores tasks by urgency, fit, and importance
2. Selects top 3 priorities
3. Creates time blocks respecting work/free time
4. Suggests optimal focus duration
5. Estimates completion likelihood
6. Generates personalized coaching message

### execution_metrics.py
**Purpose:** Tracks momentum and execution status

**Key class:** `ExecutionMetrics`
```python
metrics = ExecutionMetrics(user_data)
momentum = metrics.compute_momentum_status(
    completed_today, missed_today, completed_habits,
    focus_sessions, streak_data, planned_tasks
)
# Returns: MomentumStatus (status, score, summary)
```

**Status categories:**
- **ON_TRACK** (momentum > 70): Keep momentum
- **AT_RISK** (40-70): Needs attention
- **RECOVERY_MODE** (< 40): Activate lighter plan

### execution_recovery.py
**Purpose:** Creates lighter rescue plans

**Key class:** `ExecutionRecovery`
```python
recovery = ExecutionRecovery(user_data)
plan = recovery.generate_recovery_plan(
    all_tasks, habits_today, missed_count,
    current_streak, momentum_score
)
# Returns: RecoveryPlan with 4 focused items
```

**4 components:**
1. **Must-do** (most critical, shortest)
2. **Easy win** (quick morale boost)
3. **Habit** (protect streak)
4. **Focus sprint** (15-minute intense focus)

### execution_personalizer.py
**Purpose:** Adapts plans to user's work style

**Key class:** `ExecutionPersonalizer`
```python
personalizer = ExecutionPersonalizer(user_data)
personalized = personalizer.adjust_plan_for_user(base_plan)
# Returns: Plan adjusted for chronotype, task style, messaging tone
```

**Personalization factors:**
- **Chronotype:** morning_person, night_owl, bimodal
- **Task style:** one_big_task, many_small_tasks, mixed
- **Message tone:** direct, supportive, motivational
- **Focus duration:** Based on history (15-60 min)

---

## 📊 Database Tables

### execution_plans
Stores daily plans
```sql
id, user_id, plan_date, top_priorities (JSON),
time_blocks (JSON), current_block_id, do_now_task,
suggested_focus_duration, coaching_message,
total_planned_minutes, estimated_completion_rate,
is_completed, actual_completion_rate, created_at, updated_at
```

### execution_blocks
Individual time blocks within a plan
```sql
id, plan_id, user_id, task_id, task_title, block_type (focus/work/habit/break/review),
start_time, end_time, duration_minutes, priority,
status (scheduled/active/completed/skipped),
completed_at, actual_duration_minutes, completion_notes, created_at
```

### execution_events
User interactions (for analytics)
```sql
id, user_id, event_type (plan_generated/block_started/block_completed/etc.),
plan_id, block_id, event_data (JSON), timestamp
```

### execution_preferences
User preferences for personalization
```sql
id, user_id, chronotype, work_time_preference, task_style,
preferred_focus_duration, preferred_message_tone,
enable_notifications, auto_suggest_recovery, created_at, updated_at
```

### execution_reflections
Daily reflections and feedback
```sql
id, user_id, plan_date, went_well, challenges, improvements,
energy_level (1-5), focus_quality (1-5),
tasks_completed, tasks_missed, habits_completed, focus_sessions, created_at
```

### execution_recovery_plans
Saved recovery plans
```sql
id, user_id, plan_date, must_do_task (JSON), easy_win_task (JSON),
streak_protecting_habit (JSON), focus_sprint (JSON),
recovery_message, estimated_recovery_time,
created_at, activated_at, completed_at, is_successful
```

---

## 🔧 Configuration Options

### Per User in execution_preferences Table

```python
# Set user preferences
preferences = {
    'chronotype': 'morning_person',  # morning_person, night_owl, bimodal, standard
    'task_style': 'mixed',            # one_big_task, many_small_tasks, mixed
    'preferred_focus_duration': 45,   # minutes (15-60)
    'preferred_message_tone': 'motivational',  # direct, supportive, motivational
    'enable_notifications': True,
    'auto_suggest_recovery': True,
    'recovery_mode_threshold': 40      # momentum score to trigger recovery
}
```

### In execution_planner.py

Adjust scoring weights:
```python
# In _score_task_priority():
score = (urgency * 40) + (duration_fit * 30) + (importance * 20) + (history * 10)

# Adjust thresholds in _estimate_completion_rate():
if required_time <= available_time:
    completion_rate = 0.9
elif required_time <= available_time * 1.3:
    completion_rate = 0.7
```

### In execution_metrics.py

Adjust momentum weights:
```python
momentum_score = (
    (task_completion * 0.40) +      # 40% weight
    (habit_completion * 0.20) +     # 20% weight
    (focus_score * 0.20) +          # 20% weight
    (streak_score * 0.20)           # 20% weight
)
```

Adjust status thresholds:
```python
if momentum_score < 40:
    status = RECOVERY_MODE
elif momentum_score < 70:
    status = AT_RISK
else:
    status = ON_TRACK
```

---

## 🧪 Testing

### Test Data Creation

```python
# Add test user with sample tasks
user_id = 1

# Create sample tasks
for i in range(5):
    create_ai_task(
        user_id=user_id,
        title=f"Sample Task {i}",
        description="Test task",
        priority='high' if i < 2 else 'medium',
        estimated_duration=30 + (i * 10),
        due_date=datetime.now().strftime('%Y-%m-%d')
    )

# Test API endpoint
curl http://localhost:5000/api/execution/today \
    -H "Cookie: session=YOUR_SESSION_ID"
```

### Manual Testing Checklist

- [ ] `GET /api/execution/today` returns complete plan with 3 priorities
- [ ] `GET /api/execution/momentum` returns status with score 0-100
- [ ] `POST /api/execution/rebuild-day` creates recovery plan with 4 items
- [ ] UI loads execution plan and displays priorities
- [ ] "Start Focus" button integrates with focus mode
- [ ] "Rebuild Day" button activates recovery mode
- [ ] Time blocks display correctly with colors
- [ ] Momentum score bar updates visually
- [ ] Coaching message appears and personalizes

### Debug Output

Enable debug logging in execution modules:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add to each module
logger.debug(f"Generating plan for user {user_id}")
logger.info(f"Top priority: {priorities[0]}")
```

---

## 📈 Expected Behavior

### Daily Flow

1. **Morning (7-9am)**: User sees execution plan with top 3 priorities
2. **During day**: Plan updates with completed tasks, momentum status changes
3. **Afternoon (3pm)**: If falling behind, "Rebuild Day" button appears
4. **Evening**: User can save reflection on how day went
5. **Next day**: New plan generated with insights from previous day

### Recovery Mode Activation

Triggered when:
- Momentum score drops below 40
- 2+ high-priority tasks missed
- User clicks "Rebuild Day" button

Response:
- Generate lighter plan (4 items instead of many)
- Focus on 1 must-do + protecting streak
- Empathetic, action-oriented coaching message
- 15-minute focus sprint to restart momentum

### Progress Tracking

System tracks:
- Plans generated and their accuracy
- Completion rates over time
- Energy patterns (when user does best work)
- Recovery success (did light plan work?)
- Streak maintenance/growth

---

## 🚀 Advanced Features (Future Enhancements)

### ML-Based Optimization (v2)
- Train model on user's completion patterns
- Predict realistic task durations
- Recommend optimal task order
- A/B test different time blocks for same user

### Smart Reminders
- Nudge before block starts (15 min warning)
- Suggest stretch break after 90 min focus
- Congratulate on completed block
- Auto-pause if user on break

### Calendar Integration
- Sync with Google Calendar / Outlook
- Show meeting blocks in execution plan
- Suggest execution blocks around meetings
- Add focus blocks to calendar

### Mobile App Support
- Mobile-optimized execution view
- Push notifications for block reminders
- Quick capture of new tasks
- One-tap "Start Focus" from notification

### Team Features
- Shared execution plans for team projects
- Accountability check-ins
- Team momentum dashboard
- Collaborative recovery planning

---

## ❓ Troubleshooting

### Issue: API returns 401 Unauthorized
**Solution:** User not authenticated. Check session cookie and `get_user()` function.

### Issue: Import errors for execution modules
**Solution:** Ensure all 4 modules are in project root, not in subdirectories.

### Issue: Database migration fails
**Solution:** Run `init_db()` first from memory.py before running migration.

### Issue: Execution plan shows no tasks
**Solution:** Check that `ai_daily_tasks` table has data for the user.

### Issue: UI doesn't load from home.html
**Solution:** 
- Check CSS classes exist in your base.html
- Verify dark theme colors match your `--color-*` variables
- Check browser console for JS errors

### Issue: Recovery mode not triggering
**Solution:** 
- Check momentum calculation in `execution_metrics.py`
- Verify missed_tasks are marked with status='missed'
- Check recovery_mode_threshold in user's preferences

---

## 📞 Support & Customization

### Customize Coaching Messages

Edit messages in `execution_planner.py`:
```python
def _generate_coaching_message(self, plan):
    # Modify messages here
    message = f"🚀 Custom message for your style!"
    return message
```

### Customize Time Block Colors

Edit in `EXECUTION_COACH_UI.html`:
```javascript
if (block.block_type === 'focus') {
    borderColor = '#ef4444';  // Change this color
}
```

### Customize Recovery Plan Logic

Edit in `execution_recovery.py`:
```python
def _select_must_do_task(self, all_tasks, missed_count):
    # Modify selection criteria here
```

### Add Custom Metrics

Extend `execution_metrics.py`:
```python
def _calculate_custom_score(self, user_data):
    # Add your custom calculation
    return score
```

---

## ✅ Integration Checklist

- [ ] Database migration completed (6 tables created)
- [ ] Imports added to web/app.py
- [ ] All 7 API routes added to web/app.py
- [ ] UI component added to home.html or execution.html
- [ ] Helper functions added to memory.py
- [ ] Focus mode integration tested
- [ ] Reminders integration planned (optional)
- [ ] Reports integration planned (optional)
- [ ] Chat integration planned (optional)
- [ ] All API endpoints tested with curl
- [ ] UI loads correctly in browser
- [ ] Momentum status computes correctly
- [ ] Recovery mode triggers appropriately
- [ ] Personalization working for your user

---

## 🎉 You're Ready!

Your Execution Coach system is now fully integrated. Users will experience:

✅ **Daily planning** that's realistic and personalized  
✅ **Real-time momentum tracking** showing their status  
✅ **Smart recovery** when they fall behind  
✅ **Adaptive coaching** that matches their work style  
✅ **Integration** with existing focus mode, habits, and tasks  

Start Flask and visit the home dashboard to see it in action!

```bash
python web/app.py
# Visit http://localhost:5000/
```

**Questions or issues?** Check the troubleshooting section or examine the detailed module docstrings.

Happy executing! 🚀
