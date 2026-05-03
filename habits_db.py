"""
Habits Database Helper Functions
Handles CRUD operations for habits and completion tracking.
"""
import sqlite3
from datetime import datetime, timedelta
import json
from memory import get_db

def init_habits_db():
    """Initialize habits tables if they don't exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Habits Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                icon TEXT DEFAULT '📝',
                frequency TEXT DEFAULT 'Daily',
                time_of_day TEXT DEFAULT 'Anytime',
                streak INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Completions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_str TEXT NOT NULL, -- YYYY-MM-DD for easy querying
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        """)
        conn.commit()

def create_habit(user_id, title, category="General", icon="📝", time_of_day="Anytime"):
    """Create a new habit."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO habits (user_id, title, category, icon, time_of_day)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, title, category, icon, time_of_day))
        conn.commit()
        return cursor.lastrowid

def delete_habit(habit_id, user_id):
    """Delete a habit and its history."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify ownership
        cursor.execute("SELECT id FROM habits WHERE id=? AND user_id=?", (habit_id, user_id))
        if not cursor.fetchone():
            return False
            
        # Delete completions first (FK)
        cursor.execute("DELETE FROM habit_completions WHERE habit_id=?", (habit_id,))
        # Delete habit
        cursor.execute("DELETE FROM habits WHERE id=?", (habit_id,))
        conn.commit()
        return True

def get_user_habits(user_id):
    """Get all habits for a user with their today's status."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"DEBUG_HABIT: Fetching for User {user_id} on {today_str}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all habits
        cursor.execute("""
            SELECT id, title, category, icon, time_of_day, streak 
            FROM habits 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        
        habits = []
        rows = cursor.fetchall()
        print(f"DEBUG_HABIT: Found {len(rows)} habits")
        
        for row in rows:
            habit_id = row[0]
            
            # Check if completed today
            cursor.execute("""
                SELECT 1 FROM habit_completions 
                WHERE habit_id = ? AND date_str = ?
            """, (habit_id, today_str))
            
            is_completed = cursor.fetchone() is not None
            print(f"DEBUG_HABIT: ID {habit_id} Completed? {is_completed}")
            
            habits.append({
                'id': habit_id,
                'title': row[1],
                'category': row[2],
                'icon': row[3],
                'time_of_day': row[4],
                'streak': row[5],
                'completed_today': is_completed
            })
            
        return habits

def toggle_habit(habit_id, user_id):
    """Toggle habit completion for today."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"DEBUG_HABIT: Toggling ID {habit_id} for User {user_id} on {today_str}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check current status
        cursor.execute("""
            SELECT id FROM habit_completions 
            WHERE habit_id = ? AND date_str = ?
        """, (habit_id, today_str))
        
        existing = cursor.fetchone()
        
        status = False
        if existing:
            # Remove completion
            print(f"DEBUG_HABIT: Removing completion {existing[0]}")
            cursor.execute("DELETE FROM habit_completions WHERE id = ?", (existing[0],))
            status = False
        else:
            # Add completion
            print(f"DEBUG_HABIT: Adding completion")
            cursor.execute("""
                INSERT INTO habit_completions (habit_id, user_id, completed_at, date_str)
                VALUES (?, ?, ?, ?)
            """, (habit_id, user_id, timestamp, today_str))
            status = True
            
        # Update streak using EXISTING cursor to avoid Deadlock
        update_streak(habit_id, cursor)
        
        conn.commit()
        print(f"DEBUG_HABIT: Committed. New Status: {status}")
        
        return status

def update_streak(habit_id, external_cursor=None):
    """Recalculate streak for a habit. Uses external_cursor if provided."""
    
    if external_cursor:
        _calculate_and_update(external_cursor, habit_id)
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            _calculate_and_update(cursor, habit_id)
            conn.commit()

def _calculate_and_update(cursor, habit_id):
    # Get all unique completion dates sorted desc
    cursor.execute("""
        SELECT DISTINCT date_str FROM habit_completions 
        WHERE habit_id = ? 
        ORDER BY date_str DESC
    """, (habit_id,))
    
    dates = [r[0] for r in cursor.fetchall()]
    streak = 0
    
    if dates:
        # Check if today or yesterday is present
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        current = datetime.strptime(dates[0], "%Y-%m-%d")
        
        # If the latest completion is not today or yesterday, streak is broken (or 0)
        # But wait, if we just toggled ON, it is today.
        
        if dates[0] == today or dates[0] == yesterday:
            streak = 1
            last_date = current
            
            for i in range(1, len(dates)):
                d = datetime.strptime(dates[i], "%Y-%m-%d")
                if (last_date - d).days == 1:
                    streak += 1
                    last_date = d
                else:
                    break
    
    cursor.execute("UPDATE habits SET streak=? WHERE id=?", (streak, habit_id))

def get_weekly_stats(user_id):
    """Get weekly completion stats for the chart."""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday()) # Monday
    
    dates = [(start_of_week + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    days_labels = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get total active habits count to calculate percentage
        cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (user_id,))
        total_habits = cursor.fetchone()[0]
        
        if total_habits == 0:
            return {'completion_rate': 0, 'chart_data': [{'day': d, 'label': l, 'value': 0} for d, l in zip(dates, days_labels)]}
            
        chart_data = []
        total_completions = 0
        
        for date_str, label in zip(dates, days_labels):
            cursor.execute("""
                SELECT COUNT(*) FROM habit_completions 
                WHERE user_id = ? AND date_str = ?
            """, (user_id, date_str))
            
            completed_count = cursor.fetchone()[0]
            if date_str <= datetime.now().strftime("%Y-%m-%d"):
                percentage = int((completed_count / total_habits) * 100)
                # Cap at 100
                percentage = min(100, percentage)
                total_completions += completed_count
            else:
                percentage = 0 # Future days
                
            chart_data.append({
                'day': date_str,
                'label': label,
                'value': percentage,
                'is_today': date_str == datetime.now().strftime("%Y-%m-%d")
            })
            
        # Calculate overall weekly completion rate
        # Only count up to today for the denominator
        days_passed = today.weekday() + 1
        possible_completions = total_habits * days_passed
        weekly_rate = int((total_completions / possible_completions) * 100) if possible_completions > 0 else 0
        
        # Calculate TODAY's specific rate for the big display
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM habit_completions WHERE user_id = ? AND date_str = ?", (user_id, today_str))
        today_completed = cursor.fetchone()[0]
        today_rate = int((today_completed / total_habits) * 100) if total_habits > 0 else 0
        
        return {
            'completion_rate': weekly_rate,
            'today_rate': today_rate,
            'chart_data': chart_data
        }

def analyze_habits_ai(user_id):
    """Generate AI insights based on habit data."""
    # Get user's completion history
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.title, h.time_of_day, hc.completed_at
            FROM habit_completions hc
            JOIN habits h ON hc.habit_id = h.id
            WHERE hc.user_id = ?
            ORDER BY hc.completed_at DESC
            LIMIT 50
        """, (user_id,))
        
        history = cursor.fetchall()
        
    if not history:
        return "Start tracking your habits to get personalized AI insights!"
        
    # Simple rule-based analysis (Mocking AI logic for speed, can connect to LLM later)
    # 1. Analyze Time of Day consistency
    morning_count = sum(1 for h in history if 5 <= datetime.strptime(h[2], "%Y-%m-%d %H:%M:%S").hour < 12)
    evening_count = sum(1 for h in history if 17 <= datetime.strptime(h[2], "%Y-%m-%d %H:%M:%S").hour < 23)
    
    if morning_count > len(history) * 0.5:
        return "You're a morning achiever! 🌅 You complete most habits before noon. Try stacking your hardest habits then."
    elif evening_count > len(history) * 0.5:
        return "You finish strong! 🌙 You're most consistent in the evenings."
    else:
        return "You have a balanced flow. Consider anchoring habits to specific cues to build stronger automaticity."
