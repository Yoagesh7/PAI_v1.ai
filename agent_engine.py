"""
Autonomous AI Agent Engine
Proactive system that monitors user activity and makes autonomous decisions.
Transforms the system from reactive (user asks) to proactive (AI observes → decides → acts).
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

# Setup logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_engine.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import database utilities
from memory import get_db, get_user, save_chat_message

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "dreamsyncai07@gmail.com"
EMAIL_PASSWORD = "whcvbcvflkgsnicj"

def send_email(to_email, subject, body):
    """Send email via SMTP"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Email failed to {to_email}: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# 1. DATA COLLECTION LAYER
# ─────────────────────────────────────────────────────────────

def collect_user_data(user_id: int) -> Dict[str, Any]:
    """
    Collects all relevant user data for decision making.
    
    Returns:
    {
        'user_id': int,
        'name': str,
        'last_active': datetime or None,
        'active_today': bool,
        'missed_tasks': int,
        'incomplete_tasks': int,
        'completed_tasks_today': int,
        'total_tasks_today': int,
        'completion_rate': float (0-100),
        'focus_sessions_today': int,
        'habit_completion_rate': float (0-100),
        'current_streak': int,
        'last_action_time': str or None,
        'inactivity_hours': float,
        'productivity_score': float (0-100)
    }
    """
    try:
        user = get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get today's date
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Count incomplete AI daily tasks
            cursor.execute(
                f"SELECT COUNT(*) as count FROM ai_daily_tasks WHERE user_id=? AND task_date=? AND status='pending'",
                (user_id, today)
            )
            incomplete_tasks = cursor.fetchone()[0]
            
            # Count completed AI daily tasks
            cursor.execute(
                f"SELECT COUNT(*) as count FROM ai_daily_tasks WHERE user_id=? AND task_date=? AND status='completed'",
                (user_id, today)
            )
            completed_tasks = cursor.fetchone()[0]
            
            total_tasks = incomplete_tasks + completed_tasks
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Count focus sessions today
            cursor.execute(
                f"SELECT COUNT(*) as count FROM focus_sessions WHERE user_id=? AND DATE(started_at)=?",
                (user_id, today)
            )
            focus_sessions_today = cursor.fetchone()[0]
            
            # Get habit completion rate for today
            cursor.execute(
                f"""SELECT COUNT(*) as total, 
                          SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) as completed
                   FROM habits WHERE user_id=?""",
                (user_id,)
            )
            habit_row = cursor.fetchone()
            total_habits = habit_row[0] if habit_row[0] else 0
            completed_habits = habit_row[1] if habit_row[1] else 0
            habit_completion_rate = (completed_habits / total_habits * 100) if total_habits > 0 else 0
            
            # Last active timestamp
            last_active_date = user.get('last_active_date')
            last_active = None
            inactivity_hours = 24
            
            if last_active_date:
                try:
                    last_active = datetime.strptime(last_active_date, "%Y-%m-%d")
                    inactivity_hours = (datetime.now() - last_active).total_seconds() / 3600
                except:
                    pass
            
            # Determine if active today
            active_today = inactivity_hours < 24
            
            # Productivity score (simple calculation)
            productivity_score = (completion_rate * 0.5) + (habit_completion_rate * 0.3) + (min(focus_sessions_today * 25, 100) * 0.2)
            
            data = {
                'user_id': user_id,
                'name': user.get('name', 'User'),
                'email': user.get('email', ''),
                'last_active': last_active,
                'active_today': active_today,
                'missed_tasks': incomplete_tasks,
                'incomplete_tasks': incomplete_tasks,
                'completed_tasks_today': completed_tasks,
                'total_tasks_today': total_tasks,
                'completion_rate': round(completion_rate, 2),
                'focus_sessions_today': focus_sessions_today,
                'habit_completion_rate': round(habit_completion_rate, 2),
                'current_streak': user.get('streak', 0),
                'last_action_time': last_active_date,
                'inactivity_hours': round(inactivity_hours, 2),
                'productivity_score': round(productivity_score, 2),
            }
            
            logger.info(f"Collected data for user {user_id}: {data}")
            return data
            
    except Exception as e:
        logger.error(f"Error collecting user data for {user_id}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 2. DECISION ENGINE (Rule-Based v1)
# ─────────────────────────────────────────────────────────────

def make_decision(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Makes autonomous decisions based on user data.
    Implements rule-based decision logic.
    
    Returns:
    {
        'action': str,  # reschedule_tasks, send_inactivity_nudge, suggest_focus, reduce_task_load, encourage_habits
        'reason': str,
        'priority': str,  # low, medium, high
        'details': dict
    }
    """
    if not user_data:
        return None
    
    try:
        action = None
        reason = None
        priority = "low"
        details = {}
        
        # Rule 1: Too many missed tasks
        if user_data['missed_tasks'] >= 2:
            action = "reschedule_tasks"
            reason = f"User has {user_data['missed_tasks']} missed tasks"
            priority = "high" if user_data['missed_tasks'] >= 3 else "medium"
            details = {
                'count': user_data['missed_tasks'],
                'completion_rate': user_data['completion_rate']
            }
        
        # Rule 2: Long inactivity
        elif user_data['inactivity_hours'] > 24:
            action = "send_inactivity_nudge"
            reason = f"User inactive for {user_data['inactivity_hours']:.1f} hours"
            priority = "medium" if user_data['inactivity_hours'] < 48 else "high"
            details = {
                'hours_inactive': user_data['inactivity_hours'],
                'last_active': user_data['last_action_time']
            }
        
        # Rule 3: No focus sessions today but has tasks
        elif user_data['total_tasks_today'] > 0 and user_data['focus_sessions_today'] == 0:
            action = "suggest_focus"
            reason = "User has tasks but no focus sessions scheduled"
            priority = "medium"
            details = {
                'pending_tasks': user_data['incomplete_tasks'],
                'total_tasks': user_data['total_tasks_today']
            }
        
        # Rule 4: Low completion rate
        elif user_data['completion_rate'] < 40:
            action = "reduce_task_load"
            reason = f"User completion rate is low: {user_data['completion_rate']}%"
            priority = "medium"
            details = {
                'current_rate': user_data['completion_rate'],
                'target_rate': 80
            }
        
        # Rule 5: Low habit completion
        elif user_data['habit_completion_rate'] < 30 and user_data['current_streak'] > 0:
            action = "encourage_habits"
            reason = f"User habit streak at risk: {user_data['current_streak']} days"
            priority = "low"
            details = {
                'streak': user_data['current_streak'],
                'completion_rate': user_data['habit_completion_rate']
            }
        
        if action:
            decision = {
                'action': action,
                'reason': reason,
                'priority': priority,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"Decision for user {user_data['user_id']}: {action} ({priority})")
            return decision
        
        return None
        
    except Exception as e:
        logger.error(f"Error making decision for user {user_data.get('user_id')}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 3. ACTION ENGINE
# ─────────────────────────────────────────────────────────────

def execute_action(user_id: int, decision: Dict[str, Any]) -> bool:
    """
    Executes the autonomous action decided by the decision engine.
    
    Actions:
    - reschedule_tasks: Move incomplete tasks to next day
    - send_inactivity_nudge: Send message and optional email reminder
    - suggest_focus: Insert AI message suggesting focus mode
    - reduce_task_load: Limit tasks to top priorities
    - encourage_habits: Send motivation message for streaks
    """
    if not decision:
        return False
    
    try:
        action = decision['action']
        user = get_user(user_id)
        
        if action == "reschedule_tasks":
            return _reschedule_tasks(user_id, user, decision)
        
        elif action == "send_inactivity_nudge":
            return _send_inactivity_nudge(user_id, user, decision)
        
        elif action == "suggest_focus":
            return _suggest_focus(user_id, user, decision)
        
        elif action == "reduce_task_load":
            return _reduce_task_load(user_id, user, decision)
        
        elif action == "encourage_habits":
            return _encourage_habits(user_id, user, decision)
        
        else:
            logger.warning(f"Unknown action: {action}")
            return False
            
    except Exception as e:
        logger.error(f"Error executing action for user {user_id}: {e}")
        return False


def _reschedule_tasks(user_id: int, user: Dict, decision: Dict) -> bool:
    """Move incomplete tasks to next day."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Get incomplete tasks
            cursor.execute(
                f"SELECT id FROM ai_daily_tasks WHERE user_id=? AND task_date=? AND status='pending'",
                (user_id, today)
            )
            tasks = cursor.fetchall()
            
            # Update them to tomorrow
            for task in tasks:
                cursor.execute(
                    f"UPDATE ai_daily_tasks SET task_date=? WHERE id=?",
                    (tomorrow, task[0])
                )
            
            conn.commit()
            
            message = f"📅 I've rescheduled your {len(tasks)} incomplete tasks to tomorrow. Let's reset and start fresh!"
            save_chat_message(user_id, 'ai', message)
            
            logger.info(f"Rescheduled {len(tasks)} tasks for user {user_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error rescheduling tasks for user {user_id}: {e}")
        return False


def _send_inactivity_nudge(user_id: int, user: Dict, decision: Dict) -> bool:
    """Send inactivity nudge via chat and email."""
    try:
        email = user.get('email', '')
        name = user.get('name', 'there')
        hours = decision['details'].get('hours_inactive', 24)
        
        # AI message in chat
        message = f"👋 I noticed you've been away for {int(hours)} hours. How's everything going? I'm here whenever you're ready to tackle your goals!"
        save_chat_message(user_id, 'ai', message)
        
        # Optional: Send email
        if email and hours > 48:
            subject = f"Checking in on your progress 👋"
            body = f"""Hi {name},

I noticed you haven't checked in with me for a while. I'm here to support you and help you stay on track with your goals!

Why not drop by and let me know what you're working on? 

Let's get back on track together! 🚀

- Your PartnerAI Mentor
"""
            send_email(email, subject, body)
            logger.info(f"Sent inactivity email to {email}")
        
        logger.info(f"Sent inactivity nudge to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending inactivity nudge to user {user_id}: {e}")
        return False


def _suggest_focus(user_id: int, user: Dict, decision: Dict) -> bool:
    """Suggest focus mode to help user concentrate."""
    try:
        pending = decision['details'].get('pending_tasks', 0)
        message = f"🎯 You have {pending} task(s) ready to go! Want to activate **Focus Mode** to minimize distractions and knock them out?"
        save_chat_message(user_id, 'ai', message)
        logger.info(f"Sent focus suggestion to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error suggesting focus for user {user_id}: {e}")
        return False


def _reduce_task_load(user_id: int, user: Dict, decision: Dict) -> bool:
    """Reduce task load by limiting to top priorities."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get all pending tasks ordered by creation (assume earliest = most important)
            cursor.execute(
                f"""SELECT id FROM ai_daily_tasks 
                   WHERE user_id=? AND task_date=? AND status='pending'
                   ORDER BY created_at ASC""",
                (user_id, today)
            )
            tasks = cursor.fetchall()
            
            # Keep only top 3, mark rest as postponed
            keep_count = 3
            if len(tasks) > keep_count:
                for task in tasks[keep_count:]:
                    cursor.execute(
                        f"UPDATE ai_daily_tasks SET status='postponed' WHERE id=?",
                        (task[0],)
                    )
                conn.commit()
                
                message = f"📌 I've focused your list to the **{keep_count} most important tasks** today. This keeps you from getting overwhelmed. You've got this! 💪"
                save_chat_message(user_id, 'ai', message)
                logger.info(f"Reduced task load for user {user_id}: kept {keep_count}, postponed {len(tasks) - keep_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error reducing task load for user {user_id}: {e}")
        return False


def _encourage_habits(user_id: int, user: Dict, decision: Dict) -> bool:
    """Encourage habit completion to maintain streak."""
    try:
        streak = decision['details'].get('streak', 0)
        message = f"🔥 You're on a **{streak}-day streak**! Don't break it now. Just one small habit today keeps the momentum going. You're doing amazing! 🎉"
        save_chat_message(user_id, 'ai', message)
        logger.info(f"Sent habit encouragement to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error encouraging habits for user {user_id}: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# 4. LOGGING SYSTEM
# ─────────────────────────────────────────────────────────────

def init_agent_actions_log():
    """Initialize the agent actions log table."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Determine ID type
            is_pg = "DATABASE_URL" in os.environ
            id_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS agent_actions_log (
                    id {id_type},
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    priority TEXT,
                    decision_data TEXT,
                    success INTEGER DEFAULT 0,
                    error_message TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()
            logger.info("Agent actions log table initialized")
            return True
            
    except Exception as e:
        logger.error(f"Error initializing agent actions log: {e}")
        return False


def log_action(user_id: int, action: str, reason: str, priority: str, 
               decision_data: Dict, success: bool, error_msg: str = None) -> bool:
    """Log an agent action to the database."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            decision_json = json.dumps(decision_data)
            
            cursor.execute(f"""
                INSERT INTO agent_actions_log 
                (user_id, action, reason, priority, decision_data, success, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, action, reason, priority, decision_json, int(success), error_msg, timestamp))
            
            conn.commit()
            logger.info(f"Logged action for user {user_id}: {action}")
            return True
            
    except Exception as e:
        logger.error(f"Error logging action for user {user_id}: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# 5. COOLDOWN SYSTEM (Prevent Spam)
# ─────────────────────────────────────────────────────────────

COOLDOWN_HOURS = 6  # Don't repeat the same action within 6 hours

def check_action_cooldown(user_id: int, action: str) -> bool:
    """Check if user is on cooldown for this action."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            hours_ago = (datetime.now() - timedelta(hours=COOLDOWN_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM agent_actions_log 
                WHERE user_id=? AND action=? AND timestamp > ? AND success=1
            """, (user_id, action, hours_ago))
            
            count = cursor.fetchone()[0]
            return count == 0  # True if no recent action found (not on cooldown)
            
    except Exception as e:
        logger.error(f"Error checking cooldown for user {user_id}: {e}")
        return True  # Assume not on cooldown if error


# ─────────────────────────────────────────────────────────────
# 6. MAIN ORCHESTRATION
# ─────────────────────────────────────────────────────────────

def run_autonomous_agent(user_id: int) -> bool:
    """
    Main orchestration function.
    Runs the complete agent pipeline for a single user.
    """
    logger.info(f"=== Running autonomous agent for user {user_id} ===")
    
    try:
        # 1. Collect data
        user_data = collect_user_data(user_id)
        if not user_data:
            return False
        
        # 2. Make decision
        decision = make_decision(user_data)
        if not decision:
            logger.info(f"No action needed for user {user_id}")
            return True
        
        # 3. Check cooldown
        action = decision['action']
        if not check_action_cooldown(user_id, action):
            logger.info(f"User {user_id} is on cooldown for action {action}")
            log_action(user_id, action, decision['reason'], decision['priority'], 
                      decision['details'], False, "Action on cooldown")
            return True
        
        # 4. Execute action
        success = execute_action(user_id, decision)
        
        # 5. Log the action
        log_action(user_id, action, decision['reason'], decision['priority'], 
                  decision['details'], success, None if success else "Execution failed")
        
        logger.info(f"Autonomous agent execution completed for user {user_id}: {action} - {'SUCCESS' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        logger.error(f"Critical error in autonomous agent for user {user_id}: {e}")
        return False


def run_autonomous_agent_for_all_users() -> Dict[int, bool]:
    """
    Runs the autonomous agent for all active users.
    Called by scheduler every 30 minutes.
    """
    logger.info("=== Running autonomous agent for all users ===")
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE state='ACTIVE' OR state='RETURNING'")
            user_ids = [row[0] for row in cursor.fetchall()]
        
        results = {}
        for user_id in user_ids:
            try:
                results[user_id] = run_autonomous_agent(user_id)
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}")
                results[user_id] = False
        
        logger.info(f"Autonomous agent cycle completed. Processed {len(user_ids)} users. Success: {sum(results.values())}/{len(user_ids)}")
        return results
        
    except Exception as e:
        logger.error(f"Critical error in autonomous agent cycle: {e}")
        return {}


# Initialize on import
init_agent_actions_log()

if __name__ == "__main__":
    # Testing
    print("Agent Engine Initialized")
    # Example: run_autonomous_agent_for_all_users()
