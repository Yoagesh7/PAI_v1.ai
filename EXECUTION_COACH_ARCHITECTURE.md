# Execution Coach - Architecture Overview

## 🎯 System Design

The Execution Coach is a **modular, deterministic planning system** that helps users execute their day with intelligence and recover when falling behind.

### Core Philosophy

1. **Realism First**: Plans are based on user's actual time, energy, and history—not wishful thinking
2. **Personalization**: Adapts to chronotype, task style, and communication preference
3. **Graceful Degradation**: System guides without overwhelming (3 priorities, not 10)
4. **Recovery-First**: When falling behind, pivot to a lighter plan rather than pushing harder
5. **Integration**: Works seamlessly with existing focus mode, habits, tasks, and chat

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB BROWSER (Vanilla JS)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  EXECUTION COACH UI (home.html / execution.html)         │  │
│  │  - Momentum status card                                  │  │
│  │  - Do now task & current block                           │  │
│  │  - Top 3 priorities                                      │  │
│  │  - Time blocks schedule                                  │  │
│  │  - Start Focus / Rebuild Day buttons                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FLASK BACKEND (app.py)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API ROUTES (7 endpoints)                                │  │
│  │  GET  /api/execution/today          → GetPlan            │  │
│  │  GET  /api/execution/momentum       → GetStatus          │  │
│  │  POST /api/execution/rebuild-day    → RecoveryMode       │  │
│  │  POST /api/execution/start-block    → BlockStarted       │  │
│  │  POST /api/execution/complete-block → BlockCompleted     │  │
│  │  GET/POST /api/execution/preferences → UserPrefs        │  │
│  │  POST /api/execution/reflection    → SaveReflection      │  │
│  │  GET  /api/execution/summary       → WeeklySummary       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION COACH MODULES                       │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ ExecutionPlanner │  │ ExecutionMetrics │                     │
│  │                  │  │                  │                     │
│  │ ▪ Score tasks    │  │ ▪ Compute score  │                     │
│  │ ▪ Prioritize     │  │ ▪ Determine      │                     │
│  │ ▪ Build blocks   │  │   status         │                     │
│  │ ▪ Estimate       │  │ ▪ Track momentum │                     │
│  │   completion     │  │ ▪ Identify       │                     │
│  │                  │  │   blockers       │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ ExecutionRecovery│  │ ExecutionPersonal│                     │
│  │                  │  │      izer        │                     │
│  │ ▪ Generate 4-item│  │                  │                     │
│  │   rescue plan    │  │ ▪ Adjust for     │                     │
│  │ ▪ Must-do task   │  │   chronotype     │                     │
│  │ ▪ Easy win       │  │ ▪ Adjust for     │                     │
│  │ ▪ Habit protect  │  │   task style     │                     │
│  │ ▪ Focus sprint   │  │ ▪ Personalize    │                     │
│  │                  │  │   messages       │                     │
│  │ ▪ Empathetic msg │  │ ▪ Adjust focus   │                     │
│  │                  │  │   duration       │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SQLITE DATABASE                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ execution_plans, execution_blocks, execution_events       │  │
│  │ execution_preferences, execution_reflections              │  │
│  │ execution_recovery_plans                                  │  │
│  │                                                            │  │
│  │ + existing: users, ai_daily_tasks, habits, focus_sessions│  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Data Flow

### 1. DAILY PLAN GENERATION (`GET /api/execution/today`)

```
User loads home page
        ↓
GET /api/execution/today
        ↓
ExecutionPlanner.generate_plan()
    ├─ Input: User profile, tasks, habits, focus history, streak
    ├─ Step 1: Score each task (urgency + duration_fit + importance + history)
    ├─ Step 2: Select top 3 by score
    ├─ Step 3: Build time blocks (morning focus, afternoon, evening, breaks)
    ├─ Step 4: Determine current block (which block is user in now?)
    ├─ Step 5: Set do-now task (first priority right now)
    ├─ Step 6: Suggest focus duration (based on history)
    ├─ Step 7: Estimate completion rate
    └─ Step 8: Generate coaching message
        ↓
ExecutionPersonalizer.adjust_plan_for_user()
    ├─ Reorder blocks for chronotype
    ├─ Filter priorities for task style
    └─ Personalize message tone
        ↓
Return to UI
        ↓
UI renders plan (priorities, blocks, coaching, do-now)
```

### 2. MOMENTUM STATUS TRACKING (`GET /api/execution/momentum`)

```
User views home page during day
        ↓
GET /api/execution/momentum
        ↓
ExecutionMetrics.compute_momentum_status()
    ├─ Input: Completed tasks, missed tasks, habits, focus sessions, streak
    ├─ Calculate 4 component scores:
    │  ├─ Task completion score (40% weight)
    │  ├─ Habit completion score (20% weight)
    │  ├─ Focus score (20% weight)
    │  └─ Streak score (20% weight)
    ├─ Combine: momentum_score = weighted average (0-100)
    ├─ Determine status:
    │  ├─ ON_TRACK if score > 70
    │  ├─ AT_RISK if 40-70
    │  └─ RECOVERY_MODE if < 40
    └─ Generate status message
        ↓
Return MomentumStatus to UI
        ↓
UI shows:
    ├─ Score with progress bar
    ├─ Status emoji and summary
    ├─ Metrics (tasks done, focus count, streak)
    └─ If recovery_needed: Show "Rebuild Day" button
```

### 3. RECOVERY MODE (`POST /api/execution/rebuild-day`)

```
User clicks "Rebuild Day" button (or momentum < 40 auto-triggers)
        ↓
POST /api/execution/rebuild-day
        ↓
ExecutionRecovery.generate_recovery_plan()
    ├─ Input: Incomplete tasks, habits, missed count, streak, momentum
    ├─ Select 4 items (not 10+):
    │  ├─ 1. Must-do: Most critical, shortest task
    │  ├─ 2. Easy win: Quick task for morale (< 20 min)
    │  ├─ 3. Streak habit: Protect ongoing habit streak
    │  └─ 4. Focus sprint: 15-minute intense focus block
    ├─ Calculate total recovery time
    ├─ Assess recovery feasibility
    └─ Generate empathetic message
        ↓
Save recovery plan to database
        ↓
Return to UI (or show in modal)
        ↓
UI shows recovery plan with:
    ├─ The 4 items clearly laid out
    ├─ Total time needed (e.g., "47 minutes total")
    ├─ Next checkpoint (when to check progress)
    └─ Compassionate message
```

### 4. PERSONALIZATION

**Chronotype Adjustment:**
- Morning person: Reorder blocks to put hard tasks 7am-11am
- Night owl: Move hard tasks to 4pm-8pm
- Bimodal: Create peaks at morning AND evening
- Standard: Keep as is

**Task Style Adjustment:**
- One big task person: Keep 1 priority, remove extras
- Many small tasks person: Add more small items, break down larger ones
- Mixed: Keep 2-3 balanced priorities

**Message Tone:**
- Direct: "Your priority is X. Duration: 30 min."
- Supportive: "You've got this! Focus on X while fresh."
- Motivational: "🚀 This is your moment! Tackle X!"

---

## 🔄 State Management

### User State in Execution Coach

```python
# Captured in execution_preferences table
{
    'chronotype': 'morning_person',      # How they're wired
    'task_style': 'mixed',                # How they prefer work
    'preferred_focus_duration': 45,       # Their Pomodoro length
    'preferred_message_tone': 'supportive',  # How they like to be talked to
    'enable_notifications': True,         # Do they want reminders?
    'auto_suggest_recovery': True,        # Auto-activate recovery mode?
    'recovery_mode_threshold': 40         # At what momentum score?
}
```

### Today's Execution State

```python
# In execution_plans table
{
    'user_id': 123,
    'plan_date': '2026-05-05',
    'top_priorities': [task1, task2, task3],
    'time_blocks': [block1, block2, ..., review_block],
    'current_block': block3,           # Where they are now
    'do_now_task': task1,              # What to do right now
    'is_completed': 0,                 # Did they complete the plan?
    'actual_completion_rate': None,    # How many of the priorities?
}
```

### Tracking User Actions

```python
# In execution_events table
{
    'event_type': 'plan_generated',
    'timestamp': '2026-05-05T09:00:00',
    'event_data': {...}
}

Events:
- plan_generated: Daily plan created
- block_started: User clicked to start a block
- block_completed: User finished a block
- recovery_initiated: Recovery mode activated
- recovery_completed: User completed recovery plan
- reflection_saved: End-of-day reflection submitted
```

---

## 🎨 UI/UX Design

### Information Hierarchy

**Primary (Top of page):**
- Momentum status card (is user on track?)
- Do now task (what to do RIGHT NOW?)

**Secondary:**
- Top 3 priorities (what matters today?)
- Time blocks schedule (when to do what?)

**Tertiary:**
- Coach message (personalized insight)
- Buttons (start focus, rebuild day)

### Color Coding

- **On Track**: Green/teal, ✅ emoji, "You've got this"
- **At Risk**: Yellow/orange, ⚠️ emoji, "Refocus to catch up"
- **Recovery**: Red, 🆘 emoji, "Let's rebuild together"

### Interaction Patterns

1. **Start Focus**: Click button → Opens focus mode with current task
2. **Rebuild Day**: Click button → Shows lighter 4-item plan
3. **View Details**: Click priority → Shows description (optional)
4. **See Schedule**: Scroll to see all time blocks
5. **End of day**: Save reflection on how it went

---

## 📊 Metrics Calculated

### Momentum Score (0-100)

```
Final = (task_completion * 40%) + 
        (habit_completion * 20%) +
        (focus_sessions * 20%) +
        (streak_status * 20%)

Example:
- Completed 3/4 tasks = 75/100 task score
- Completed 2 habits = 80/100 habit score
- Had 1 focus session = 50/100 focus score
- 7-day streak active = 85/100 streak score

Momentum = (75 * 0.4) + (80 * 0.2) + (50 * 0.2) + (85 * 0.2)
         = 30 + 16 + 10 + 17 = 73/100 ✅ ON TRACK
```

### Task Priority Score

```
Priority Score = (urgency * 40) + 
                 (duration_fit * 30) +
                 (importance * 20) +
                 (completion_history * 10)

Urgency (40 pts max):
- Overdue: 40
- Due today: 35
- Due tomorrow: 30
- etc.

Duration Fit (30 pts max):
- Fits in available time: 30
- Slightly over: 15
- Way over: 0

Importance (20 pts max):
- Goal-related: 15
- Project: 12
- Learning: 8
+ Priority bonus: 0-5

History (10 pts max):
- User's completion rate in this category: 0-10
```

### Completion Rate Estimation

```
Feasibility = (available_time / required_time) * 60% +
              user_historical_rate * 40%

Example:
- 4 hours available, 4.5 hours needed = 89% feasible
- User completes 60% of tasks historically = 60% 
- Estimated completion = (89 * 0.6) + (60 * 0.4) = 77%

If < 50%: Activate recovery mode
If 50-70%: Stay focused, cut slack items
If > 70%: On track, keep momentum
```

---

## 🔌 Integration Points

### With Focus Mode
- Pass task_id to focus session
- Track focus duration toward daily goals
- Auto-start focus from "Start Focus" button

### With Habits
- Daily habits included in execution plan
- Habit completion tracked in momentum score
- Streak protection in recovery mode

### With Tasks (ai_daily_tasks)
- Tasks pulled from ai_daily_tasks table
- Completed tasks marked and tracked
- Due dates determine urgency

### With Chat
- Support natural language queries ("What should I do now?")
- Recovery mode suggestions in chat
- Momentum status on demand

### With Reports (Weekly)
- Execution completion metrics
- Average momentum score
- Focus session statistics
- Task completion rate

---

## 🔐 Data Privacy & Safety

### What's Stored
- Plans generated (not sensitive)
- Completion events (timestamped)
- User preferences (non-sensitive)
- Reflections (user-owned)

### What's NOT Stored
- Task content itself (only IDs and metadata)
- Personal notes (those stay in tasks table)
- Messages (those stay in chat table)

### Data Retention
- Keep daily plans for 30 days
- Keep execution events for 90 days
- Keep recovery plans for 30 days
- Delete old records via cleanup job

---

## 🚀 Performance Considerations

### Optimization

**Query Optimization:**
- Index on (user_id, plan_date) for fast lookups
- Index on (user_id, status) for event queries
- Denormalize counts in users table if needed

**Caching:**
- Cache daily plan for 30 minutes
- Cache momentum score for 5 minutes
- Invalidate on task completion

**Async Loading:**
- Load momentum in background
- Render UI first, load data second
- Use fetch() with error fallback

### Expected Load

```
Per user per day:
- 1 plan generation: ~100ms (DB queries + calculations)
- 5 momentum checks: ~50ms each = 250ms
- Recovery plan: ~150ms
- Total: ~500ms per user

For 1000 users:
- ~500 seconds = ~8 minutes (spread over day)
- No blocking, all async

Reasonable for most servers
```

---

## 🧬 Algorithm Logic

### Task Scoring Algorithm

```
for task in all_incomplete_tasks:
    score = 0
    
    # Factor 1: Urgency (0-40)
    days_until_due = (due_date - today).days
    if days_until_due < 0: score += 40
    elif days_until_due == 0: score += 35
    elif days_until_due == 1: score += 30
    elif days_until_due <= 3: score += 20
    elif days_until_due <= 7: score += 10
    else: score += 2
    
    # Factor 2: Fit (0-30)
    if duration <= available_time:
        score += 30
    elif duration <= available_time + 30:
        score += 15
    
    # Factor 3: Importance (0-20)
    if type == 'goal_related': score += 15
    if priority == 'high': score += 5
    
    # Factor 4: History (0-10)
    completion_rate = historical_completion_for_category
    score += completion_rate * 10
    
    return min(score, 100)

Sort by score descending
Take top 3
```

### Status Determination Algorithm

```
if momentum_score < 40 OR (missed_tasks >= 2 AND streak_at_risk):
    status = RECOVERY_MODE
elif momentum_score < 70 OR streak_at_risk OR missed_tasks > 0:
    status = AT_RISK
else:
    status = ON_TRACK
```

### Recovery Plan Selection

```
must_do = select_highest_priority_incomplete_task(
    filter_by=[priority=high, due=today, duration=shortest]
)

easy_win = select_shortest_incomplete_task(
    filter_by=[duration < 20min, exclude=must_do]
)

habit = select_streak_protecting_habit(
    if_streak_active=[pick_main_habit],
    if_no_streak=[pick_any_habit]
)

focus_sprint = TimeBlock(duration=15, task=must_do, intensity='high')
```

---

## 🎓 Learning & Improvement

### Data Collection for ML (Future)

```python
# What we track for future ML:
- user_id
- task_characteristics (duration_estimate, actual, category, priority)
- user_state (energy_level, focus_quality, mood)
- completion_outcome (completed, missed, partial)
- time_of_day_completed
- environmental_factors (from user reflection)

# Use for:
- Duration estimation accuracy
- Optimal task ordering
- Best time for different types of work
- Predict burnout risk
- Personalize recommendations
```

### Continuous Improvement

```python
# After each day, system learns:
1. Was the plan realistic? (completion_rate vs estimated_rate)
2. Which tasks got done? (improve scoring)
3. When was focus best? (optimize time blocks)
4. Did recovery mode work? (refine light plan logic)
5. What blocked the user? (improve blockers list)
```

---

## 📖 Summary

The Execution Coach transforms PartnerAI from a **reactive task manager** into a **proactive execution assistant** that:

1. **Plans realistically** based on time, energy, and history
2. **Guides intelligently** with top 3 priorities and time blocks
3. **Tracks momentum** in real-time (On Track / At Risk / Recovery)
4. **Recovers gracefully** with lighter plans when falling behind
5. **Personalizes** to chronotype, task style, and communication
6. **Integrates seamlessly** with focus mode, habits, and chat

Users experience a **mentor that knows their rhythms** and **helps them execute** rather than just tracking what they didn't do.

---

**Built with focus on:** Simplicity, Personalization, and Real Results 🚀
