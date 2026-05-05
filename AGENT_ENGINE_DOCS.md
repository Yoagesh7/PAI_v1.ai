# Autonomous AI Agent Engine - Complete Documentation

## 📋 Overview

The **Autonomous Agent Engine** transforms PartnerAI from a **reactive system** (user asks → AI responds) to a **proactive system** (AI observes → decides → acts automatically).

The system monitors user behavior every 30 minutes and makes intelligent decisions to keep users engaged and productive, without requiring manual intervention.

---

## 🏗️ Architecture

### Core Pipeline

```
1. DATA COLLECTION LAYER
   ↓
   collect_user_data(user_id)
   └─ Gathers: tasks, habits, focus sessions, inactivity, productivity score
   
2. DECISION ENGINE (Rule-Based v1)
   ↓
   make_decision(user_data)
   └─ Applies rules → Returns action with priority & reason
   
3. ACTION ENGINE
   ↓
   execute_action(user_id, decision)
   └─ Reschedule tasks, send nudges, suggest focus, reduce load, encourage habits
   
4. LOGGING SYSTEM
   ↓
   log_action(user_id, action, reason, priority, success, error)
   └─ Stores all decisions in agent_actions_log table
```

---

## 📊 1. Data Collection Layer

### Function: `collect_user_data(user_id: int) → Dict`

Collects comprehensive user data for analysis.

#### Returns:
```python
{
    'user_id': int,
    'name': str,
    'email': str,
    'last_active': datetime,
    'active_today': bool,
    'missed_tasks': int,              # Incomplete tasks today
    'incomplete_tasks': int,
    'completed_tasks_today': int,
    'total_tasks_today': int,
    'completion_rate': float,         # 0-100%
    'focus_sessions_today': int,
    'habit_completion_rate': float,   # 0-100%
    'current_streak': int,
    'last_action_time': str,
    'inactivity_hours': float,
    'productivity_score': float       # Weighted score
}
```

#### Data Sources:
- **ai_daily_tasks**: Tasks for today (pending/completed)
- **focus_sessions**: Focused work periods
- **habits**: User habit tracking
- **users**: Last active timestamp, streak count

---

## 🧠 2. Decision Engine (Rule-Based v1)

### Function: `make_decision(user_data: Dict) → Optional[Dict]`

Applies rule-based logic to determine the best action.

#### Decision Rules (Priority Order):

| Rule | Condition | Action | Priority |
|------|-----------|--------|----------|
| **Rule 1** | `missed_tasks >= 2` | `reschedule_tasks` | HIGH |
| **Rule 2** | `inactivity_hours > 24` | `send_inactivity_nudge` | MEDIUM/HIGH |
| **Rule 3** | `total_tasks > 0 AND focus_sessions == 0` | `suggest_focus` | MEDIUM |
| **Rule 4** | `completion_rate < 40%` | `reduce_task_load` | MEDIUM |
| **Rule 5** | `habit_completion < 30% AND streak > 0` | `encourage_habits` | LOW |

#### Returns:
```python
{
    'action': str,              # e.g., 'reschedule_tasks'
    'reason': str,              # Explanation of the decision
    'priority': str,            # 'low', 'medium', 'high'
    'details': dict,            # Action-specific details
    'timestamp': str            # ISO format timestamp
}
```

---

## ⚡ 3. Action Engine

### Function: `execute_action(user_id: int, decision: Dict) → bool`

Executes the decided action automatically.

### Action Types:

#### A. `reschedule_tasks`
- **When**: User has 2+ incomplete tasks
- **What**: Moves incomplete tasks to next day
- **Message**: "📅 I've rescheduled your N incomplete tasks to tomorrow..."
- **Database**: Updates `ai_daily_tasks.task_date`

#### B. `send_inactivity_nudge`
- **When**: User inactive for >24 hours
- **What**: Sends chat message + optional email
- **Message**: "👋 I noticed you've been away for N hours..."
- **Triggers**: Automatic email if inactive >48 hours

#### C. `suggest_focus`
- **When**: User has tasks but no focus sessions today
- **What**: Suggests activating Focus Mode
- **Message**: "🎯 You have N task(s) ready. Want to activate Focus Mode?"

#### D. `reduce_task_load`
- **When**: User completion rate < 40%
- **What**: Limits active tasks to top 3 by priority
- **Message**: "📌 I've focused your list to 3 most important tasks..."
- **Status**: Marks others as 'postponed'

#### E. `encourage_habits`
- **When**: User's streak is at risk (habit completion <30%)
- **What**: Sends motivation message
- **Message**: "🔥 You're on N-day streak! Don't break it now..."

---

## 📝 4. Logging System

### Database Table: `agent_actions_log`

```sql
CREATE TABLE agent_actions_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,              -- e.g., 'reschedule_tasks'
    reason TEXT,                        -- Explanation
    priority TEXT,                      -- 'low', 'medium', 'high'
    decision_data TEXT,                 -- JSON with details
    success INTEGER DEFAULT 0,          -- 1 = success, 0 = failure
    error_message TEXT,                 -- If failed
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

### Function: `log_action(user_id, action, reason, priority, decision_data, success, error_msg)`

Every decision and action execution is logged for:
- Auditing
- Analytics
- Learning what works best
- Debugging issues

---

## 🚫 5. Cooldown System

### Function: `check_action_cooldown(user_id: int, action: str) → bool`

Prevents action spam by enforcing a **6-hour cooldown** between identical actions.

```python
# Example: Don't reschedule tasks twice in 6 hours
if check_action_cooldown(user_id, 'reschedule_tasks'):
    execute_action(user_id, decision)  # OK to proceed
else:
    log_action(..., success=False, error='Action on cooldown')
```

---

## 🔄 6. Integration with Scheduler

### File: `ai_task_scheduler.py`

The agent runs **every 30 minutes** via APScheduler:

```python
scheduler.add_job(
    run_autonomous_agent_job,
    IntervalTrigger(minutes=30),
    id='autonomous_agent',
    name='Autonomous AI Agent'
)
```

### Function: `run_autonomous_agent_for_all_users() → Dict[int, bool]`

Called periodically:
1. Fetches all active users
2. For each user:
   - Collects data
   - Makes decision
   - Checks cooldown
   - Executes action
   - Logs result
3. Returns results for monitoring

---

## 💬 7. Chat Integration

When the agent takes an action, it inserts a message into `chat_history`:

```python
save_chat_message(user_id, 'ai', "📅 I've rescheduled...")
```

The message appears in the chat as if the AI spoke directly to the user, making the system feel like a real mentor.

---

## 🚀 8. Setup & Usage

### 1. Database Migration

```bash
python migrate_agent_engine.py
```

Creates the `agent_actions_log` table.

### 2. Enable in Flask App

The agent is automatically initialized when the scheduler starts:

```python
from ai_task_scheduler import init_scheduler
scheduler = init_scheduler(app)
```

### 3. Test the System

```bash
python tests/test_agent_engine.py
```

### 4. Monitor Actions

Query the log table:

```sql
SELECT * FROM agent_actions_log 
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;
```

---

## 📈 9. Future Enhancements

### v2: Machine Learning Decision Engine
- Replace rules with trained model
- Learn from user feedback
- Adapt thresholds based on user behavior

### v3: Collaborative Agent
- Detect team struggles
- Suggest group interventions
- Track team productivity

### v4: Advanced Analytics
- Pattern recognition
- Predictive interventions
- Custom rules per user

---

## 🐛 10. Troubleshooting

### Agent not triggering?
1. Check scheduler is running: `ps aux | grep python`
2. Check `partnerai.log` for errors
3. Verify APScheduler job: `print(scheduler.get_jobs())`

### Actions not working?
1. Check `agent_actions_log` for errors
2. Verify user has data to collect
3. Check cooldown hasn't triggered

### Messages not appearing?
1. Check `chat_history` table for new entries
2. Verify `save_chat_message()` is called
3. Restart chat page to reload history

---

## 📚 11. Key Files

```
PartnerAI/
├── agent_engine.py              # Main agent logic
├── migrate_agent_engine.py       # Database setup
├── ai_task_scheduler.py          # Scheduler integration
├── tests/test_agent_engine.py    # Test suite
└── web/app.py                    # Flask app (scheduler init)
```

---

## 🎯 12. Success Metrics

Track agent effectiveness:

```sql
-- Actions per user per week
SELECT COUNT(*) as actions, user_id 
FROM agent_actions_log 
WHERE timestamp > datetime('now', '-7 days') AND success = 1
GROUP BY user_id;

-- Most effective actions
SELECT action, COUNT(*) as count, 
    ROUND(100.0 * SUM(success) / COUNT(*), 1) as success_rate
FROM agent_actions_log
GROUP BY action
ORDER BY success_rate DESC;

-- Average action latency
SELECT AVG((julianday(timestamp) - julianday('now')) * 24) as hours_ago
FROM agent_actions_log
WHERE success = 1;
```

---

## 💡 Example Workflow

**User: John (1000 tasks, 0% completion)**

**Cycle 1 (8:00 AM)**
- ✅ Collect data: 5 missed tasks, 0% completion
- ✅ Decide: `reschedule_tasks` (HIGH)
- ✅ Execute: Move 5 tasks to tomorrow
- ✅ Chat: "📅 I've rescheduled your 5 incomplete tasks..."
- ✅ Log: Action successful

**Cycle 2 (9:00 AM)**
- ✅ Collect data: 0 missed tasks, 0 completed (it's early)
- ✅ Decide: No action needed (cooldown on reschedule)
- ✅ Log: No action

**Cycle 3 (12:00 PM)**
- ✅ Collect data: 3 incomplete tasks, still 0 completed
- ✅ Decide: `suggest_focus` (MEDIUM)
- ✅ Execute: Chat message suggesting focus mode
- ✅ Chat: "🎯 You have 3 task(s) ready. Want to activate Focus Mode?"

**Result**: John feels supported and guided, even without asking!

---

## 📞 Support

For issues or questions about the agent engine:
1. Check logs in `agent_engine.log`
2. Run test suite: `python tests/test_agent_engine.py`
3. Review decision rules in `make_decision()`
4. Check action logic in action execution functions

---

**Built with ❤️ for Proactive Productivity**
