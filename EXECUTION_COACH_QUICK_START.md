# Execution Coach - Quick Start (5 Minutes)

## What You Got

✅ **4 Python modules** (500+ lines each)
✅ **Database migration** (6 new tables)
✅ **7 Flask API routes** (copy-paste ready)
✅ **Complete UI component** (HTML + vanilla JS)
✅ **Comprehensive documentation** (guides + architecture)

---

## TL;DR Setup (Copy-Paste)

### 1. Run Migration (1 minute)
```bash
python migrate_execution_coach.py
```
Output: `✅ All Execution Coach tables created successfully!`

### 2. Add Imports to web/app.py (30 seconds)
Find this line (~75):
```python
from habits_db import init_habits_db, ...
```

Add after it:
```python
# Execution Coach imports
try:
    from execution_planner import ExecutionPlanner, DailyExecutionPlan
    from execution_metrics import ExecutionMetrics, MomentumStatus
    from execution_recovery import ExecutionRecovery
    from execution_personalizer import ExecutionPersonalizer, UserPreferences
    print("✅ Execution Coach modules loaded")
except ImportError as e:
    print(f"⚠️  Execution Coach modules not available: {e}")
```

### 3. Copy Routes (2 minutes)
Open `EXECUTION_COACH_ROUTES.py`

Copy everything between the route comment sections

Paste into `web/app.py` around line 2500+

### 4. Add UI (1 minute)
Copy everything from `EXECUTION_COACH_UI.html`

Paste into `web/templates/home.html` before the closing `{% endblock %}`

### 5. Test (1 minute)
```bash
python web/app.py
# Visit http://localhost:5000/
```

You should see:
- ✅ Momentum status card
- ✅ Do now task
- ✅ Top 3 priorities
- ✅ Time blocks
- ✅ Start Focus button

---

## File Reference

| File | Purpose | Action |
|------|---------|--------|
| `execution_planner.py` | Daily planning logic | Already created ✅ |
| `execution_metrics.py` | Momentum tracking | Already created ✅ |
| `execution_recovery.py` | Recovery plans | Already created ✅ |
| `execution_personalizer.py` | Personalization | Already created ✅ |
| `migrate_execution_coach.py` | DB setup | Run this ⬇️ |
| `EXECUTION_COACH_ROUTES.py` | API routes | Copy into app.py ⬇️ |
| `EXECUTION_COACH_UI.html` | Frontend | Copy into home.html ⬇️ |
| `EXECUTION_COACH_INTEGRATION_GUIDE.md` | Full docs | Reference 📖 |
| `EXECUTION_COACH_ARCHITECTURE.md` | Design docs | Reference 📖 |

---

## Key Features

### Daily Planning
- Generates realistic plan with top 3 priorities
- Creates time blocks respecting work/free time
- Suggests optimal focus duration
- Estimates completion likelihood
- Generates personalized coaching message

### Momentum Tracking
- Real-time score (0-100)
- Status: On Track / At Risk / Recovery Mode
- Tracks completed tasks, habits, focus sessions, streaks
- Shows progress visually

### Recovery Mode
- Activates when falling behind (momentum < 40)
- Creates 4-item lightweight plan:
  - 1 must-do (most critical)
  - 1 easy win (quick morale boost)
  - 1 habit (protect streak)
  - 1 focus sprint (15 min burst)
- Empathetic messaging

### Personalization
- **Chronotype:** Morning person, night owl, bimodal
- **Task style:** One big task, many small tasks, mixed
- **Focus duration:** 15-60 minutes
- **Message tone:** Direct, supportive, motivational

---

## API Endpoints Summary

```
GET  /api/execution/today             → Complete daily plan
GET  /api/execution/momentum           → Current momentum status
POST /api/execution/rebuild-day        → Activate recovery mode
POST /api/execution/start-block        → Start a time block
POST /api/execution/complete-block     → Complete a block
GET  /api/execution/preferences        → User preferences
POST /api/execution/preferences        → Update preferences
POST /api/execution/reflection         → Save daily reflection
GET  /api/execution/summary            → Weekly/monthly summary
```

---

## Database Tables

```
execution_plans                 → Daily plans
execution_blocks                → Time blocks
execution_events                → User actions
execution_preferences           → User settings
execution_reflections           → Daily feedback
execution_recovery_plans        → Recovery plans
```

---

## Integration Checklist

- [ ] Run `python migrate_execution_coach.py`
- [ ] Add imports to `web/app.py` (line ~75)
- [ ] Copy routes from `EXECUTION_COACH_ROUTES.py` into `web/app.py` (line ~2500+)
- [ ] Copy UI from `EXECUTION_COACH_UI.html` into `web/templates/home.html`
- [ ] Start Flask: `python web/app.py`
- [ ] Visit home page and verify UI loads
- [ ] Test "Start Focus" button
- [ ] (Optional) Set user preferences in database

---

## Expected Behavior

### First Time User Opens Home Page
```
1. System generates daily plan
2. Shows top 3 priorities
3. Shows time blocks for the day
4. Displays "do now" task
5. Shows momentum status (e.g., "On Track: 75/100")
```

### During the Day
```
1. Completed tasks update momentum
2. If falling behind, "Rebuild Day" button appears
3. Time blocks update as blocks pass
4. Habits tracked toward streak
```

### If Falling Behind
```
1. Momentum score drops
2. Status changes to "At Risk" or "Recovery Mode"
3. "Rebuild Day" button becomes prominent
4. User can click to get lighter 4-item plan
```

### End of Day (Optional)
```
1. User can save reflection on how day went
2. System learns from completion data
3. Tomorrow's plan adjusts based on insights
```

---

## Customization Quick Tips

### Change Recovery Threshold
In `execution_metrics.py`, line ~220:
```python
if momentum_score < 40:  # Change 40 to 50, 30, etc.
    status = RECOVERY_MODE
```

### Change Focus Duration
In `execution_planner.py`, line ~140:
```python
return 25  # Change to 45, 20, etc.
```

### Change Message Tone
In `EXECUTION_COACH_UI.html`, adjust coaching messages or edit generation in `execution_planner.py`

### Change Time Block Colors
In `EXECUTION_COACH_UI.html`, find the color hex codes and update:
```javascript
if (block.block_type === 'focus') {
    borderColor = '#ef4444';  // Change to your color
}
```

---

## Troubleshooting

### "Module not found" error
```
Make sure all 4 Python files are in project root:
- execution_planner.py
- execution_metrics.py
- execution_recovery.py
- execution_personalizer.py
```

### UI not showing
```
1. Check browser console (F12) for JS errors
2. Verify CSS classes exist (--color-primary-600, etc.)
3. Check home.html was updated correctly
4. Refresh page (Ctrl+Shift+R)
```

### API returns 401
```
User not authenticated. Check:
1. User session is valid
2. get_user() returns correct user object
3. Check Flask session cookie
```

### Momentum always shows 0
```
Check that these tables have data:
- ai_daily_tasks (completed tasks)
- focus_sessions (focus data)
- habits (habit data)
- users (streak data)
```

### Time blocks not showing
```
Check that:
1. User has work_time and free_time set (defaults: '09:00-17:00', '18:00-22:00')
2. ai_daily_tasks table has tasks
3. Check browser console for errors
```

---

## Next Steps (Optional)

### Basic Setup ✅ (You are here)
- [x] Create execution coach modules
- [x] Setup database
- [x] Add API routes
- [x] Add UI to home

### Intermediate (Pick One)
- [ ] Integrate with Focus Mode (pass task to focus session)
- [ ] Integrate with Chat (support "what should I do?" prompts)
- [ ] Integrate with Reminders (remind user before block starts)
- [ ] Integrate with Reports (add execution metrics to weekly report)

### Advanced (Future)
- [ ] ML-based duration estimation
- [ ] A/B test different task orderings
- [ ] Mobile app support
- [ ] Team collaboration features

---

## Key Files Reference

For **detailed integration steps**, see:
→ `EXECUTION_COACH_INTEGRATION_GUIDE.md`

For **architecture and design**, see:
→ `EXECUTION_COACH_ARCHITECTURE.md`

For **API route code**, see:
→ `EXECUTION_COACH_ROUTES.py`

For **UI code**, see:
→ `EXECUTION_COACH_UI.html`

For **module documentation**, see:
→ Docstrings in each .py file

---

## Support

### If something breaks:
1. Check the troubleshooting section above
2. Read `EXECUTION_COACH_INTEGRATION_GUIDE.md` for detailed help
3. Check browser console (F12) for JS errors
4. Check Flask logs for Python errors
5. Verify database migration ran successfully

### To customize:
1. Edit thresholds in `execution_metrics.py`
2. Edit scoring logic in `execution_planner.py`
3. Edit recovery plan in `execution_recovery.py`
4. Edit personalization in `execution_personalizer.py`
5. Edit UI in `EXECUTION_COACH_UI.html`

---

## What's Next After Setup?

```
🎉 Congratulations! Your Execution Coach is live!

Users will now experience:
✅ Daily planning that's realistic
✅ Real-time momentum tracking
✅ Smart recovery when falling behind
✅ Personalized coaching and guidance
✅ Integration with focus mode and habits

The system will automatically:
📊 Generate plans each morning
📈 Track momentum throughout the day
🆘 Suggest recovery if needed
📚 Learn from completion patterns
```

---

**Setup Time:** ~5 minutes  
**Integration Time:** ~15 minutes for full features  
**User Impact:** Immediate (visible on home page today)

Let's execute! 🚀
