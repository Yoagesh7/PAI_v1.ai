
from config import MAIN_MODEL

def analyze_habit_data(habits, logs):
    """
    Deterministic analysis of habit performance.
    Returns a structured analysis string.
    """
    if not habits:
        return "No habits found. Start tracking!"
        
    analysis = "📊 **Habit Analysis**\n\n"
    
    analysis += f"Tracking {len(habits)} habits.\n"
    total_logs = len(logs)
    analysis += f"Total completions logged: {total_logs}\n\n"
    
    # Calculate simple stats
    habit_counts = {}
    for log in logs:
        # log is (id, habit_id, date, status, notes)
        h_id = log[1]
        habit_counts[h_id] = habit_counts.get(h_id, 0) + 1
        
    analysis += "**Performance:**\n"
    
    for h in habits:
        # h is (id, user_id, title, ...)
        h_id = h[0]
        title = h[2]
        count = habit_counts.get(h_id, 0)
        
        status = "Needs Focus ⚠️"
        if count > 5: status = "Doing Great! 🔥"
        elif count > 2: status = "Good Start 👍"
            
        analysis += f"- **{title}**: {count} logs ({status})\n"
        
    return analysis
