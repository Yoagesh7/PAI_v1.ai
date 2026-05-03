import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.append(ROOT_DIR)
import json
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import threading
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, Response, send_from_directory, stream_with_context


# ... (Previous imports) ...
from habits_db import init_habits_db, create_habit, get_user_habits, toggle_habit, get_weekly_stats, analyze_habits_ai, delete_habit

# Generic System Prompt
SYSTEM_PROMPT = "You are a helpful, friendly, and intelligent AI assistant. Answer the user's questions clearly and concisely."

# EMAIL CONFIGURATION
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "dreamsyncai07@gmail.com"
EMAIL_PASSWORD = "whcvbcvflkgsnicj"

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        print(f"DEBUG: Email sent to {to_email}", flush=True)
        return True
    except Exception as e:
        print(f"DEBUG: Email failed: {e}", flush=True)
        return False

# Add parent directory to path to allow importing config
sys.path.append(ROOT_DIR)

# Cloud AI configuration
MAIN_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
GROUP_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
MODEL_NAME = MAIN_MODEL
# ------------------------------------------------
from nvidia_llm import rag_system, AIConnectionError, _OFFLINE_MSG
from rag_engine_cloud import init_rag_system, build_rag_context, maybe_extract_memory
from memory import (
    get_user, save_user, reset_user, create_post, get_posts,
    create_group, join_group, get_user_group, get_group_members,
    set_group_goal, add_group_task, get_group_tasks, complete_group_task,
    save_chat_message, get_chat_history, create_account, verify_user,
    add_reward, get_rewards,
    create_daily_task, get_daily_tasks, toggle_daily_task,
    create_daily_article, get_latest_article,
    save_daily_news, get_daily_news,
    save_group_message, get_group_messages, update_group,
    # New team collaboration functions
    set_group_project, get_or_create_invite_code, join_group_by_invite,
    update_task_status, get_group_with_details, get_weekly_productivity,
    get_flow_day, increment_flow_day,
    save_focus_session, get_focus_stats,
    aggregate_user_routine,
    create_ai_task, get_ai_tasks_for_date, complete_ai_task,
    # Reminder functions
    save_reminder, get_pending_reminders, dismiss_reminder,
    clear_chat_history
)

# Smart Blocks imports
from smart_blocks import (
    create_block, validate_block_type, get_block_template,
    suggest_related_blocks, auto_link_blocks, analyze_block_network, BLOCK_TYPES
)
from smart_blocks_db import (
    get_user_blocks, update_smart_block, delete_smart_block,
    link_blocks, get_block_relationships, search_blocks
)

# Habit Intelligence imports
# Habit Intelligence imports
# from habit_intelligence import (...) # Removed unused imports

# Coach Engine imports
from coach_engine import create_weekly_report, calculate_progress_score

# RLHF Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../rlhf')))
try:
    from rlhf.strategy_selector import StrategySelector
    from rlhf.feedback_manager import FeedbackManager
except ImportError:
    # Fallback if running from root
    from rlhf.strategy_selector import StrategySelector
    from rlhf.feedback_manager import FeedbackManager

from reminders import parse_reminder_time, IST


def generate_weekly_insights(user_id):
    stats = get_weekly_stats(user_id)
    analysis = analyze_habits_ai(user_id)
    completion_rate = stats.get('completion_rate', 0)
    today_rate = stats.get('today_rate', 0)
    recommendations = []

    if completion_rate < 40:
        recommendations.append('Focus on one or two habits this week to build momentum.')
    elif completion_rate < 70:
        recommendations.append('Your consistency is decent; tighten your routine with fixed time blocks.')
    else:
        recommendations.append('Excellent momentum — keep your current cadence and protect it.')

    return {
        'week_score': completion_rate,
        'today_score': today_rate,
        'insights': [analysis],
        'recommendations': recommendations,
    }


def analyze_habit_failures(user_id, habit_name):
    habits = get_user_habits(user_id)
    habit = next((h for h in habits if h['title'].lower() == habit_name.lower()), None)
    if not habit:
        return {'habit': habit_name, 'reasons': ['Habit not found'], 'suggestions': []}

    reasons = []
    suggestions = []
    if not habit.get('completed_today'):
        reasons.append('It has not been completed today.')
    if habit.get('streak', 0) < 3:
        reasons.append('The habit streak is still building.')

    if habit.get('time_of_day') == 'Morning':
        suggestions.append('Move it to your first 30 minutes after waking.')
    elif habit.get('time_of_day') == 'Evening':
        suggestions.append('Place it after dinner or before your shutdown routine.')
    else:
        suggestions.append('Attach it to an existing routine trigger like meals or commute.')

    return {'habit': habit_name, 'reasons': reasons or ['Low consistency detected'], 'suggestions': suggestions}


def detect_optimal_timing(user_id, habit_name):
    habits = get_user_habits(user_id)
    habit = next((h for h in habits if h['title'].lower() == habit_name.lower()), None)
    if not habit:
        return {'habit': habit_name, 'best_time': 'Anytime', 'reason': 'Habit not found'}

    time_of_day = habit.get('time_of_day') or 'Anytime'
    return {
        'habit': habit_name,
        'best_time': time_of_day,
        'reason': f"This habit is currently configured for {time_of_day.lower()} focus."
    }


def map_habits_to_goals(user_id):
    user = get_user(user_id)
    goal = user[2] if user and len(user) > 2 else ''
    habits = get_user_habits(user_id)
    return {
        'goal': goal,
        'habits': [{'name': h['title'], 'category': h.get('category', 'General')} for h in habits],
        'summary': f"Mapped {len(habits)} habits to the current goal."
    }


def auto_adjust_habit(user_id, habit_name):
    habit = next((h for h in get_user_habits(user_id) if h['title'].lower() == habit_name.lower()), None)
    if not habit:
        return {'habit': habit_name, 'adjustments': ['Habit not found']}
    return {
        'habit': habit_name,
        'adjustments': [
            'Reduce the habit size by 50% for one week.',
            f"Keep it in your {habit.get('time_of_day', 'preferred')} window.",
            'Track completion for 7 days before making another change.'
        ]
    }

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = 'partnerai_secret_key'  # Needed for session

QUOTES = [
    "Believe in yourself! 🌟",
    "Consistency is key. 🗝️",
    "Small steps lead to big places. 🚀",
    "You got this! 💪",
    "Keep pushing, you're doing great! 🔥"
]

@app.route('/debug/routes')
def debug_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote("{:50s} {:20s} {}".format(str(rule), methods, rule.endpoint))
        output.append(line)
    return "<pre>" + "\n".join(output) + "</pre>"


@app.route('/intro')
def intro_page():
    return render_template('intro.html')

@app.route('/')
def home():
    if 'user_id' not in session:
        return render_template('intro.html')
    
    # Check if user needs onboarding
    user_id = session['user_id']
    user = get_user(user_id)
    # Check Onboarding
    if user:
         # Schema Mapping (0-indexed):
         # 0:user_id, 1:name, 2:goal, 6:state, 11:work_time, 12:free_time, 13:age
         try:
            goal = user[2]
            state = user[6]
            work_t = user[11]
            free_t = user[12]
            age = user[13]
            
            print(f">>> HOME: User {user_id} | State: {state} | Goal: {goal} | Age: {age}", flush=True)

            # Manual bypass for debugging
            if request.args.get('force_chat') == 'true':
                 return render_template('chat.html', active_page='chat', history=get_chat_history(user_id))

            # Logic: If they have a goal and aren't in WAITING state, they're good.
            # We use a broad check to prevent loops.
            if goal and state == "ACTIVE":
                print(f">>> HOME: User {user_id} verified ACTIVE. Loading Home Dashboard.", flush=True)
                history = get_chat_history(user_id, limit=50)
                return render_template('home.html', active_page='home', history=history)
            
            print(f">>> HOME: User {user_id} failed check. Redirecting to onboarding...", flush=True)
            return redirect('/onboarding')
         except Exception as e:
            print(f">>> HOME ERROR: {e}", flush=True)
            return redirect('/onboarding')
    else:
        print(f">>> HOME: No user Record for ID {user_id}. Redirecting...", flush=True)
        return redirect('/onboarding')

@app.route('/api/init')
def api_init_chat():
    if 'user_id' not in session: 
        return jsonify({'history': []}) # Return empty valid structure instead of 401/error for safety
    
    user_id = session['user_id']
    try:
        # Check if user exists first to match home logic
        user = get_user(user_id)
        if not user:
            return jsonify({'history': []})

        history = get_chat_history(user_id, limit=50)
        print(f"DEBUG: /api/init served {len(history)} msgs for {user_id}", flush=True)
        return jsonify({'history': history})
    except Exception as e:
        print(f"DEBUG: /api/init error: {e}", flush=True)
        return jsonify({'history': []})

@app.route('/onboarding')
def onboarding_page():
    if 'user_id' not in session: return redirect('/login')
    # If they are already active, don't let them back into onboarding unless they want to
    user = get_user(session['user_id'])
    if user and user[6] == "ACTIVE" and not request.args.get('re_onboard'):
         return redirect('/')
    return render_template('onboarding.html')
@app.route('/api/onboarding/complete', methods=['POST'])
def complete_onboarding():
    data = request.json
    user_id = session.get('user_id')
    if not user_id: return jsonify({'error': 'No session'}), 401
    
    # Extract data
    name = data.get('name')
    age = data.get('age')
    goal = data.get('goal')
    work_time = data.get('work_time')
    free_time = data.get('free_time')
    
    # 1. Save User FIRST with placeholder to ensure instant transition
    initial_tasks = f"✅ Define your first milestone for '{goal}'\n✅ Calendar blocking for {free_time}\n✅ Research best resources"
    
    save_user(user_id, 
              name=name, 
              age=age, 
              career=goal, 
              work_time=work_time, 
              free_time=free_time, 
              state="ACTIVE",
              last_task=initial_tasks,
              task_status="pending")

    # 2. Run AI in Background to update tasks later
    def generate_initial_tasks_bg():
         prompt = (
            f"Context: User '{name}' (Age {age}) wants to '{goal}'.\n"
            f"Constraint: Their Work Time is '{work_time}', Free Time is '{free_time}'.\n"
            "Act as a PartnerAI Mentor.\n"
            "Task 1: Generate 3 actionable starter tasks for them.\n"
            "Output: Plain text list with emojis."
         )
         try:
             # Re-import to ensure thread safety scope
             # from ollama_utils import safe_ollama_chat, OllamaConnectionError
             # from config import MODEL_NAME
             # from mentor_prompt import SYSTEM_PROMPT # Removed dependency
             
             system_prompt = (
                f"You are PartnerAI, a dedicated Mentor for {name}."
                f"Your GOAL is to help them achieve: '{goal}'."
                "Create a 3-step high-level roadmap."
             )

             response = rag_system.generate_response(messages=[
                 {"role": "system", "content": system_prompt},
                 {"role": "user", "content": prompt}
             ])
             new_tasks = response['message']['content']
             
             # Update DB with real AI tasks
             save_user(user_id, last_task=new_tasks)
             
             # Send welcome message
             welcome_msg = f"All set, {name}! 🚀\n\nI've analyzed your schedule and goal ('{goal}').\nI'm ready to help you grow. Check your tasks below! 👇"
             save_chat_message(user_id, 'ai', welcome_msg)
             print(f"DEBUG: Background AI Onboarding Complete for {name}", flush=True)

             # Send Welcome Email
             try:
                 # Fetch latest user data to get email (Index 17 based on schema)
                 updated_user = get_user(user_id)
                 user_email = updated_user[17] if updated_user and len(updated_user) > 17 else None
                 
                 if user_email and "@" in user_email:
                     subject = "🚀 Welcome to PartnerAI - Let's Crush Your Goals!"
                     body = f"""Hi {name}!
                     
Welcome to PartnerAI! I'm thrilled to be your productivity partner. 🌟

You've set a bold goal: "{goal}".
I've already analyzed your schedule and I'm ready to help you every step of the way.

Here's what you can do next:
1. Check your Dashboard for your daily tasks.
2. Use Focus Mode to crush your work sessions.
3. Chat with me anytime for advice or motivation.

Let's make it happen! 💪

- Your PartnerAI Mentor
"""
                     send_email(user_email, subject, body)
             except Exception as e:
                 print(f"DEBUG: Welcome Email Failed: {e}", flush=True)

         except Exception as e:
             print(f"DEBUG: AI service failed during onboarding: {e}", flush=True)
             # Keep the initial fallback tasks - they're already saved
         except Exception as e:
             print(f"DEBUG: Background Onboarding AI Failed: {e}", flush=True)

    threading.Thread(target=generate_initial_tasks_bg).start()
    
    return jsonify({'success': True})

@app.route('/reset')
def reset_account():
    if 'user_id' in session:
        reset_user(session['user_id'])
    return redirect('/onboarding')


@app.route('/focus')
def focus_mode():
    return render_template('focus_mode.html', active_page='productivity')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')



@app.route('/community')
def community_page():
    if 'user_id' not in session: return render_template('login.html')
    return render_template('community.html', active_page='community')

@app.route('/habits')
def habits_page():
    if 'user_id' not in session: return render_template('login.html')
    return render_template('habits.html', active_page='habits')

@app.route('/group')
def group_page():
    if 'user_id' not in session: return render_template('login.html')
    return render_template('group.html', active_page='group')

@app.route('/productivity')
def productivity_page():
    if 'user_id' not in session: return render_template('login.html')
    return render_template('productivity.html', active_page='productivity')




@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


@app.route('/api/debug/ai-key')
def debug_ai_key():
    """Return whether the NVIDIA API key is present on the running server.
    This endpoint intentionally does NOT reveal the key value.
    """
    try:
        present = bool(getattr(rag_system, 'api_key', None))
        return jsonify({'present': present})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API ENDPOINTS ---


@app.route('/api/user')
def api_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user = get_user(user_id)
    if user:
        return jsonify({
            'user_id': user[0],
            'username': user[1],
            'goal': user[2] if len(user) > 2 else None
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email') # New
    
    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400
        
    user_id = create_account(username, password, email)
    if not user_id:
        return jsonify({'error': 'Username already exists'}), 400
        
    session['user_id'] = user_id
    session['user_name'] = username
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user_id = verify_user(username, password)
    if user_id:
        session['user_id'] = user_id
        session['user_name'] = username
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/switch', methods=['POST'])
def switch_user():
    data = request.json
    user_id = int(data.get('user_id', 1))
    name = f"User {user_id}"
    session['user_id'] = user_id
    session['user_name'] = name
    
    # Ensure user exists in DB
    if not get_user(user_id):
        save_user(user_id, name=name, state="ACTIVE")
        
    return jsonify({'success': True, 'user_name': name})

@app.route('/api/group/status', methods=['GET'])
def group_status():
    user_id = session.get('user_id', 1)
    group = get_user_group(user_id)
    if not group:
        return jsonify({'in_group': False})
    
    # group: id, name, goal, leader_id, status
    group_id = group[0]
    tasks = get_group_tasks(group_id)
    members = get_group_members(group_id)
    
    return jsonify({
        'in_group': True,
        'name': group[1],
        'goal': group[2],
        'status': group[4],
        'is_leader': (group[3] == user_id),
        'tasks': [{'id': t[0], 'assigned_to': t[2], 'content': t[3], 'status': t[4]} for t in tasks],
        'member_count': len(members)
    })

@app.route('/api/group/create_or_join', methods=['POST'])
def create_or_join():
    data = request.json
    action = data.get('action')
    user_id = session.get('user_id', 1)
    
    if action == 'create':
        container_name = data.get('name', 'Squad')
        create_group(container_name, user_id)
    elif action == 'join':
        # Simply join the most recent group created by anyone (for demo simplicity)
        # In real app, would need group code
        # We'll just hack: try joining group ID 1, 2, etc. or just last created.
        # Actually let's just create a new group if none, or join last.
        # For this demo, let's just make "User 2" join "User 1"'s group
        success = join_group(group_id=1, user_id=user_id) # Hardcoded demo assumption
        if not success: return jsonify({'error': 'Could not join (full or invalid)'})
        
    return jsonify({'success': True})

@app.route('/api/group/set_goal', methods=['POST'])
def group_set_goal():
    data = request.json
    goal = data.get('goal')
    user_id = session.get('user_id', 1)
    group = get_user_group(user_id)
    
    if not group or group[3] != user_id: # Only leader
        return jsonify({'error': 'Not authorized'})

    group_id = group[0]
    set_group_goal(group_id, goal)
    
    try:
        # AI Logic: Assign Tasks
        members = get_group_members(group_id) # list of IDs
        
        # Simple mocked AI task assignment
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": f"You are a team manager. The goal is: '{goal}'. There are {len(members)} members. Assign 1 specific task to each member ID ({members}). Return JSON list of strings: ['User 1 Task', 'User 2 Task']."},
            {"role": "user", "content": "Assign now."}
        ])
        
        try:
            # Optimistic parsing
            content = response['message']['content']
            # Fallback if AI is chatty
            if "[" not in content: 
                 tasks_text = ["Research phase", "Implementation phase"]
            else:
                 # Very rough extraction
                 start = content.find('[')
                 end = content.find(']') + 1
                 tasks_text = json.loads(content[start:end])
        except:
            tasks_text = [f"Work on {goal}" for _ in members]

        for i, member_id in enumerate(members):
            task_str = tasks_text[i] if i < len(tasks_text) else "Support team"
            add_group_task(group_id, member_id, task_str)
    except Exception as e:
        print(f"DEBUG: AI service failed for group tasks: {e}", flush=True)
        # Fallback manual assignment if AI service unavailable
        for member_id in members:
            add_group_task(group_id, member_id, f"Core work on '{goal}'")
    except Exception as e:
        print(f"DEBUG: Group AI Task Gen Failed: {e}", flush=True)
        # Fallback manual assignment if AI fails
        for member_id in members:
            add_group_task(group_id, member_id, f"Core work on '{goal}'")

    return jsonify({'success': True})

@app.route('/api/group/complete_task', methods=['POST'])
def complete_task():
    data = request.json
    task_id = data.get('task_id')
    complete_group_task(task_id)
    return jsonify({'success': True})


@app.route('/api/stats', methods=['GET'])
@app.route('/api/stats', methods=['GET'])
def get_stats():
    # Attempt to use session, else fallback to 21 (Data found in DB) or 1
    current_uid = session.get('user_id', 21) 
    user = get_user(current_uid)
    
    if not user:
        # Prevent frontend crash by returning empty chart data
        return jsonify({
            'level': 1, 'streak': 0, 'tasks': 0, 
            'quote': "Start your journey today!",
            'history': [0]*7,
            'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        })
    
    # Unpack user stats
    # Schema: (user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic)
    try:
        tasks_completed = user[7] if user[7] is not None else 0
        streak = user[8] if user[8] is not None else 0
        level = 1 + (tasks_completed // 5)
    except:
         tasks_completed = 0
         streak = 0
         level = 1

    # Get real weekly stats
    print(f"DEBUG: /api/stats for user {current_uid}", flush=True)
    weekly_stats = get_weekly_productivity(current_uid)
    print(f"DEBUG: Weekly Stats Res: {weekly_stats}", flush=True)

    return jsonify({
        'level': level,
        'streak': streak,
        'tasks': tasks_completed,
        'quote': random.choice(QUOTES),
        'history': weekly_stats['counts'],
        'days': weekly_stats['days']

    })

@app.route('/api/community/posts', methods=['GET', 'POST'])
def community_api():
    if request.method == 'GET':
        posts = get_posts(limit=20)
        return jsonify(posts)
    
    if request.method == 'POST':
        data = request.json
        content = data.get('content', '').strip()
        if not content: return jsonify({'error': 'Empty post'}), 400
        
        current_uid = session.get('user_id', 1)
        user = get_user(current_uid)
        user_name = user[1] if user else f"User {current_uid}"
        
        create_post(user_name, content)
        return jsonify({'success': True})

# --- AI DAILY TASKS API ---
@app.route('/api/ai-tasks', methods=['GET'])
def get_ai_tasks():
    """Get today's AI-generated tasks"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    from memory import get_ai_tasks_for_date
    tasks = get_ai_tasks_for_date(user_id)
    
    return jsonify({'tasks': tasks})



@app.route('/api/ai-tasks/complete', methods=['POST'])
def complete_ai_task_endpoint():
    """Mark an AI task as completed"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'Task ID required'}), 400
    
    from memory import complete_ai_task
    complete_ai_task(task_id)
    
    return jsonify({'success': True})

@app.route('/api/ai-tasks/clear', methods=['POST'])
def clear_ai_tasks_endpoint():
    """Clear all AI tasks for today"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    from memory import clear_ai_tasks_for_date
    clear_ai_tasks_for_date(session['user_id'])
    return jsonify({'success': True})

# /api/ai-tasks/generate removed — tasks are now auto-extracted from chat conversations


# ---------------------------------------------------------------------------
# Background task extractor — runs after every AI reply
# ---------------------------------------------------------------------------
def _extract_tasks_from_chat(user_id: int, user_message: str, ai_reply: str, user_goal: str):
    """Parse the AI reply for actionable tasks and save them to ai_daily_tasks.

    Runs in a background thread so it never slows down the streaming response.
    Uses a lightweight LLM call to extract concrete tasks from the conversation.
    """
    try:
        # Skip very short replies or system messages
        if not ai_reply or len(ai_reply.strip()) < 30:
            return

        extraction_prompt = (
            "You are a task extraction engine. Read the following conversation between a user and their AI mentor, "
            "then extract any ACTIONABLE tasks or action items the AI recommended.\n\n"
            "RULES:\n"
            "1. Only extract concrete, specific actions (NOT vague advice).\n"
            "2. If NO actionable task exists, return exactly: []\n"
            "3. Maximum 3 tasks. Each task must be under 15 words.\n"
            "4. Return ONLY a JSON array of strings. No explanation.\n\n"
            f"User goal: {user_goal}\n\n"
            f"User said: {user_message[:500]}\n\n"
            f"AI replied: {ai_reply[:1000]}\n\n"
            "Extracted tasks (JSON array):"
        )

        response = rag_system.generate_response(
            messages=[
                {"role": "system", "content": "Return ONLY a valid JSON array of strings. Nothing else."},
                {"role": "user", "content": extraction_prompt},
            ],
            temperature=0.2,
        )

        content = response["message"]["content"].strip()

        # Parse JSON array from the response
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()

        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            return

        import json as _json
        tasks = _json.loads(content[start:end])

        if not isinstance(tasks, list) or len(tasks) == 0:
            return

        # Deduplicate against today's existing tasks
        existing = get_ai_tasks_for_date(user_id)
        existing_lower = {t["task"].lower().strip() for t in existing}

        saved = 0
        for task_text in tasks[:3]:
            task_text = str(task_text).strip()
            if not task_text or task_text.lower() in existing_lower:
                continue
            create_ai_task(user_id, task_text)
            existing_lower.add(task_text.lower())
            saved += 1

        if saved:
            print(f"✅ Extracted {saved} task(s) from chat for user {user_id}", flush=True)

    except Exception as e:
        print(f"DEBUG: Task extraction error (non-fatal): {e}", flush=True)


@app.route('/api/chat', methods=['POST'])
def chat():
    print("DEBUG: /api/chat endpoint HIT (Start)", flush=True)
    data = request.json
    text = data.get('message', '').strip()
    deep_think = data.get('deep_think', False)
    
    if not text:
        return Response("Error: No message", mimetype='text/plain')

    user_id = session.get('user_id', 1)
    
            # SAVE USER MESSAGE TO HISTORY
    save_chat_message(user_id, 'user', text)
    
    user = get_user(user_id)

    # --- PARTNER AI LOGIC ---
    name = user[1] if user else "Friend"
    # ... (other user vars extraction if needed by RAG, but RAG handles context)

    is_command = text.startswith("/")
    
    if is_command:
        # ... (keep command handling)
        pass # Placeholder to signify indentation, actual commands are below

        # /custom [tasks]
        if text.startswith("/custom"):
            custom_tasks = text.replace("/custom", "").strip()
            if not custom_tasks:
                return Response("⚠️ Please specify tasks! Example: `/custom Write code, Drink water`", mimetype='text/plain')
            
            save_user(user_id, last_task=custom_tasks, task_status="pending", state="ACTIVE")
            msg = f"📝 **Tasks Updated!**\n\nI've set your current focus to:\n_{custom_tasks}_\n\nLet's get to work! 🚀"
            save_chat_message(user_id, 'ai', msg)
            return Response(msg, mimetype='text/plain')

        # /reminder [time] [msg]
        if text.startswith("/reminder"):
            clean_text = text.replace("/reminder", "").strip()
            
            if not clean_text:
                return Response("⏰ Usage: `/reminder [time] [message]`\nExamples:\n• `/reminder 10m Drink water`\n• `/reminder 2h Check oven`\n• `/reminder 5pm Call mom`", mimetype='text/plain')
            
            # Parse time from the full text
            from reminders import parse_reminder_time, IST
            
            # Try parsing the full clean_text for patterns like "at 5pm call mom"
            parsed_time = parse_reminder_time(clean_text)
            
            # Determine content and delay
            content = clean_text
            time_label = ""
            delay_seconds = 0
            
            if parsed_time:
                if isinstance(parsed_time, timedelta):
                    delay_seconds = parsed_time.total_seconds()
                    # Extract content: remove the time part
                    import re as _re
                    content = _re.sub(r'(?:in\s+)?\d+\s*(?:m(?:in(?:ute)?s?)?|h(?:(?:ou)?rs?)?|s(?:ec(?:ond)?s?)?)\s*', '', clean_text).strip()
                    mins = int(delay_seconds // 60)
                    time_label = f"{mins} minute{'s' if mins != 1 else ''}" if mins > 0 else f"{int(delay_seconds)} seconds"
                elif isinstance(parsed_time, datetime):
                    delay_seconds = (parsed_time - datetime.now(IST)).total_seconds()
                    # Extract content: remove the time part
                    import re as _re
                    content = _re.sub(r'(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*', '', clean_text).strip()
                    time_label = parsed_time.strftime("%I:%M %p")
            else:
                # Fallback: split by first space (e.g., "10m drink water")
                parts = clean_text.split(" ", 1)
                if len(parts) >= 1:
                    parsed_time = parse_reminder_time(parts[0])
                if parsed_time:
                    content = parts[1] if len(parts) >= 2 else "Check in"
                    if isinstance(parsed_time, timedelta):
                        delay_seconds = parsed_time.total_seconds()
                        mins = int(delay_seconds // 60)
                        time_label = f"{mins} minute{'s' if mins != 1 else ''}" if mins > 0 else f"{int(delay_seconds)} seconds"
                    elif isinstance(parsed_time, datetime):
                        delay_seconds = (parsed_time - datetime.now(IST)).total_seconds()
                        time_label = parsed_time.strftime("%I:%M %p")
            
            if not content:
                content = "Check in"
            
            if delay_seconds <= 0:
                return Response("⚠️ Invalid time. Try:\n• `/reminder 10m Drink water`\n• `/reminder 2h Check oven`\n• `/reminder 5pm Call mom`", mimetype='text/plain')
            
            # Get user email
            user_email = user[17] if user and len(user) > 17 and user[17] else None
            r_name = name  # capture for thread closure
            r_content = content
            r_delay = delay_seconds
            
            print(f"DEBUG: Reminder set — email={user_email}, content='{r_content}', delay={int(r_delay)}s", flush=True)
            
            # Schedule email in background thread (simple, no LLM)
            def send_scheduled_email():
                import time as _time
                _time.sleep(r_delay)
                try:
                    # Re-fetch user for fresh email
                    u = get_user(user_id)
                    email = u[17] if u and len(u) > 17 and u[17] else user_email
                    if email and "@" in email:
                        u_name = u[1] if u else r_name
                        subject = f"⏰ Reminder: {r_content}"
                        body = f"Hey {u_name}!\n\n🔔 Here's your reminder:\n\n    {r_content}\n\nStay on track! 💪\n\n- PartnerAI"
                        success = send_email(email, subject, body)
                        print(f"DEBUG: Reminder email sent={success} to {email}", flush=True)
                    else:
                        print(f"DEBUG: No valid email for reminder '{r_content}'", flush=True)
                except Exception as e:
                    print(f"DEBUG: Reminder email error: {e}", flush=True)
            
            threading.Thread(target=send_scheduled_email).start()
            
            # Save in-app reminder for notification
            trigger_at = (datetime.now() + timedelta(seconds=delay_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            save_reminder(user_id, content, trigger_at)
            
            msg = f"⏰ **Reminder Set!**\n\nI'll remind you to **'{content}'** in **{time_label}**.\n📧 You'll get an email + in-app notification when it's time! 🔔"
            save_chat_message(user_id, 'ai', msg)
            return Response(msg, mimetype='text/plain')

        # /reset
        if text.startswith("/reset"):
             reset_user(user_id)
             msg = "🧹 **Memory Wiped!**\n\nI've forgotten everything by your request. Let's start fresh! 🌟\n\nRefesh the page to restart onboarding."
             save_chat_message(user_id, 'ai', msg)
             return Response(msg, mimetype='text/plain')
        
        # /report 
        if text.startswith("/report"):
            def analyze_user_report():
                yield "📊 **Analyzing Your Productivity Report...**\n\nFetching your stats... 📈\n\n"
                
                try:
                    # Fetch user data
                    tasks_completed = user[7] if user and len(user) > 7 and user[7] is not None else 0
                    streak = user[8] if user and len(user) > 8 and user[8] is not None else 0
                    level = 1 + (tasks_completed // 5)
                    user_goal = user[2] if user and len(user) > 2 and user[2] else "Not set"
                    
                    # Get weekly productivity
                    weekly_stats = get_weekly_productivity(user_id)
                    total_this_week = sum(weekly_stats['counts'])
                    
                    # Get habits data if available
                    try:
                        habits = get_user_habits(user_id)
                        habit_stats = get_weekly_stats(user_id)
                        habit_count = len(habits) if habits else 0
                        habit_completion = habit_stats.get('completion_rate', 0) if habit_stats else 0
                    except:
                        habit_count = 0
                        habit_completion = 0
                    
                    # Prepare data summary for AI
                    data_summary = f"""
User Profile Analysis Data:
- Name: {name}
- Primary Goal: {user_goal}
- Level: {level}
- Total Tasks Completed: {tasks_completed}
- Current Streak: {streak} days
- Tasks This Week: {total_this_week}
- Weekly Activity: {weekly_stats['counts']} (across {weekly_stats['days']})
- Active Habits: {habit_count}
- Habit Completion Rate: {habit_completion}%

Task: Analyze this user's productivity data and provide a comprehensive, structured review.
"""
                    
                    # AI Analysis Prompt
                    analysis_prompt = f"""{data_summary}

Generate a detailed productivity report with the following structure:

# 📊 Your Productivity Analysis

## 🎯 Current Status
Brief overview of user's current level and performance

## ✅ Areas of Improvement
List 2-3 specific areas where the user has shown progress

## ⚠️ Identified Weaknesses  
List 2-3 areas that need attention or improvement

## 💪 Positive Patterns
Highlight 2-3 positive habits or behaviors observed

## 🚀 Recommendations for Next Week
Provide 3-5 specific, actionable recommendations

Use markdown formatting with proper headings, bold text, and emojis. Be encouraging but honest. Keep it concise but meaningful."""

                    # Stream AI response
                    response = rag_system.generate_response(messages=[
                        {"role": "system", "content": "You are a productivity coach analyzing user data. Provide structured, actionable insights."},
                        {"role": "user", "content": analysis_prompt}
                    ])
                    
                    analysis = response['message']['content']
                    
                    # Save to chat history
                    save_chat_message(user_id, 'ai', analysis)
                    
                    yield analysis
                    
                except Exception as e:
                    print(f"Report Analysis Error: {e}", flush=True)
                    error_msg = f"❌ **Error generating report analysis.**\n\nReason: {str(e)}\n\nPlease try again."
                    save_chat_message(user_id, 'ai', error_msg)
                    yield error_msg
            
            return Response(stream_with_context(analyze_user_report()), mimetype='text/plain')
        
        # /reminder - Send immediate email with current tasks
        if text.startswith("/reminder"):
            user_email = user[17] if user and len(user) > 17 and user[17] else None
            
            if not user_email:
                msg = "❌ **No Email Found**\n\nPlease set your email in your profile to receive reminders!"
                save_chat_message(user_id, 'ai', msg)
                return Response(msg, mimetype='text/plain')
            
            from memory import get_ai_tasks_for_date
            # from datetime import datetime # Removed to fix UnboundLocalError
            import random
            
            tasks = get_ai_tasks_for_date(user_id)
            
            if not tasks:
                msg = "⚠️ **No Tasks Found**\n\nYou haven't generated any tasks yet. Use the home page to create your AI-powered daily tasks first!"
                save_chat_message(user_id, 'ai', msg)
                return Response(msg, mimetype='text/plain')
            
            # Build task list
            task_list = "\n".join([f"{'✅' if t['status'] == 'completed' else '⚠️'} {t['task']}" for t in tasks])
            
            motivational_quotes = [
                "Every small step counts. Keep pushing forward! 💪",
                "Success is the sum of small efforts repeated day in and day out.",
                "Don't wait for perfect conditions. Start where you are!",
                "Your only limit is you. Make today count! 🚀",
                "Progress, not perfection. You've got this! 🔥"
            ]
            
            quote = random.choice(motivational_quotes)
            
            # Email subject and body
            subject = f"⏰ Task Reminder for {name}!"
            body = f"""Hey {name}!

Here's a reminder of your tasks for {datetime.now().strftime('%B %d, %Y')}:

{task_list}

💡 {quote}

Keep going strong! 💪

- PartnerAI
"""
            
            # Send email
            try:
                send_email(user_email, subject, body)
                msg = f"✅ **Reminder Sent!**\n\nI've sent an email to **{user_email}** with your current tasks. Check your inbox! 📧"
            except Exception as e:
                print(f"Email send error: {e}", flush=True)
                msg = f"❌ **Email Failed**\n\nCouldn't send email to {user_email}. Please check your email settings.\n\nError: {str(e)}"
            
            save_chat_message(user_id, 'ai', msg)
            return Response(msg, mimetype='text/plain')
        
        # /daily
        if text.startswith("/daily"):
            existing = get_daily_tasks(user_id)
            if existing:
                msg = "📅 **Daily Tasks Already Set!**\n\nYou've already generated your tasks for today. Check the Productivity Dashboard to finish them! 🚀"
                save_chat_message(user_id, 'ai', msg)
                return Response(msg, mimetype='text/plain')
            
            # Generate Logic
            def generate_daily():
                yield "🧠 **Analyzing your goals...** generating daily plan...\n\n"
                
                user_goal = user[2] if user and len(user) > 2 and user[2] else "Productivity"
                
                # Dynamic Persona Prompt for Tasks
                prompt = (
                    f"User Goal: '{user_goal}'. Context: User is Age {user[13] if len(user) > 13 else 'N/A'}.\n"
                    f"Date: {datetime.now().strftime('%Y-%m-%d')}.\n"
                    "ACT AS AN EXPERT COACH. Create exactly 3 HIGHLY SPECIFIC, TECHNICAL, and ACTIONABLE daily tasks for today.\n"
                    "CRITICAL RULES:\n"
                    "1. Tasks must be DIRECTLY related to the goal.\n"
                    "2. If goal is coding, give coding tasks. If fitness, give workouts.\n"
                    "3. No generic tasks like 'Research' or 'Plan'. Be specific (e.g. 'Write a GET endpoint', 'Do 3x10 squats').\n"
                    "4. Progressive Overload: Make them slightly challenging.\n"
                    "Output STRICTLY a JSON format array of strings: ['Task 1', 'Task 2', 'Task 3']."
                )
                
                try:
                    res = rag_system.generate_json(prompt=prompt)
                    content = res['message']['content']
                    
                    print(f"DEBUG: AI Content for Daily Tasks: {content}", flush=True)
                    
                    # Clean Markdown
                    cleaned_content = content
                    if "```" in cleaned_content:
                        # Remove first ```json or ```
                        cleaned_content = cleaned_content.replace("```json", "").replace("```", "")
                    
                    import json
                    start = cleaned_content.find('[')
                    end = cleaned_content.rfind(']') + 1
                    
                    if start == -1 or end == 0:
                        raise ValueError("AI did not return a valid JSON list. Raw: " + content[:50] + "...")

                    tasks = json.loads(cleaned_content[start:end])
                    
                    for t in tasks:
                        create_daily_task(user_id, t)
                        
                    msg = f"✅ **Daily Plan Ready!**\n\nI've added {len(tasks)} tasks to your Productivity Dashboard.\n\nGo check them off! 📝"
                    save_chat_message(user_id, 'ai', msg)
                    yield msg
                except Exception as e:
                    print(f"Daily Gen Error (AI service): {e}", flush=True)
                    error_msg = f"Error: {e}"
                    save_chat_message(user_id, 'ai', error_msg)
                    yield error_msg
                except Exception as e:
                    print(f"Daily Gen Error: {e}", flush=True)
                    yield f"❌ **Error generating tasks.**\nReason: {str(e)}\n\nPlease try again."

            return Response(stream_with_context(generate_daily()), mimetype='text/plain')
        
        # /article
        if text.startswith("/article"):
            def generate_article():
                yield "📚 **Researching your personalized article...** this might take a moment... \n\n"
                
                user_goal = user[2] if user and len(user) > 2 and user[2] else "Self Improvement"
                prompt = f"User Goal: {user_goal}. Write a short, powerful motivational article (max 200 words) to help the user achieve this. \n\nCRITICAL REQUIREMENT: CITE REAL BOOKS AND AUTHORS.\nAt the end, list 2 recommended books with authors clearly. \nFormat with Markdown (Bold, Lists)."
                
                try:
                    res = rag_system.generate_response(messages=[
                         {"role": "system", "content": "You are a wise mentor and bibliophile. deeply knowledgeable."},
                         {"role": "user", "content": prompt}
                    ])
                    article_content = res['message']['content']
                    
                    # Save to DB
                    create_daily_article(user_id, article_content)
                    
                    # Send to chat
                    yield article_content
                    yield "\n\n(Added to your Daily Read box on Dashboard! 📖)"
                    
                except Exception as e:
                    print(f"Article Gen Error (AI service): {e}", flush=True)
                    error_msg = f"Error: {e}"
                    save_chat_message(user_id, 'ai', error_msg)
                    yield error_msg
                except Exception as e:
                    print(f"Article Gen Error: {e}")
                    yield "❌ **Error generating article.** Please try again."

            return Response(stream_with_context(generate_article()), mimetype='text/plain')
        
        # /news
        if text.startswith("/news"):
            def generate_news():
                yield "📰 **Fetching latest Indian headlines...**\n\n"
                
                user_goal = user[2] if user and len(user) > 2 and user[2] else "Technology"
                
                news_list = fetch_google_news(user_id, user_goal)
                
                if not news_list:
                    yield "❌ **Error fetching news.** Please try again later."
                    return

                msg = f"🇮🇳 **Top News for {user_goal}:**\n\n"
                
                for item in news_list:
                    msg += f"🔹 [{item['title']}]({item['link']}) - *{item['source']}*\n"
                
                save_chat_message(user_id, 'ai', msg)
                
                yield msg
                yield "\n\n(Added to 'Daily News' on Dashboard! 🗞️)"

            return Response(stream_with_context(generate_news()), mimetype='text/plain')



        # (Duplicate /reminder handler removed — handled above)

    # Define today for use in logic
    today = datetime.now().strftime("%Y-%m-%d")

    # --- NATURAL LANGUAGE REMINDER DETECTION ---
    # Catch phrases like "remind me to X in 10 minutes", "set a reminder for 5pm to call mom"
    import re
    reminder_patterns = [
        r'remind\s+me\s+(?:to\s+)?(.+?)\s+(?:in\s+(\d+)\s*(min|minute|hour|sec|second)s?)',
        r'remind\s+me\s+(?:to\s+)?(.+?)\s+(?:at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?)',
        r'set\s+(?:a\s+)?reminder\s+(?:for\s+)?(?:(\d+)\s*(min|minute|hour|sec|second)s?\s+(?:to\s+)?(.+))',
        r'set\s+(?:a\s+)?reminder\s+(?:for\s+)?(?:at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+(?:to\s+)?(.+))',
    ]
    
    text_lower = text.lower().strip()
    detected_reminder = None
    
    # Pattern 1: "remind me to [content] in [time]" — handles m/min/minute/h/hr/hour/s/sec/second
    m = re.search(r'remind\s+me\s+(?:to\s+)?(.+?)\s+in\s+(\d+)\s*(m(?:in(?:ute)?s?)?|h(?:(?:ou)?rs?)?|s(?:ec(?:ond)?s?)?)', text_lower)
    if m:
        r_content = m.group(1).strip()
        r_amount = int(m.group(2))
        r_unit = m.group(3)
        if r_unit.startswith('m'):
            delay_s = r_amount * 60
            time_label = f"{r_amount} minute{'s' if r_amount != 1 else ''}"
        elif r_unit.startswith('h'):
            delay_s = r_amount * 3600
            time_label = f"{r_amount} hour{'s' if r_amount != 1 else ''}"
        else:
            delay_s = r_amount
            time_label = f"{r_amount} second{'s' if r_amount != 1 else ''}"
        detected_reminder = {'content': r_content, 'delay': delay_s, 'label': time_label}
    
    # Pattern 2: "remind me to [content] at [time]"
    if not detected_reminder:
        m = re.search(r'remind\s+me\s+(?:to\s+)?(.+?)\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text_lower)
        if m:
            r_content = m.group(1).strip()
            hour = int(m.group(2))
            minute = int(m.group(3) or 0)
            meridiem = m.group(4)
            if meridiem == 'pm' and hour < 12: hour += 12
            elif meridiem == 'am' and hour == 12: hour = 0
            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            delay_s = (target - now).total_seconds()
            time_label = target.strftime("%I:%M %p")
            detected_reminder = {'content': r_content, 'delay': delay_s, 'label': time_label}
    
    # Pattern 3: "set reminder for 10 min to [content]" / "set a reminder in 5m [content]"
    if not detected_reminder:
        m = re.search(r'set\s+(?:a\s+)?reminder\s+(?:for|in)\s+(\d+)\s*(m(?:in(?:ute)?s?)?|h(?:(?:ou)?rs?)?|s(?:ec(?:ond)?s?)?)\s+(?:to\s+)?(.+)', text_lower)
        if m:
            r_amount = int(m.group(1))
            r_unit = m.group(2)
            r_content = m.group(3).strip()
            if r_unit.startswith('m'):
                delay_s = r_amount * 60
                time_label = f"{r_amount} minute{'s' if r_amount != 1 else ''}"
            elif r_unit.startswith('h'):
                delay_s = r_amount * 3600
                time_label = f"{r_amount} hour{'s' if r_amount != 1 else ''}"
            else:
                delay_s = r_amount
                time_label = f"{r_amount} second{'s' if r_amount != 1 else ''}"
            detected_reminder = {'content': r_content, 'delay': delay_s, 'label': time_label}
    
    if detected_reminder:
        r_content = detected_reminder['content']
        delay_s = detected_reminder['delay']
        time_label = detected_reminder['label']
        
        # Save in-app reminder
        trigger_at = (datetime.now() + timedelta(seconds=delay_s)).strftime("%Y-%m-%d %H:%M:%S")
        save_reminder(user_id, r_content, trigger_at)
        
        # Also schedule email if user has email
        def send_nl_reminder_email():
            import time as _time
            _time.sleep(delay_s)
            u = get_user(user_id)
            u_email = u[17] if u and len(u) > 17 else None
            u_name = u[1] if u else "Friend"
            if u_email:
                subject = f"⏰ Reminder: {r_content}"
                body = f"Hey {u_name}!\n\nHere is your reminder: '{r_content}'.\n\n- PartnerAI"
                send_email(u_email, subject, body)
        
        threading.Thread(target=send_nl_reminder_email).start()
        
        msg = f"⏰ **Reminder Set!**\n\nI'll remind you to **'{r_content}'** in **{time_label}**.\n\nYou'll get a notification right here in chat when it's time! 🔔"
        save_chat_message(user_id, 'ai', msg)
        return Response(msg, mimetype='text/plain')


    # --- PARTNER AI CHAT ---
    try:
        # Mentor Persona Prompt
        # --- DYNAMIC PERSONA GENERATION ---
        goal = user[2] if user and len(user) > 2 and user[2] else "General Productivity"
        
        # safely get other fields by index from your schema
        # Schema: 0:id, 1:name, 2:career(goal), 3:hobbies, ..., 11:work_time, 12:free_time, 13:age
        work_time = user[11] if len(user) > 11 else "Unspecified"
        free_time = user[12] if len(user) > 12 else "Unspecified"
        age = user[13] if len(user) > 13 else "Unspecified"

        # --- RLHF STRATEGY SELECTION ---
        selected_strategy = StrategySelector.get_best_strategy()
        strategy_instruction = StrategySelector.get_prompt_instruction(selected_strategy)
        print(f"DEBUG: Selected RLHF Strategy: {selected_strategy}", flush=True)

        # ── Build domain-specific coaching persona ──────────────────────────────
        goal_lower = goal.lower()
        if any(k in goal_lower for k in ['fitness','gym','workout','muscle','weight','fat','body']):
            persona = (
                f"You are a real fitness coach for {name}. "
                "You talk like a human — short, direct, real. No bullet-point lectures. "
                "You ask ONE question at a time to understand where they are. "
                "You give small concrete next steps, not big overwhelming plans. "
                "You know that motivation is unreliable — you coach discipline and identity. "
                "You mix tough love with genuine care. You never judge."
            )
        elif any(k in goal_lower for k in ['code','coding','python','programming','software','developer','web','app']):
            persona = (
                f"You are a senior developer and mentor for {name}. "
                "You talk like a real teammate, not a textbook. "
                "You give working code snippets when helpful, but keep explanations tight. "
                "You debug thinking patterns, not just code bugs. "
                "You ask what they've already tried before giving answers. "
                "You celebrate small wins — shipping matters more than perfection."
            )
        elif any(k in goal_lower for k in ['business','startup','entrepreneur','freelance','money','income']):
            persona = (
                f"You are a business mentor for {name}. "
                "You've seen startups succeed and fail — you speak from experience. "
                "You cut through overthinking with real questions like 'Who is your first customer?' "
                "You focus on revenue and traction first, strategy second. "
                "You're direct but never dismissive of their ideas."
            )
        elif any(k in goal_lower for k in ['study','exam','college','university','learn','course']):
            persona = (
                f"You are a study coach and academic mentor for {name}. "
                "You understand burnout, procrastination, and exam anxiety from the inside. "
                "You use evidence-based techniques (spaced repetition, active recall) naturally. "
                "You keep sessions short and focused. You ask about energy levels, not just schedules."
            )
        else:
            persona = (
                f"You are a personal growth mentor for {name}. "
                "You talk naturally — like a coach who genuinely knows them. "
                "You ask one good question at a time. You give real, specific advice. "
                "You help them build habits and momentum, not just motivation spikes."
            )

        # ── Core system prompt ───────────────────────────────────────────────────
        system_prompt = f"""{persona}

USER CONTEXT:
- Name: {name}, Age: {age}
- Main goal: {goal}
- Available time: free {free_time}, works {work_time}
- Coaching style this session: {strategy_instruction}

CONVERSATION RULES (follow naturally, don't state them):
- You remember everything from this conversation. Reference it when relevant.
- Never repeat the same advice twice. If you already covered something, build on it.
- Keep responses conversational — 2 to 5 sentences max unless they ask for a plan or detail.
- Never start with "Great!", "Absolutely!", "Of course!" or similar filler openers.
- Ask at most ONE question per reply. Make it specific and useful.
- IMPORTANT: When you ask ANY question, you MUST end your reply with [OPTIONS: choice1 | choice2 | choice3] on a new line. This creates clickable buttons for the user. Examples:
  - Yes/no question → [OPTIONS: Yes | No | Tell me more]
  - Choice question → [OPTIONS: Option A | Option B | Option C]
  - Open question → [OPTIONS: Help me decide | I'm not sure | Skip this]
  Never skip this. Always include 2-4 options.
- Use plain text. No markdown headers (#, ##). Bold is fine for key words.
- If they say they're tired, struggling, or failing — acknowledge it first before coaching.
- Never lecture. Never moralize. Give the next smallest step forward."""

        # ── RAG Context Injection ────────────────────────────────────────────────
        try:
            rag_context = build_rag_context(user_id, text, user_goal=goal)
            if rag_context:
                system_prompt += "\n\n" + rag_context
        except Exception as _rag_err:
            print(f"DEBUG: RAG context error (non-fatal): {_rag_err}", flush=True)

        # ── Extract user memory in background (non-blocking) ─────────────────────
        threading.Thread(
            target=maybe_extract_memory,
            args=(user_id, text),
            daemon=True,
        ).start()

        # ── Load recent conversation memory (last 12 turns) ──────────────────────
        raw_history = get_chat_history(user_id, limit=14)
        # Exclude the message we just saved (last entry = current user msg)
        # Convert role 'ai' → 'assistant' for the LLM
        history_messages = []
        for h in raw_history[:-1]:  # exclude just-saved current message
            role = 'assistant' if h['role'] == 'ai' else 'user'
            content = h['content']
            # skip empty or very long command outputs to save context
            if content and len(content.strip()) > 0 and not content.startswith('📊') and len(content) < 1200:
                history_messages.append({"role": role, "content": content})
        # Cap to last 10 turns to stay within context window
        history_messages = history_messages[-10:]

        # ── Build messages array: system + history + current ─────────────────────
        messages_to_send = (
            [{"role": "system", "content": system_prompt}]
            + history_messages
            + [{"role": "user", "content": text}]
        )

        print(f"DEBUG: Sending {len(messages_to_send)} messages to LLM (strategy={selected_strategy})", flush=True)

        # ── Streaming response ────────────────────────────────────────────────────
        full_text_accumulator = []
        _uid = user_id          # capture for closure
        _user_text = text       # capture for closure
        _user_goal = goal       # capture for closure

        def stream_chat_response():
            for token in rag_system.generate_response_stream(messages=messages_to_send):
                full_text_accumulator.append(token)
                yield token
            # Save full reply to history
            ai_reply = ''.join(full_text_accumulator)
            save_chat_message(_uid, 'ai', ai_reply)
            # Extract actionable tasks in background (non-blocking)
            threading.Thread(
                target=_extract_tasks_from_chat,
                args=(_uid, _user_text, ai_reply, _user_goal),
                daemon=True,
            ).start()

        return Response(stream_with_context(stream_chat_response()), mimetype='text/plain')
        
    except AIConnectionError as e:
        print(f"Chat AIConnectionError: {e}", flush=True)
        return Response(_OFFLINE_MSG, mimetype='text/plain')
    except Exception as e:
        print(f"Chat Error: {e}", flush=True)
        return Response("I'm having a bit of trouble connecting to my brain right now. 🧠", mimetype='text/plain')

# --- REMINDER NOTIFICATION API ---
@app.route('/api/reminders/check', methods=['GET'])
def check_reminders():
    """Check for pending reminders that have fired"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'reminders': []})
    
    pending = get_pending_reminders(user_id)
    return jsonify({'reminders': pending})

@app.route('/api/reminders/dismiss', methods=['POST'])
def dismiss_reminder_api():
    """Dismiss a fired reminder"""
    data = request.json
    reminder_id = data.get('id')
    if reminder_id:
        dismiss_reminder(reminder_id)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Missing id'}), 400

# --- RLHF FEEDBACK API ---
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    user_input = data.get('user_input')
    ai_response = data.get('ai_response')
    strategy = data.get('strategy')
    feedback = data.get('feedback') # "very_helpful", "helpful", "not_helpful"
    
    if not all([user_input, ai_response, strategy, feedback]):
        return jsonify({"error": "Missing fields"}), 400
        
    result = FeedbackManager.process_feedback(user_input, ai_response, strategy, feedback)
    return jsonify(result)


# --- AI RECOMMENDED TASKS (old manual generate removed — tasks come from chat now) ---

# --- SETTINGS & PROFILE (Moved from nested) ---
@app.route('/settings')
def settings_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('settings.html')

@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    if request.method == 'GET':
        user = get_user(user_id)
        return jsonify({
            'name': user[1],
            'career': user[2],
            'hobbies': user[3],
            'daily_topic': user[10],
            'work_time': user[11],
            'free_time': user[12],
            'age': user[13]
        })
        
    data = request.json
    save_user(
        user_id,
        name=data.get('name'),
        career=data.get('career'),
        hobbies=data.get('hobbies'),
        daily_topic=data.get('daily_topic'),
        work_time=data.get('work_time'),
        free_time=data.get('free_time'),
        age=data.get('age')
    )
    return jsonify({'success': True})

@app.route('/api/init')
def init_chat():
    user_id = session.get('user_id')
    print(f"DEBUG: init_chat called. Session user_id={user_id}", flush=True)
    
    if not user_id:
        return jsonify({'is_new_user': True, 'history': []})

    user = get_user(user_id)
    if not user: 
        print(f"DEBUG: User {user_id} not found in DB", flush=True)
        return jsonify({'is_new_user': True, 'history': []})
    
    try: name = user[1]
    except: name = "Friend"
    
    # Fetch History
    history = get_chat_history(user_id)
    print(f"DEBUG: Retrieved {len(history)} messages for user {user_id}", flush=True)
    
    return jsonify({
        'is_new_user': False, 
        'name': name,
        'history': history 
    })

@app.route('/collection')
def collection_page():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('collection.html')

@app.route('/api/reward', methods=['POST'])
def save_reward():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    # Random Landscape Logic
    import random
    landscapes = ['Santorini', 'Aurora', 'Sahara', 'Amazon', 'Fuji', 'Alps', 'Lavender', 'Maldives', 'Tuscany', 'Patagonia']
    
    # Allow client to suggest, but default to random
    data = request.json or {}
    forced_type = data.get('type')
    duration = data.get('duration', 25)  # Get actual duration or default to 25
    
    if forced_type and forced_type in landscapes:
        reward_type = forced_type
    else:
        reward_type = random.choice(landscapes)
        
    add_reward(session['user_id'], reward_type, duration)
    
    return jsonify({
        'success': True, 
        'reward': reward_type, 
        'name': reward_type
    })

@app.route('/api/rewards')
def get_user_rewards():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    rewards = get_rewards(session['user_id'])
    return jsonify(rewards)

@app.route('/api/songs')
def get_songs():
    song_dir = os.path.join(os.getcwd(), 'song')
    if not os.path.exists(song_dir): return jsonify([])
    songs = [f for f in os.listdir(song_dir) if f.endswith('.mp3')]
    return jsonify(songs)

@app.route('/songs/<path:filename>')
def serve_song(filename):
    song_dir = os.path.join(os.getcwd(), 'song')
    print(f"DEBUG: Requested song: {filename}, in dir: {song_dir}", flush=True)
    if not os.path.exists(os.path.join(song_dir, filename)):
        print(f"ERROR: File not found: {filename}", flush=True)
        return "File not found", 404
    return send_from_directory(song_dir, filename)

    return send_from_directory(song_dir, filename)

@app.route('/api/daily', methods=['GET'])
def get_daily_tasks_api():
    if 'user_id' not in session: return jsonify([]), 401
    user_id = session['user_id']
    
    # Check if we need to inject flow tasks
    import flow_content
    tasks = get_daily_tasks(user_id)
    
    if not tasks:
        # No tasks for today, let's see if we are in the flow
        try:
            day = get_flow_day(user_id)
            if day <= 14:
                flow_tasks = flow_content.get_day_content(day)
                if flow_tasks:
                    for t in flow_tasks:
                        create_daily_task(user_id, t)
                    # Re-fetch
                    tasks = get_daily_tasks(user_id)
                    
                    # Notify user only if it's a new day generation
                    msg = f"🌅 **Day {day} of 14**\n\nGood morning! Here are your missions for today. Let's keep the momentum going! 🚀"
                    save_chat_message(user_id, 'ai', msg)
        except Exception as e:
            print(f"Flow Logic Error: {e}")
            
    return jsonify(tasks)

@app.route('/api/clear_chat', methods=['POST'])
def clear_chat_api():
    """Clear all chat messages for the current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Clear chat history from database
        clear_chat_history(session['user_id'])
        return jsonify({'success': True, 'message': 'Chat history cleared'})
    except Exception as e:
        print(f"Error clearing chat: {e}", flush=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily/<int:task_id>/toggle', methods=['POST'])
def toggle_daily_task_api(task_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    toggle_daily_task(task_id, data.get('status'))
    
    # Check for flow progression
    status = data.get('status')
    if status:
        # Check if ALL daily tasks are done
        tasks = get_daily_tasks(session['user_id'])
        if all(t['is_completed'] for t in tasks):
             # Increment flow day
             try:
                 day = get_flow_day(session['user_id'])
                 if day <= 14:
                     increment_flow_day(session['user_id'])
                     msg = f"🎉 **Day {day} Complete!**\n\nFantastic work! You've conquered today's missions. Get ready for Day {day+1} tomorrow! 🌟"
                     save_chat_message(session['user_id'], 'ai', msg)
             except Exception as e:
                 print(f"Flow Increment Error: {e}")

    return jsonify({'success': True})

@app.route('/api/daily/complete', methods=['POST'])
def complete_daily_tasks_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    # Send congratulatory message
    user_name = session.get('user_name', 'Champ')
    msg = f"🏆 **Victory!** 🏆\n\nOutstanding work, {user_name}! You crushed your daily tasks today. \n\nKeep this momentum going! 🔥"
    save_chat_message(session['user_id'], 'ai', msg)
    
    return jsonify({'success': True})

@app.route('/api/article', methods=['GET'])
def get_daily_article_api():
    if 'user_id' not in session: return jsonify({'content': None}), 401
    content = get_latest_article(session['user_id'])
    content = get_latest_article(session['user_id'])
    return jsonify({'content': content})

def fetch_google_news(user_id, goal):
    """Fetch and save news for a user based on their goal"""
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET
    import json
    
    try:
        query = urllib.parse.quote(f"{goal} India")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        print(f"DEBUG: Fetching news for {goal} from {rss_url}", flush=True)
        
        with urllib.request.urlopen(rss_url) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            items = root.findall('.//item')[:5] # Top 5
            news_list = []
            
            for item in items:
                title = item.find('title').text
                link = item.find('link').text
                pubDate = item.find('pubDate').text
                
                # Clean title
                clean_title = title.rsplit('-', 1)[0].strip()
                source = title.rsplit('-', 1)[1].strip() if '-' in title else "News"
                
                news_list.append({'title': clean_title, 'link': link, 'source': source, 'date': pubDate})

            save_daily_news(user_id, json.dumps(news_list))
            return news_list
            
    except Exception as e:
        print(f"News Auto-Fetch Error: {e}", flush=True)
        return []

@app.route('/api/news', methods=['GET'])
def get_daily_news_api():
    if 'user_id' not in session: return jsonify({'news': []}), 401
    user_id = session['user_id']
    
    news_json = get_daily_news(user_id)
    
    import json
    news = []
    
    if news_json:
        try:
            news = json.loads(news_json)
        except:
            news = []
            
    if not news:
        # Auto-fetch if missing
        user = get_user(user_id)
        goal = user[2] if user and len(user) > 2 and user[2] else "Technology"
        news = fetch_google_news(user_id, goal)
        
    return jsonify({'news': news})

# --- HABITS API ROUTE ---

@app.route('/api/habits', methods=['GET', 'POST'])
def manage_habits():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        category = data.get('category', 'General')
        icon = data.get('icon', '📝')
        time_of_day = data.get('time_of_day', 'Anytime')
        
        if not title: return jsonify({'error': 'Title required'}), 400
        
        habit_id = create_habit(user_id, title, category, icon, time_of_day)
        return jsonify({'id': habit_id, 'status': 'created'})
        
    else:
        habits = get_user_habits(user_id)
        return jsonify(habits)

@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
def remove_habit(habit_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    from habits_db import delete_habit
    success = delete_habit(habit_id, session['user_id'])
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Habit not found or unauthorized'}), 404

@app.route('/api/habits/<int:habit_id>/toggle', methods=['POST'])
def toggle_habit_route(habit_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    completed = toggle_habit(habit_id, user_id)
    return jsonify({'id': habit_id, 'completed': completed})

@app.route('/api/habits/stats', methods=['GET'])
def habit_stats():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    stats = get_weekly_stats(user_id)
    return jsonify(stats)

@app.route('/api/habits/analyze', methods=['GET'])
def ai_habit_analysis():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    insight = analyze_habits_ai(user_id)
    return jsonify({'insight': insight})

def suggest_habits():
    """AI-powered habit suggestions based on user's goal"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    user = get_user(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's goal and context
    name = user[1]
    goal = user[2] if user[2] else "Personal Growth"
    age = user[16] if len(user) > 16 and user[16] else "Not specified"
    work_time = user[14] if len(user) > 14 and user[14] else "Not specified"
    free_time = user[15] if len(user) > 15 and user[15] else "Not specified"
    
    # AI Prompt for habit suggestions
    prompt = f"""User Profile:
- Name: {name}
- Goal: {goal}
- Age: {age}
- Work Schedule: {work_time}
- Free Time: {free_time}

Task: Suggest 5 specific, actionable daily habits that would help achieve their goal: "{goal}"

Requirements:
1. Make habits specific and achievable
2. Consider their schedule
3. Mix physical, mental, and skill-building habits
4. Keep each habit simple (5-30 minutes)

Output ONLY valid JSON array (no markdown):
[
    {{"name": "Habit Name", "description": "Why this helps", "frequency": "daily", "time": "10 min"}},
    ...
]"""
    
    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are a habit formation expert. Return ONLY valid JSON, no markdown formatting."},
            {"role": "user", "content": prompt}
        ], format='json')
        
        content = response['message']['content']
        
        # Clean up markdown if AI adds it
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()
        
        # Extract JSON
        start = content.find('[')
        end = content.rfind(']') + 1
        
        if start == -1 or end == 0:
            # Fallback suggestions
            suggestions = [
                {"name": "Morning Reflection", "description": "Start your day with clarity", "frequency": "daily", "time": "10 min"},
                {"name": "Focused Learning", "description": "Dedicate time to skill development", "frequency": "daily", "time": "30 min"},
                {"name": "Evening Review", "description": "Track progress and plan tomorrow", "frequency": "daily", "time": "10 min"}
            ]
        else:
            suggestions = json.loads(content[start:end])
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        print(f"AI Habit Suggestion Error: {e}", flush=True)
        # Return fallback suggestions
        return jsonify({'suggestions': [
            {"name": "Daily Goal Review", "description": f"Reflect on progress toward: {goal}", "frequency": "daily", "time": "10 min"},
            {"name": "Skill Practice", "description": "Practice key skills for your goal", "frequency": "daily", "time": "20 min"},
            {"name": "Progress Journaling", "description": "Document wins and learnings", "frequency": "daily", "time": "10 min"}
        ]})

from memory import get_db

def save_habit_insights(user_id, insights):
    """Save insights to ai_user_memory"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = json.dumps(insights)
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if exists
        cursor.execute("SELECT id FROM ai_user_memory WHERE user_id=? AND memory_key='habit_insight'", (user_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("UPDATE ai_user_memory SET memory_value=?, last_updated=? WHERE id=?", 
                          (value, timestamp, row[0]))
        else:
            cursor.execute("INSERT INTO ai_user_memory (user_id, memory_key, memory_value, last_updated) VALUES (?, 'habit_insight', ?, ?)",
                          (user_id, value, timestamp))
        conn.commit()

@app.route('/api/habits/insights', methods=['GET', 'POST'])
def get_habit_insights():
    """AI-generated insights about habit patterns (Persisted)"""
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    # GET: Retrieve stored insight
    if request.method == 'GET':
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT memory_value FROM ai_user_memory WHERE user_id=? AND memory_key='habit_insight'", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return jsonify(json.loads(row[0]))
            else:
                return jsonify({}) # Empty means frontend will show default or ask to update

    # POST: Generate NEW insight
    data = request.json
    habits = data.get('habits', [])
    stats = data.get('stats', {})
    
    user = get_user(user_id)
    if not user: return jsonify({'error': 'User not found'}), 404
    
    goal = user[2] if user[2] else "Personal Growth"
    
    # Analyze habit data
    habit_names = [h.get('name', '') for h in habits[:5]]  
    current_streak = stats.get('currentStreak', 0)
    completion_rate = stats.get('completionRate', 0)
    
    prompt = f"""Analyze this habit tracking data:
User Goal: {goal}
Active Habits: {', '.join(habit_names)}
Current Streak: {current_streak} days
Completion Rate: {completion_rate}%

Provide brief insights:
1. Pattern: Observation (1 sentence)
2. Tip: Motivation (1 sentence)
3. Recommendation: Specific action (1 sentence)

Output JSON: {{"pattern": "...", "tip": "...", "recommendation": "..."}}"""
    
    # Initialize row to None to avoid UnboundLocalError in finally/except block
    row = None

    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are a supportive habit coach. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ])
        
        content = response['message']['content']
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()
        
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start != -1 and end > 0:
            insights = json.loads(content[start:end])
            # SAVE to DB
            save_habit_insights(user_id, insights)
            return jsonify(insights)
        else:
            return jsonify({})
            
    except Exception as e:
        print(f"AI Error: {e}")
        # Fallback to stored if available
        # logic for row retrieval was not here, so just return empty
        return jsonify({})

# ==========================================
# KNOWLEDGE BLOCKS API
# ==========================================
from knowledge_db import create_knowledge_block, get_user_knowledge_blocks, delete_knowledge_block, get_knowledge_block, update_knowledge_block

@app.route('/api/knowledge/update', methods=['POST'])
def update_knowledge_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    block_id = data.get('id')
    
    if not block_id: return jsonify({'error': 'Missing ID'}), 400
    
    update_knowledge_block(
        session['user_id'],
        block_id,
        title=data.get('title'),
        content=data.get('content'),
        type=data.get('type'),
        tags=data.get('tags'),
        meta=data.get('meta')
    )
    return jsonify({'success': True})

@app.route('/api/knowledge', methods=['GET', 'POST'])
def knowledge_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    if request.method == 'GET':
        type_filter = request.args.get('type', 'all')
        blocks = get_user_knowledge_blocks(user_id, type_filter)
        return jsonify(blocks)
        
    if request.method == 'POST':
        data = request.json
        block_id = create_knowledge_block(
            user_id, 
            data.get('type', 'idea'),
            data.get('title', 'Untitled'),
            data.get('content', ''),
            data.get('tags', []),
            data.get('meta', {})
        )
        return jsonify({'id': block_id, 'status': 'success'})

@app.route('/knowledge/<int:block_id>')
def knowledge_detail(block_id):
    if 'user_id' not in session: return redirect('/login')
    
    block = get_knowledge_block(session['user_id'], block_id)
    if not block: return "Block not found", 404
    
    return render_template('knowledge_detail.html', block=block, active_page='workspace')

@app.route('/api/knowledge/<int:block_id>', methods=['DELETE'])
def delete_knowledge_api(block_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    delete_knowledge_block(session['user_id'], block_id)
    return jsonify({'status': 'deleted'})

@app.route('/api/knowledge/insight', methods=['POST'])
def knowledge_insight():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    # Get recent blocks to analyze
    blocks = get_user_knowledge_blocks(session['user_id'])[:10]
    block_summary = "\n".join([f"- [{b['type']}] {b['title']}: {b['content'][:50]}..." for b in blocks])
    
    prompt = f"""Analyze these knowledge blocks and suggest a connection:
{block_summary}

Task: Identify 2 related blocks that should be linked.
Return JSON: {{"source_id": 123, "target_id": 456, "reason": "Both discuss..."}}
If no strong connection, return empty JSON {{}}."""

    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are a knowledge architect. JSON only."},
            {"role": "user", "content": prompt}
        ], format='json')
        content = response['message']['content']
        # Clean markdown
        if "```" in content: content = content.replace("```json", "").replace("```", "").strip()
        
        return jsonify(json.loads(content))
    except Exception as e:
        print(f"AI Link Error: {e}")
        return jsonify({})

@app.route('/api/knowledge/analyze-block', methods=['POST'])
def analyze_block_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    block_id = data.get('block_id')
    block = get_knowledge_block(session['user_id'], block_id)
    
    if not block: return jsonify({'error': 'Block not found'}), 404
    
    prompt = f"""Analyze this knowledge block content:
Title: {block['title']}
Content: {block['content']}

Provide a structured analysis in JSON format with these keys:
- "summary": A concise one-sentence summary.
- "actions": A list of 3 concrete next steps or actionable ideas.
- "tags": A list of 3-5 relevant tags.
- "insight": A deeper philosophical or strategic insight related to this.

Return ONLY valid JSON."""

    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are a strategic mentor. Output JSON only."},
            {"role": "user", "content": prompt}
        ], format='json')
        content = response['message']['content']
        # Clean markdown
        if "```" in content: content = content.replace("```json", "").replace("```", "").strip()
        
        return jsonify(json.loads(content))
    except Exception as e:
        print(f"AI Analyze Error: {e}")
        return jsonify({'error': 'AI Analysis failed'})


@app.route('/api/knowledge/ai-assist', methods=['POST'])
def knowledge_ai_assist():
    """AI writing assistant for the block editor."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data    = request.json
    title   = data.get('title', '')
    content = data.get('content', '')
    mode    = data.get('mode', 'improve')

    mode_prompts = {
        'improve':  (
            f"Rewrite this text to be clearer, more insightful, and better structured:\n"
            f"Title: {title}\n{content}\n\nReturn ONLY the improved version, no commentary."
        ),
        'summarize': (
            f"Summarize the following in 2-3 clear sentences:\n"
            f"Title: {title}\n{content}\n\nReturn ONLY the summary."
        ),
        'expand': (
            f"Expand on this idea with more detail, examples, and context:\n"
            f"Title: {title}\n{content}\n\nReturn ONLY the expanded version."
        ),
        'actions': (
            f"Extract 3-5 specific, actionable next steps from this:\n"
            f"Title: {title}\n{content}\n\nReturn as a numbered list only."
        ),
        'tags': (
            f"Suggest 5 short, relevant tags for this knowledge block:\n"
            f"Title: {title}\n{content}\n\nReturn as comma-separated tags only (e.g. productivity, habits, mindset)."
        ),
    }

    prompt = mode_prompts.get(mode, mode_prompts['improve'])

    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are a knowledge assistant. Be concise and directly useful."},
            {"role": "user", "content": prompt}
        ])
        result = response['message']['content']
        return jsonify({'result': result.strip()})
    except Exception as e:
        print(f"AI Assist Error: {e}", flush=True)
        return jsonify({'error': 'AI server unavailable. Start the LLM server and try again.'}), 503



def debug_habits():
    """Debug endpoint to verify DB state for current user"""
    if 'user_id' not in session: 
        return jsonify({'error': 'Not logged in', 'session': dict(session)})
        
    user_id = session.get('user_id')
    today = datetime.now().strftime("%Y-%m-%d")
    
    debug_info = {
        'user_id': user_id,
        'server_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'today_str': today,
        'habits': []
    }
    
    try:
        from memory import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            habits = cursor.execute("SELECT id, title FROM habits WHERE user_id=?", (user_id,)).fetchall()
            for h in habits:
                h_id = h[0]
                # Get ALL completions for this habit (any date)
                all_comps = cursor.execute("SELECT date_str FROM habit_completions WHERE habit_id=?", (h_id,)).fetchall()
                
                # Get TODAY completions
                today_comps = cursor.execute("SELECT * FROM habit_completions WHERE habit_id=? AND date_str=?", (h_id, today)).fetchall()
                
                debug_info['habits'].append({
                    'id': h_id,
                    'title': h[1],
                    'is_completed_today_check': len(today_comps) > 0,
                    'today_completion_count': len(today_comps),
                    'all_completions_dates': [c[0] for c in all_comps]
                })
    except Exception as e:
        debug_info['error'] = str(e)
        
    return jsonify(debug_info)

@app.route('/api/wallpapers')
def get_wallpapers():
    wp_dir = os.path.join(os.getcwd(), 'wallpaper')
    if not os.path.exists(wp_dir): return jsonify([])
    # List valid images
    wps = [f for f in os.listdir(wp_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return jsonify(wps)

@app.route('/wallpaper/<path:filename>')
def serve_wallpaper(filename):
    wp_dir = os.path.join(os.getcwd(), 'wallpaper')
    return send_from_directory(wp_dir, filename)


# --- GROUP / TEAM ROUTES ---

@app.route('/api/group/status')
def group_status_api():
    if 'user_id' not in session: return jsonify({'in_group': False})
    
    user_id = session['user_id']
    group = get_user_group(user_id)
    
    if not group:
         return jsonify({'in_group': False})
    
    # group: id, name, leader_id, status, goal
    group_id = group[0]
    tasks = get_group_tasks(group_id)
    # tasks: id, group_id, assigned_user_id, task_content, status
    
    task_list = [{
        'id': t[0],
        'assigned_to': t[2], # user_id
        'assigned_user_id': t[2],
        'content': t[3],
        'status': t[4]
    } for t in tasks]
    
    return jsonify({
        'in_group': True,
        'name': group[1],
        'status': group[3],
        'is_leader': (group[2] == user_id),
        'tasks': task_list
    })

@app.route('/api/group/create_or_join', methods=['POST'])
def group_create_join_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    action = data.get('action')
    user_id = session['user_id']
    
    if action == 'create':
        name = data.get('name', 'New Squad')
        goal = data.get('goal', 'General')
        group_id = create_group(name, user_id, goal)
        return jsonify({'success': True, 'group_id': group_id})
    
    if action == 'join':
        # Try to join group 1 by default for demo
        # Or create if fails
        success = join_group(1, user_id)
        if not success:
             create_group("Alpha Squad", user_id, "General Excellence")
        return jsonify({'success': True})

    if action == 'invite':
        # Add a mock user or existing user
        # For local demo, we just add "User 2" (id=2) or "User 3" (id=3)
        # Check if they exist?
        target_name = data.get('username') # e.g. "User 2"
        # We need a way to find user ID by name or just hardcode for demo
        # Let's assume user passes an ID or we create a dummy user
        target_id = int(data.get('target_id', 0))
        if target_id == 0:
             # Basic invite logic: invite User 2 if I am User 1
             target_id = 2 if user_id == 1 else 1
        
        group = get_user_group(user_id)
        if group:
            join_group(group[0], target_id)
            return jsonify({'success': True, 'message': f'Invited User {target_id}'})
        
    return jsonify({'error': 'Invalid action'})

@app.route('/api/group/chat', methods=['GET', 'POST'])
def group_chat_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    group = get_user_group(user_id)
    if not group: return jsonify({'error': 'No group'}), 400
    group_id = group[0]

    if request.method == 'GET':
        msgs = get_group_messages(group_id)
        return jsonify(msgs)

    if request.method == 'POST':
        data = request.json
        content = data.get('content')
        if not content: return jsonify({'error': 'Empty'}), 400
        
        # Save User Msg
        save_group_message(group_id, user_id, 'user', content)
        
        # AI Logic: Respond to everyone or specific questions
        def ai_reply():
            # fetch context
            history = get_group_messages(group_id, limit=10)
            chat_log = []
            for m in history:
                role = "assistant" if m['role'] == 'ai' else "user"
                chat_log.append({"role": role, "content": f"{m['user_name']}: {m['content']}"})
            
            # --- NEW PROMPT INJECTION ---
            prompt = (
                "You are PartnerAI, an AI Group Manager that behaves like a calm, intelligent HR manager and project coordinator.\n"
                "Your job is to manage group chats where humans work together toward shared goals.\n\n"
                f"Current Group: '{group[1]}'\n"
                f"Shared Goal: '{group[4]}'\n\n"
                "You MUST follow these principles:\n"
                "- Be supportive, fair, and motivating\n"
                "- Never shame or insult users\n"
                "- Act like an HR + Project Manager + Mentor\n"
                "- Focus on productivity, clarity, and teamwork\n\n"
                "When a user completes a task (checks in), praise briefly and check overall group progress.\n"
                "If a user is delayed, ask politely for the reason and offer help.\n"
                "Keep responses short, clear, and professional. No emojis unless user uses them.\n"
                "You are NOT a chatbot. You are a Team Productivity Partner."
            )
            
            try:
                # Use local_llm (Model ignored, server uses loaded model)
                res = rag_system.generate_response(messages=[
                    {"role": "system", "content": prompt},
                    *chat_log
                ])
                reply = res['message']['content']
                save_group_message(group_id, 0, 'ai', reply) # User 0 = AI
            except Exception as e:
                print(f"Group AI Error: {e}")

        # Trigger AI ONLY if mentioned OR if text looks like a status update ("done", "finished")
        trigger_words = ["@mentor", "partnerai", "done", "finished", "check in", "completed"]
        if any(w in content.lower() for w in trigger_words):
            threading.Thread(target=ai_reply).start()
        
        return jsonify({'success': True})

@app.route('/api/group/set_goal', methods=['POST'])
def group_set_goal_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    group = get_user_group(user_id)
    if not group: return jsonify({'error': 'No group'}), 400
    
    data = request.json
    goal = data.get('goal')
    
    # 1. Save Goal
    set_group_goal(group[0], goal)
    
    # 2. AI Agent creates tasks (HR Manager Style)
    def bg_assign():
        members = get_group_members(group[0]) # list of user_ids
        
        # Generate tasks via LLM with HR Persona
        prompt = (
            f"You are PartnerAI, an expert Project Manager. \n"
            f"Team Goal: {goal}. Team Size: {len(members)}. \n"
            "Action: Break this goal into clear, actionable, human-sized tasks. \n"
            f"Create exactly {len(members)} tasks (one per person). \n"
            "Format: Output ONLY a JSON Array of strings. Example: [\"User 1: Design UI\", \"User 2: Setup DB\"]. "
            "Do not use keys, just strings describing the task."
        )
        
        try:
            res = rag_system.generate_response(messages=[
                {"role": "system", "content": "You are a Team Lead. Output strictly valid JSON array."},
                {"role": "user", "content": prompt}
            ])
            import json
            content = res['message']['content']
            
            # Cleaning
            if "```" in content: content = content.replace("```json", "").replace("```", "")
            
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1:
                tasks = json.loads(content[start:end])
                
                # Distribute
                for i, task_str in enumerate(tasks):
                    # Round robin assign
                    uid = members[i % len(members)]
                    # Remove "User X:" prefix if AI added it, to prevent redundancy
                    clean_task = task_str.split(':')[-1].strip() if ":" in task_str else task_str
                    add_group_task(group[0], uid, clean_task)
            
        except Exception as e:
            print(f"Group AI Error: {e}")
            
    threading.Thread(target=bg_assign).start()
    
    return jsonify({'success': True, 'message': 'PartnerAI is organizing the team...'})

@app.route('/api/group/update', methods=['POST'])
def group_update_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    group = get_user_group(user_id)
    if not group: return jsonify({'error': 'No group'}), 400
    
    # Check permissions? Assume leader only usually, but let's allow all for collaboration today
    data = request.json
    name = data.get('name')
    goal = data.get('goal')
    
    update_group(group[0], name, goal)
    return jsonify({'success': True})

@app.route('/api/group/ask_mentor', methods=['POST'])
def ask_mentor_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    group = get_user_group(user_id) # Optional context
    
    data = request.json
    question = data.get('question')
    
    # Use Main Model (Mistral) for private mentorship
    context = ""
    if group:
        context = f"User is in Squad '{group[1]}' with Goal '{group[4]}'. "
    
    prompt = (
        f"You are a Private Mentor. {context}"
        f"User asks: {question}\n"
        "Provide a direct, helpful, and supportive answer."
    )
    
    # Switch to GROUP_MODEL (Phi3) for speed as requested ("taking more time")
    # even though earlier they asked for Mistral. Responsiveness > Model Size for chat widgets.
    def generate():
        res = rag_system.generate_response(messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ])
        # Non-streaming fallback for now
        yield res['message']['content']

    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/api/group/complete_task', methods=['POST'])
def group_complete_task_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    complete_group_task(data.get('task_id'))
    return jsonify({'success': True})

# === TEAM COLLABORATION API ENDPOINTS ===

@app.route('/api/group/create', methods=['POST'])
def create_group_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    data = request.json
    
    # Check if user already has a group
    existing_group = get_user_group(user_id)
    if existing_group:
        return jsonify({'success': True, 'group_id': existing_group[0], 'existing': True})
    
    # Create new group
    name = data.get('name', 'My Team')
    goal = data.get('goal', '')
    
    group_id = create_group(name, user_id, goal)
    
    return jsonify({'success': True, 'group_id': group_id})

@app.route('/api/group/set-project', methods=['POST'])
def set_project_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    user_id = session['user_id']
    
    # Get user's group
    group = get_user_group(user_id)
    if not group:
        return jsonify({'error': 'No group found'}), 404
    
    group_id = group[0]
    project_name = data.get('project_name')
    deadline = data.get('deadline')
    goal = data.get('goal')
    
    # Update project details
    set_group_project(group_id, project_name, deadline)
    if goal:
        set_group_goal(group_id, goal)
    
    return jsonify({'success': True, 'group_id': group_id})

@app.route('/api/group/invite', methods=['GET'])
def get_invite_link():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    # Get user's group
    group = get_user_group(user_id)
    if not group:
        return jsonify({'error': 'No group found'}), 404
    
    group_id = group[0]
    invite_code = get_or_create_invite_code(group_id)
    
    # Create full invite link
    base_url = request.host_url.rstrip('/')
    invite_link = f"{base_url}/join/{invite_code}"
    
    return jsonify({'invite_code': invite_code, 'invite_link': invite_link})

@app.route('/join/<invite_code>')
def join_by_code(invite_code):
    if 'user_id' not in session:
        # Save invite code in session and redirect to login
        session['pending_invite'] = invite_code
        return redirect('/login')
    
    user_id = session['user_id']
    group_id = join_group_by_invite(invite_code, user_id)
    
    if not group_id:
        return render_template('error.html', message='Invalid or expired invite code')
    
    return redirect('/group')

@app.route('/api/group/ai-assign-tasks', methods=['POST'])
def ai_assign_tasks():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    # Get user's group with details
    group = get_user_group(user_id)
    if not group:
        return jsonify({'error': 'No group found'}), 404
    
    group_id = group[0]
    goal = group[4] if len(group) > 4 else None
    
    if not goal:
        return jsonify({'error': 'Please set a team goal first'}), 400
    
    # Get members
    members = get_group_members(group_id)
    if len(members) == 0:
        return jsonify({'error': 'No team members'}), 400
    
    # Use AI to break down goal into tasks
    prompt = f"""Break down this project goal into {len(members)} specific, actionable tasks:
    
Goal: {goal}

Return ONLY a JSON array of task strings, nothing else. Example format:
["Task 1 description", "Task 2 description", "Task 3 description"]

Make tasks:
- Specific and actionable
- Roughly equal in complexity  
- Contribute to the main goal"""
    
    try:
        response = rag_system.generate_response(messages=[
            {"role": "user", "content": prompt}
        ])
        
        # Parse AI response
        ai_text = response['message']['content'].strip()
        
        # Extract JSON array
        import re
        json_match = re.search(r'\[.*\]', ai_text, re.DOTALL)
        if json_match:
            tasks = json.loads(json_match.group())
        else:
            # Fallback: simple splitting
            tasks = [f"Task {i+1} for project goal" for i in range(len(members))]
        
        # Assign tasks to members
        for i, member_id in enumerate(members):
            task_content = tasks[i] if i < len(tasks) else f"Support task {i+1}"
            add_group_task(group_id, member_id, task_content)
        
        return jsonify({'success': True, 'tasks_created': len(tasks)})
        
    except Exception as e:
        print(f"AI task assignment error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/group/status', methods=['GET'])
def get_team_status():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    # Get group details
    group = get_user_group(user_id)
    if not group:
        return jsonify({'error': 'No group found'}), 404
    
    group_id = group[0]
    details = get_group_with_details(group_id)
    
    return jsonify(details)

@app.route('/api/group/chat-ai', methods=['POST'])
def group_chat_ai():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    data = request.json
    message = data.get('message', '')
    
    # Get user info
    user = get_user(user_id)
    user_name = user[1] if user else f"User {user_id}"
    
    # Get group and tasks
    group = get_user_group(user_id)
    if not group:
        return jsonify({'error': 'No group'}), 404
    
    group_id = group[0]
    tasks = get_group_tasks(group_id)
    
    # Check if user is reporting task completion
    task_updated = False
    if 'done' in message.lower() or 'finished' in message.lower() or 'completed' in message.lower():
        # Find user's tasks
        user_tasks = [t for t in tasks if t[2] == user_id and t[4] != 'DONE']
        if user_tasks:
            # Mark first pending task as done
            update_task_status(user_tasks[0][0], 'DONE')
            task_updated = True
    
    # Build AI prompt with context
    members = get_group_members(group_id)
    tasks_context = []
    for t in tasks:
        status = t[4] if len(t) > 4 else 'PENDING'
        assigned_user = t[2]
        task_user = get_user(assigned_user)
        task_user_name = task_user[1] if task_user else f"User {assigned_user}"
        tasks_context.append(f"{task_user_name}: {t[3]} - {status}")
    
    prompt = f"""You are PartnerAI, team coordinator. Context:
- Team has {len(members)} members
- Tasks: {', '.join(tasks_context)}
- {user_name} said: "{message}"

Respond briefly and helpfully. If they completed a task, congratulate them and mention what others need to do. Use bullet points."""
    
    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        
        ai_response = response['message']['content']
        
        return jsonify({
            'response': ai_response,
            'task_updated': task_updated
        })
    except Exception as e:
        return jsonify({'response': f"I'm here to help! Error: {str(e)}", 'task_updated': task_updated})



# ===== SMART BLOCKS API =====

@app.route('/api/blocks', methods=['GET', 'POST'])
def blocks_api():
    """List all blocks or create a new block."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        # List blocks with optional filtering
        block_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        
        blocks = get_user_blocks(user_id, block_type=block_type, limit=limit)
        return jsonify({'blocks': blocks, 'count': len(blocks)})
    
    elif request.method == 'POST':
        # Create new block
        data = request.json
        block_type = data.get('type')
        title = data.get('title', '')
        content = data.get('content', '')
        metadata = data.get('metadata', {})
        
        if not validate_block_type(block_type):
            return jsonify({'error': f'Invalid block type. Must be one of: {list(BLOCK_TYPES.keys())}'}), 400
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        block_id = create_block(user_id, block_type, title, content, metadata)
        
        if block_id:
            # Get AI suggestions for related blocks
            suggested = auto_link_blocks(user_id, block_id, content, block_type)
            
            return jsonify({
                'success': True,
                'block_id': block_id,
                'suggested_links': suggested
            })
        else:
            return jsonify({'error': 'Failed to create block'}), 500


@app.route('/api/blocks/<int:block_id>', methods=['GET', 'PUT', 'DELETE'])
def block_detail_api(block_id):
    """Get, update, or delete a specific block."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        # Get block details with relationships
        blocks = get_user_blocks(user_id, limit=1000)
        block = next((b for b in blocks if b['id'] == block_id), None)
        
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        relationships = get_block_relationships(block_id)
        
        return jsonify({
            'block': block,
            'relationships': relationships
        })
    
    elif request.method == 'PUT':
        # Update block
        data = request.json
        title = data.get('title')
        content = data.get('content')
        metadata = data.get('metadata')
        
        update_smart_block(block_id, title, content, metadata)
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # Delete block
        delete_smart_block(block_id)
        return jsonify({'success': True})


@app.route('/api/blocks/<int:block_id>/link', methods=['POST'])
def link_blocks_api(block_id):
    """Create a relationship between two blocks."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    target_block_id = data.get('target_block_id')
    relationship_type = data.get('relationship_type', 'related')
    
    if not target_block_id:
        return jsonify({'error': 'target_block_id is required'}), 400
    
    link_blocks(block_id, target_block_id, relationship_type)
    
    return jsonify({'success': True})


@app.route('/api/blocks/search', methods=['POST'])
def search_blocks_api():
    """Search blocks by title or content."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'results': []})
    
    results = search_blocks(user_id, query)
    
    return jsonify({'results': results, 'count': len(results)})


@app.route('/api/blocks/ai-suggest', methods=['POST'])
def ai_suggest_blocks():
    """AI-powered block suggestions based on user goal and history."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    data = request.json
    block_type = data.get('type', 'idea')
    context = data.get('context', '')  # Optional context from user
    
    user = get_user(user_id)
    user_goal = user[2] if user and len(user) > 2 and user[2] else "personal growth"
    
    # Build prompt for AI suggestions
    prompt = f"""User Goal: {user_goal}
Context: {context if context else 'General brainstorming'}

Generate 3-5 {block_type} block suggestions that would help the user achieve their goal.

Format as JSON array: [{{"title": "...", "content": "..."}}]

Be specific and actionable."""
    
    try:
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are a creative assistant. Return ONLY valid JSON array."},
            {"role": "user", "content": prompt}
        ])
        
        content = response['message']['content']
        
        # Extract JSON
        if '[' in content:
            start = content.find('[')
            end = content.rfind(']') + 1
            suggestions = json.loads(content[start:end])
        else:
            suggestions = []
        
        return jsonify({'suggestions': suggestions})
        
    except AIConnectionError as e:
        return jsonify({'error': 'AI service unavailable', 'suggestions': []}), 503
    except Exception as e:
        print(f"AI Suggest Error: {e}", flush=True)
        return jsonify({'error': 'Failed to generate suggestions', 'suggestions': []}), 500


@app.route('/api/blocks/analytics', methods=['GET'])
def blocks_analytics():
    """Get analytics about user's block network."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    analytics = analyze_block_network(user_id)
    
    return jsonify(analytics)


@app.route('/api/blocks/types', methods=['GET'])
def block_types_api():
    """Get available block types and their templates."""
    return jsonify({'types': BLOCK_TYPES})


# ===== HABIT INTELLIGENCE API =====

@app.route('/api/habits/ai-insights', methods=['GET'])
def get_ai_habit_insights():
    """Get AI-generated weekly insights for all habits."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        insights = generate_weekly_insights(user_id)
        return jsonify(insights)
    except Exception as e:
        print(f"Error generating insights: {e}", flush=True)
        return jsonify({
            'week_score': 0,
            'insights': ['Unable to generate insights at this time'],
            'recommendations': []
        }), 500


@app.route('/api/habits/<habit_name>/ai-analysis', methods=['GET'])
def get_habit_ai_analysis(habit_name):
    """Get detailed failure analysis for specific habit."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        analysis = analyze_habit_failures(user_id, habit_name)
        return jsonify(analysis)
    except Exception as e:
        print(f"Error analyzing habit: {e}", flush=True)
        return jsonify({'error': 'Analysis failed'}), 500


@app.route('/api/habits/<habit_name>/ai-optimize', methods=['GET'])
def get_habit_optimization(habit_name):
    """Get optimal timing suggestions for a habit."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        timing = detect_optimal_timing(user_id, habit_name)
        return jsonify(timing)
    except Exception as e:
        print(f"Error optimizing timing: {e}", flush=True)
        return jsonify({'error': 'Optimization failed'}), 500


@app.route('/api/habits/ai-goal-map', methods=['GET'])
def get_ai_goal_mapping():
    """Get habit-to-goal dependency graph."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        mapping = map_habits_to_goals(user_id)
        return jsonify(mapping)
    except Exception as e:
        print(f"Error mapping goals: {e}", flush=True)
        return jsonify({'error': 'Goal mapping failed'}), 500


@app.route('/api/habits/<habit_name>/ai-adjust', methods=['POST'])
def get_habit_auto_adjustment(habit_name):
    """Get AI-suggested adjustments for a habit."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        adjustment = auto_adjust_habit(user_id, habit_name)
        return jsonify(adjustment)
    except Exception as e:
        print(f"Error auto-adjusting: {e}", flush=True)
        return jsonify({'error': 'Auto-adjustment failed'}), 500


# ===== COACH REPORT API =====

@app.route('/api/coach/generate-report', methods=['POST'])
def generate_coach_report():
    """Generate AI-powered weekly coaching report."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        report = create_weekly_report(user_id)
        return jsonify(report)
    except Exception as e:
        print(f"Error generating coach report: {e}", flush=True)
        return jsonify({'error': 'Failed to generate report'}), 500


@app.route('/api/coach/latest-report', methods=['GET'])
def get_latest_report():
    """Get the most recent weekly report."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    try:
        # Try to get latest report from AI memory
        from smart_blocks_db import get_ai_memory
        import json
        
        report_json = get_ai_memory(user_id, 'latest_weekly_report')
        if report_json:
            report = json.loads(report_json)
            return jsonify(report)
        else:
            # Generate new report if none exists
            report = create_weekly_report(user_id)
            return jsonify(report)
    except Exception as e:
        print(f"Error getting latest report: {e}", flush=True)
        return jsonify({'error': 'Failed to retrieve report'}), 500


# ===== WORKSPACE PAGE =====

@app.route('/workspace')
def workspace_page():
    """Main workspace page with smart blocks."""
    try:
        if 'user_id' not in session:
            return render_template('login.html')
        return render_template('workspace.html', active_page='workspace')

    except Exception as e:
        return f"Error loading workspace: {str(e)}", 500


@app.route('/workspace/new')
def new_block_page():
    """Notion-like blank block editor (new block)."""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('block_editor.html', block=None, active_page='workspace')


@app.route('/workspace/<int:block_id>/edit')
def edit_block_page(block_id):
    """Notion-like block editor for an existing block."""
    if 'user_id' not in session:
        return redirect('/login')
    block = get_knowledge_block(session['user_id'], block_id)
    if not block:
        return redirect('/workspace')
    return render_template('block_editor.html', block=block, active_page='workspace')

@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect('/')
    user_id = session['user_id']
    history = get_chat_history(user_id, limit=50)
    return render_template('chat.html', active_page='chat', history=history)





# --- FOCUS API ---
@app.route('/api/focus/complete', methods=['POST'])
def complete_focus_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    duration = data.get('duration', 25)
    task = data.get('task', 'Focus Session')
    
    save_focus_session(session['user_id'], duration, task)
    return jsonify({'status': 'success'})

# --- REDIRECTS (Legacy) ---
@app.route('/report-page')
def report_page_redirect():
    return redirect('/report')

# --- REPORT PAGE ---
# ==========================================
# AI-POWERED ROUTINE REPORT
# ==========================================

@app.route('/report')
def report_page():
    """Render AI-Powered Routine Analysis Page"""
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('report.html')

@app.route('/api/routine-analysis-v2', methods=['GET'])
def get_routine_analysis_v2():
    """Generate comprehensive AI-powered routine analysis"""
    print("DEBUG: /api/routine-analysis-v2 HIT", flush=True)
    if 'user_id' not in session:
        print("DEBUG: Unauthorized access to routine analysis", flush=True)
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    print(f"DEBUG: Generating analysis for User {user_id}", flush=True)
    
    try:
        # Get comprehensive routine data
        routine = aggregate_user_routine(user_id, days=7)
        print("DEBUG: Routine data aggregated", flush=True)
        
        # Build AI prompt with all data
        prompt = f"""Analyze this user's complete productivity routine over the past 7 days:

📊 HABITS:
- Completion Rate: {routine['habit_completion_rate']}%
- Active Days: {routine['habit_days_active']}/7

🎯 FOCUS SESSIONS:
- Total Time: {routine['total_focus_minutes']} minutes
- Sessions: {routine['total_focus_sessions']}
- Avg Score: {routine['avg_focus_score']}/10

✅ DAILY TASKS:
- Completed: {routine['completed_tasks']}/{routine['total_tasks']}
- Completion Rate: {routine['task_completion_rate']}%

🤖 AI DAILY TASKS (Goal-Based):
- Completed: {routine['ai_tasks_completed']}/{routine['ai_tasks_total']}
- Rolled Over: {routine['ai_tasks_rolled']}
- Completion Rate: {routine['ai_task_completion_rate']}%

⏰ PRODUCTIVITY PATTERN:
- Peak Hours: {', '.join(routine['peak_hours']) if routine['peak_hours'] else 'Not enough data'}
- Chat Activity: {routine['chat_activity']} interactions

Provide analysis in EXACTLY this format:

ROUTINE_SCORE: [0-100 number only]
TOP_STRENGTH: [One compelling sentence about their best metric]
MAIN_WEAKNESS: [One specific area needing improvement]
PRODUCTIVITY_PATTERN: [When they work best - morning/afternoon/evening/night]
REC1: [Specific actionable recommendation #1]
REC2: [Specific actionable recommendation #2]
REC3: [Specific actionable recommendation #3]
PREDICTION: [Expected outcome if they continue current habits]"""

        # Generate AI analysis
        response = rag_system.generate_response(messages=[
            {"role": "system", "content": "You are an elite productivity coach analyzing user routines. Be encouraging yet honest. Output ONLY in the specified format."},
            {"role": "user", "content": prompt}
        ])
        
        content = response['message']['content']
        
        # Parse AI response
        analysis = {
            'routine_score': 65,
            'top_strength': "You're showing up consistently!",
            'main_weakness': "Focus on completing more daily tasks.",
            'productivity_pattern': "Most active in the afternoon",
            'recommendations': [
                "Start your day with the hardest task",
                "Set specific time blocks for deep work",
                "Review and adjust goals weekly"
            ],
            'prediction': "With continued effort, you'll see 20% productivity increase"
        }
        
        # Parse each line
        lines = content.split('\n')
        recs = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("ROUTINE_SCORE:"):
                try:
                    score_str = line.replace("ROUTINE_SCORE:", "").strip()
                    analysis['routine_score'] = int(''.join(filter(str.isdigit, score_str)))
                except:
                    pass
            elif line.startswith("TOP_STRENGTH:"):
                analysis['top_strength'] = line.replace("TOP_STRENGTH:", "").strip()
            elif line.startswith("MAIN_WEAKNESS:"):
                analysis['main_weakness'] = line.replace("MAIN_WEAKNESS:", "").strip()
            elif line.startswith("PRODUCTIVITY_PATTERN:"):
                analysis['productivity_pattern'] = line.replace("PRODUCTIVITY_PATTERN:", "").strip()
            elif line.startswith("REC"):
                rec_text = line.split(":", 1)[1].strip() if ":" in line else line
                recs.append(rec_text)
            elif line.startswith("PREDICTION:"):
                analysis['prediction'] = line.replace("PREDICTION:", "").strip()
        
        if recs:
            analysis['recommendations'] = recs[:3]
        
        # Return combined data
        return jsonify({
            **routine,
            **analysis
        })
        
    except Exception as e:
        print(f"Routine Analysis Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        # Return fallback data
        return jsonify({
            'routine_score': 50,
            'top_strength': "You're tracking your progress!",
            'main_weakness': "Keep building consistency",
            'productivity_pattern': "Still learning your patterns",
            'recommendations': [
                "Use the focus timer daily",
                "Complete at least 3 tasks per day",
                "Check in with AI coach regularly"
            ],
            'prediction': "Stay consistent and you'll see growth",
            'habit_completion_rate': 0,
            'total_focus_minutes': 0,
            'total_tasks': 0,
            'completed_tasks': 0,
            'ai_task_completion_rate': 0
        })


# ===== HABITS API (NEW) =====
@app.route('/api/habits', methods=['GET', 'POST'])
def habits_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    
    if request.method == 'GET':
        habits = get_user_habits(user_id)
        return jsonify(habits)
    
    elif request.method == 'POST':
        data = request.json
        title = data.get('title')
        category = data.get('category', 'General')
        time_of_day = data.get('time_of_day', 'Anytime')
        
        if not title: return jsonify({'error': 'Title is required'}), 400
        
        habit_id = create_habit(user_id, title, category, time_of_day=time_of_day)
        return jsonify({'id': habit_id, 'status': 'created'})

@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
def delete_habit_api(habit_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if delete_habit(habit_id, session['user_id']):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Failed to delete'}), 400

@app.route('/api/habits/<int:habit_id>/toggle', methods=['POST'])
def toggle_habit_api(habit_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    status = toggle_habit(habit_id, session['user_id'])
    return jsonify({'completed': status})

@app.route('/api/habits/stats', methods=['GET'])
def habit_stats_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    stats = get_weekly_stats(session['user_id'])
    return jsonify(stats)

# ===== AI TASK API (NEW) =====
@app.route('/api/ai-tasks/<int:task_id>/complete', methods=['POST'])
def complete_ai_task_api(task_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    complete_ai_task(task_id)
    
    # Increment flow day on completion
    # Logic: Only increment ONCE per day? Or per task? 
    # User said: "if user done the daily ai task it was count was increce"
    # Assuming simply incrementing for now as per request.
    increment_flow_day(session['user_id'])
    
    return jsonify({'status': 'completed', 'flow_day': get_flow_day(session['user_id'])})

@app.route('/api/user/flow', methods=['GET'])
def get_user_flow_api():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    count = get_flow_day(session['user_id'])
    return jsonify({'flow_day': count})

# Duplicate /api/ai-tasks POST removed — tasks are auto-extracted from chat conversations

def _auto_start_llm_server():
    """Cloud-only deployment: no local model server to start."""
    return


if __name__ == '__main__':
    print("🚀 Starting PartnerAI Server...\n")
    try:
        init_habits_db()
    except Exception as e:
        print(f"Stats DB Init Error (Safe to ignore): {e}")

    # Cloud AI setup does not require a local model server
    _auto_start_llm_server()

    # Initialize RAG system (lightweight SQLite ranking)
    try:
        init_rag_system()
        print("✅ RAG system initialized", flush=True)
    except Exception as e:
        print(f"⚠️ RAG init failed (non-fatal): {e}", flush=True)

    # Initialize AI Task Scheduler
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ai_task_scheduler import init_scheduler
        scheduler = init_scheduler(app)
        print("✅ AI Task Scheduler initialized")
    except Exception as e:
        print(f"⚠️ Scheduler init failed: {e}")
    
    print("✅ PartnerAI is ready.", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
