import os
import sqlite3
from datetime import datetime, timedelta
import threading

from contextlib import contextmanager


def _default_db_path():
    if os.getenv("VERCEL"):
        return os.getenv("PARTNERAI_DB_PATH", "/tmp/partnerai.db")
    return os.getenv("PARTNERAI_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "partnerai.db"))


DB_NAME = _default_db_path()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        def add_column(table, column, col_type, default_value=None):
            try:
                if default_value is not None:
                     cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default_value}")
                else:
                     cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except sqlite3.OperationalError:
                pass 

        # 1. Base Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT
        )
        """)
        
        # 2. Add columns
        add_column('users', 'career', 'TEXT')
        add_column('users', 'hobbies', 'TEXT')
        add_column('users', 'last_task', 'TEXT')
        add_column('users', 'task_status', 'TEXT')
        add_column('users', 'state', 'TEXT')
        add_column('users', 'tasks_completed', 'INTEGER', 0)
        add_column('users', 'streak', 'INTEGER', 0)
        add_column('users', 'last_active_date', 'TEXT')
        add_column('users', 'daily_topic', 'TEXT')
        add_column('users', 'work_time', 'TEXT')
        add_column('users', 'free_time', 'TEXT')
        add_column('users', 'age', 'TEXT')
        add_column('users', 'last_task_date', 'TEXT')
        # Auth
        add_column('users', 'username', 'TEXT')
        add_column('users', 'password', 'TEXT')
        add_column('users', 'email', 'TEXT')
        add_column('users', 'flow_day', 'INTEGER', 0)

        # 3. Community / Groups
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            content TEXT,
            timestamp TEXT
        )
        """)
        
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            leader_id INTEGER,
            status TEXT DEFAULT 'PLANNING',
            goal TEXT
        )
        """)
        
        # Add new team collaboration columns to groups
        add_column('groups', 'project_name', 'TEXT')
        add_column('groups', 'deadline', 'TEXT')
        add_column('groups', 'invite_code', 'TEXT')
        add_column('groups', 'created_at', 'TEXT')

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            user_id INTEGER
        )
        """)
        
        # Add role tracking for members
        add_column('group_members', 'role', 'TEXT', "'member'")
        add_column('group_members', 'joined_at', 'TEXT')

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            assigned_user_id INTEGER,
            task_content TEXT,
            status TEXT DEFAULT 'PENDING'
        )
        """)

        # 4. Knowledge Blocks (AI Workspace)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT, -- idea, task, learning, reflection, read
            title TEXT,
            content TEXT,
            tags TEXT,
            status TEXT DEFAULT 'active',
            meta TEXT, -- JSON for colors, progress, etc.
            linked_to TEXT, -- IDs of linked blocks
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Chat Tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
        """)
        
        # Rewards & Daily
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reward_type TEXT,
            earned_at TEXT
        )
        """)
        
        # Add duration column
        add_column('user_rewards', 'duration_minutes', 'INTEGER', 25)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_content TEXT,
            is_completed INTEGER DEFAULT 0,
            created_at TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            created_at TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            news_json TEXT,
            created_at TEXT
        )
        """)
        
        # --- SMART BLOCKS SYSTEM ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS smart_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            block_type TEXT NOT NULL,
            title TEXT,
            content TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS block_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id_1 INTEGER NOT NULL,
            block_id_2 INTEGER NOT NULL,
            relationship_type TEXT,
            created_at TEXT,
            FOREIGN KEY (block_id_1) REFERENCES smart_blocks(id),
            FOREIGN KEY (block_id_2) REFERENCES smart_blocks(id)
        )
        """)
        
        # --- AI MEMORY SYSTEM ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT,
            confidence_score REAL DEFAULT 0.5,
            last_updated TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # --- HABIT ANALYTICS ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            habit_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            scheduled_time TEXT,
            actual_time TEXT,
            completion_duration INTEGER,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # --- WEEKLY REPORTS ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week_start_date TEXT,
            progress_score INTEGER,
            strengths TEXT,
            weaknesses TEXT,
            strategy TEXT,
            report_data TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # --- FOCUS SESSIONS ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_description TEXT,
            micro_tasks TEXT,
            duration_minutes INTEGER,
            completed_tasks INTEGER,
            focus_score REAL,
            feedback TEXT,
            started_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # --- AI DAILY TASKS ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_content TEXT NOT NULL,
            task_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        
        # --- IN-APP REMINDERS ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            trigger_at TEXT NOT NULL,
            triggered INTEGER DEFAULT 0,
            dismissed INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)

        # --- SIGNUP EMAIL VERIFICATION ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS signup_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        
        # Login verification codes (for sign-in 2FA)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        
        conn.commit()

# Initialize DB immediately
init_db()


# --- AUTH ---
def create_account(username, password, email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
        if cursor.fetchone(): return None
        # Hash password before storing
        hashed = _hash_password(password)
        cursor.execute("INSERT INTO users (username, password, email, name) VALUES (?, ?, ?, ?)", (username, hashed, email, username))
        conn.commit()
        return cursor.lastrowid

def verify_user(username_or_email, password):
    with get_db() as conn:
        cursor = conn.cursor()
        # Check both username and email columns
        cursor.execute("SELECT user_id, password FROM users WHERE username=? OR email=?", (username_or_email, username_or_email))
        row = cursor.fetchone()
        if not row:
            return None
        user_id, stored = row[0], row[1]
        if _verify_password(stored, password):
            return user_id
        return None


def get_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic, work_time, free_time, age, last_task_date, username, password, email, flow_day FROM users WHERE user_id=?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        # Force conversion to tuple for legacy index-based access in app.py
        return tuple(row)


def save_user(user_id, **fields):
    if not fields:
        return True
    allowed = {
        'name', 'career', 'hobbies', 'last_task', 'task_status', 'state', 'tasks_completed',
        'streak', 'last_active_date', 'daily_topic', 'work_time', 'free_time', 'age',
        'last_task_date', 'username', 'password', 'email', 'flow_day'
    }
    updates = []
    values = []
    for key, value in fields.items():
        if key in allowed:
            updates.append(f"{key}=?")
            values.append(value)
    if not updates:
        return True
    values.append(user_id)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id=?", values)
        if cursor.rowcount == 0:
            cursor.execute(
                "INSERT INTO users (user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic, work_time, free_time, age, last_task_date, username, password, email, flow_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [user_id] + [fields.get(k) for k in ['name', 'career', 'hobbies', 'last_task', 'task_status', 'state', 'tasks_completed', 'streak', 'last_active_date', 'daily_topic', 'work_time', 'free_time', 'age', 'last_task_date', 'username', 'password', 'email', 'flow_day']]
            )
        conn.commit()
    return True


# Password hashing utilities using PBKDF2-HMAC
import os, hashlib, binascii

def _hash_password(password: str, iterations: int = 180000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f"pbkdf2_sha256${iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def _verify_password(stored: str, password: str) -> bool:
    try:
        algo, iterations, salt_hex, dk_hex = stored.split('$')
        iterations = int(iterations)
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(dk_hex)
        test = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hashlib.compare_digest(test, expected)
    except Exception:
        return False


def username_exists(username_or_email):
    with get_db() as conn:
        cursor = conn.cursor()
        # Check both username and email to allow login with either
        cursor.execute("SELECT user_id FROM users WHERE username=? OR email=?", (username_or_email, username_or_email))
        return cursor.fetchone() is not None


def save_signup_verification(username, password, email, code, expires_at):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO signup_verifications (username, password, email, code, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password=excluded.password,
                email=excluded.email,
                code=excluded.code,
                expires_at=excluded.expires_at,
                created_at=excluded.created_at
            """,
            (username, password, email, code, expires_at, now_str),
        )
        conn.commit()


def verify_signup_code(username, email, password, code):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, expires_at, password, email
            FROM signup_verifications
            WHERE username=? AND code=?
            """,
            (username, code),
        )
        row = cursor.fetchone()
        if not row:
            return False, "Invalid verification code."

        _, expires_at, saved_password, saved_email = row

        try:
            exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return False, "Verification code is invalid. Request a new code."

        if datetime.now() > exp_dt:
            return False, "Verification code expired. Please request a new code."

        if (saved_email or "").strip().lower() != (email or "").strip().lower():
            return False, "Email does not match verification request."

        if saved_password != password:
            return False, "Password changed. Request a new verification code."

        return True, None


def clear_signup_verification(username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signup_verifications WHERE username=?", (username,))
        conn.commit()


def cleanup_expired_signup_verifications():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM signup_verifications WHERE expires_at < ?", (now_str,))
        conn.commit()


def save_login_verification(username, code, expires_at):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_verifications (username, code, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (username, code, expires_at, now_str)
        )
        conn.commit()


def verify_login_code(username, code):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, expires_at FROM login_verifications WHERE username=? AND code=?", (username, code))
        row = cursor.fetchone()
        if not row:
            return False, 'Invalid verification code.'

        vid, expires_at = row
        try:
            exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return False, 'Verification code invalid.'

        if datetime.now() > exp_dt:
            return False, 'Code expired.'

        return True, None


def clear_login_verification(username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login_verifications WHERE username=?", (username,))
        conn.commit()


def cleanup_expired_login_verifications():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login_verifications WHERE expires_at < ?", (now_str,))
        conn.commit()


def get_user_email(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else None


def get_user_by_username(username_or_email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic, work_time, free_time, age, last_task_date, username, password, email, flow_day FROM users WHERE username=? OR email=?",
            (username_or_email, username_or_email)
        )
        row = cursor.fetchone()
        if not row:
            return None
        # Force conversion to tuple for legacy index-based access in app.py
        return tuple(row)


def get_flow_day(user_id):
    user = get_user(user_id)
    if not user:
        return 0
    try:
        # index 18 is flow_day based on the SELECT query in get_user
        return int(user[18] or 0)
    except Exception:
        return 0


def update_user_streak(user_id):
    user = get_user(user_id)
    if not user:
        return 0
    
    # user[8] is streak, user[9] is last_active_date
    current_streak = user[8] or 0
    last_date_str = user[9]
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if last_date_str:
        try:
            # Assuming last_active_date is stored as YYYY-MM-DD
            last_date = datetime.strptime(last_date_str.split(' ')[0], "%Y-%m-%d").date()
        except:
            last_date = None
    else:
        last_date = None
        
    if last_date == today:
        # Already updated today
        return current_streak
    elif last_date == yesterday:
        # Consecutive day!
        new_streak = current_streak + 1
    else:
        # Broke streak or first time
        new_streak = 1
        
    save_user(user_id, streak=new_streak, last_active_date=today.strftime("%Y-%m-%d"))
    return new_streak

def increment_flow_day(user_id):
    current = get_flow_day(user_id)
    new_value = current + 1
    save_user(user_id, flow_day=new_value)
    return new_value

def reset_user(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()

# --- POSTS ---
def create_post(user_name, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("INSERT INTO community_posts (user_name, content, timestamp) VALUES (?, ?, ?)", (user_name, content, timestamp))
        conn.commit()

def get_posts(limit=20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM community_posts ORDER BY id DESC LIMIT ?", (limit,))
        return cursor.fetchall()

# --- GROUPS ---
def create_group(name, leader_id, goal=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO groups (name, leader_id, status, goal) VALUES (?, ?, 'PLANNING', ?)", (name, leader_id, goal))
        group_id = cursor.lastrowid
        cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, leader_id))
        conn.commit()
        return group_id

def join_group(group_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
        if cursor.fetchone(): return True
        cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        conn.commit()
        return True

def get_user_group(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.* FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = ? ORDER BY g.id DESC LIMIT 1
        """, (user_id,))
        return cursor.fetchone()

def get_group_members(group_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM group_members WHERE group_id=?", (group_id,))
        return [row[0] for row in cursor.fetchall()]

def set_group_goal(group_id, goal):
    with get_db() as conn:
        conn.execute("UPDATE groups SET goal=?, status='ACTIVE' WHERE id=?", (goal, group_id))
        conn.commit()

def update_group(group_id, name, goal):
    with get_db() as conn:
        conn.execute("UPDATE groups SET name=?, goal=? WHERE id=?", (name, goal, group_id))
        conn.commit()

def add_group_task(group_id, user_id, task):
    with get_db() as conn:
        conn.execute("INSERT INTO group_tasks (group_id, assigned_user_id, task_content) VALUES (?, ?, ?)", 
                       (group_id, user_id, task))
        conn.commit()

def get_group_tasks(group_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM group_tasks WHERE group_id=?", (group_id,))
        return cursor.fetchall() 

def complete_group_task(task_id):
    with get_db() as conn:
        conn.execute("UPDATE group_tasks SET status='DONE' WHERE id=?", (task_id,))
        conn.commit()

# --- TEAM COLLABORATION ---
import random
import string

def generate_invite_code():
    """Generate unique 8-character invite code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def set_group_project(group_id, project_name, deadline):
    """Set project details for a group"""
    with get_db() as conn:
        conn.execute("UPDATE groups SET project_name=?, deadline=? WHERE id=?", 
                   (project_name, deadline, group_id))
        conn.commit()

def  get_or_create_invite_code(group_id):
    """Get existing or create new invite code for group"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT invite_code FROM groups WHERE id=?", (group_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        
        # Generate new code
        code = generate_invite_code()
        cursor.execute("UPDATE groups SET invite_code=? WHERE id=?", (code, group_id))
        conn.commit()
        return code

def join_group_by_invite(invite_code, user_id):
    """Join group using invite code"""
    from datetime import datetime
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM groups WHERE invite_code=?", (invite_code,))
        row = cursor.fetchone()
        if not row:
            return None
        
        group_id = row[0]
        # Check if already member
        cursor.execute("SELECT * FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
        if cursor.fetchone():
            return group_id
        
        # Add as member
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO group_members (group_id, user_id, role, joined_at) VALUES (?, ?, 'member', ?)",
                     (group_id, user_id, timestamp))
        conn.commit()
        return group_id

def update_task_status(task_id, new_status):
    """Update task status (PENDING, IN_PROGRESS, DONE)"""
    with get_db() as conn:
        conn.execute("UPDATE group_tasks SET status=? WHERE id=?", (new_status, task_id))
        conn.commit()

def get_group_with_details(group_id):
    """Get group with all details including members and tasks"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE id=?", (group_id,))
        group = cursor.fetchone()
        
        if not group:
            return None
        
        # Get members with names
        cursor.execute("""
            SELECT u.user_id, u.name, gm.role 
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = ?
        """, (group_id,))
        members = cursor.fetchall()
        
        # Get tasks
        cursor.execute("""
            SELECT gt.id, gt.task_content, gt.status, gt.assigned_user_id, u.name
            FROM group_tasks gt
            LEFT JOIN users u ON gt.assigned_user_id = u.user_id
            WHERE gt.group_id = ?
        """, (group_id,))
        tasks = cursor.fetchall()
        
        return {
            'group': group,
            'members': members,
            'tasks': tasks
        }


# --- GROUP CHAT ---
def save_group_message(group_id, user_id, role, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("INSERT INTO group_chat_messages (group_id, user_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (group_id, user_id, role, content, timestamp))
        conn.commit()

def get_group_messages(group_id, limit=50):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.user_id, m.role, m.content, m.timestamp, u.name 
            FROM group_chat_messages m
            LEFT JOIN users u ON m.user_id = u.user_id
            WHERE m.group_id=? ORDER BY m.id ASC
        """, (group_id,))
        rows = cursor.fetchall()
        
    return [{
        'user_id': r[0], 
        'role': r[1], 
        'content': r[2], 
        'timestamp': r[3],
        'user_name': "Mentor AI" if r[0] == 0 else (r[4] if r[4] else f"User {r[0]}")
    } for r in rows] # Process outside lock

# --- CHAT HISTORY ---
def save_chat_message(user_id, role, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("INSERT INTO chat_history (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)", 
                       (user_id, role, content, timestamp))
        conn.commit()

def get_chat_history(user_id, limit=50):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM chat_history WHERE user_id=? ORDER BY id ASC", (user_id,))
        rows = cursor.fetchall()
        if len(rows) > limit:
            rows = rows[-limit:]
        return [{'role': r[0], 'content': r[1]} for r in rows]

def clear_chat_history(user_id):
    with get_db() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
        conn.commit()

# --- REWARDS ---
def add_reward(user_id, reward_type, duration_minutes=25):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("INSERT INTO user_rewards (user_id, reward_type, earned_at, duration_minutes) VALUES (?, ?, ?, ?)", 
                       (user_id, reward_type, timestamp, duration_minutes))
        conn.commit()

def get_rewards(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reward_type, earned_at, duration_minutes FROM user_rewards WHERE user_id=? ORDER BY id DESC", (user_id,))
        return [{'type': r[0], 'date': r[1], 'duration': r[2] if len(r) > 2 and r[2] else 25} for r in cursor.fetchall()]

# --- DAILY TASKS ---
def create_daily_task(user_id, task_content):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute("INSERT INTO daily_tasks (user_id, task_content, is_completed, created_at) VALUES (?, ?, 0, ?)", 
                       (user_id, task_content, date))
        conn.commit()

def get_daily_tasks(user_id):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_content, is_completed FROM daily_tasks WHERE user_id=? AND created_at=?", (user_id, date))
        return [{'id': r[0], 'task': r[1], 'is_completed': bool(r[2])} for r in cursor.fetchall()]

def toggle_daily_task(task_id, status):
    val = 1 if status else 0
    with get_db() as conn:
        conn.execute("UPDATE daily_tasks SET is_completed=? WHERE id=?", (val, task_id))
        conn.commit()

def get_weekly_productivity(user_id):
    """
    Get completed tasks count for the last 7 days.
    Returns: {'days': ['Mon', 'Tue'...], 'counts': [0, 2, 5...]}
    """
    days = []
    counts = []
    
    # Calculate last 7 days dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # We iterate 7 days to ensure 0s are included for empty days
        current = start_date
        while current <= end_date:
            day_str = current.strftime("%Y-%m-%d")
            day_label = current.strftime("%a") # Mon, Tue
            
            cursor.execute("""
                SELECT COUNT(*) FROM daily_tasks 
                WHERE user_id=? AND is_completed=1 AND created_at=?
            """, (user_id, day_str))
            
            count = cursor.fetchone()[0]
            
            days.append(day_label)
            counts.append(count)
            
            current += timedelta(days=1)
            
    return {'days': days, 'counts': counts}

def get_weekly_productivity(user_id):
    """
    Get completed tasks count for the last 7 days.
    Returns: {'days': ['Mon', 'Tue'...], 'counts': [0, 2, 5...]}
    """
    days = []
    counts = []
    
    # Calculate last 7 days dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # We iterate 7 days to ensure 0s are included for empty days
        current = start_date
        while current <= end_date:
            day_str = current.strftime("%Y-%m-%d")
            day_label = current.strftime("%a") # Mon, Tue
            
            cursor.execute("""
                SELECT COUNT(*) FROM daily_tasks 
                WHERE user_id=? AND is_completed=1 AND created_at=?
            """, (user_id, day_str))
            
            count = cursor.fetchone()[0]
            
            days.append(day_label)
            counts.append(count)
            
            current += timedelta(days=1)
            
    return {'days': days, 'counts': counts}

# --- DAILY ARTICLES ---
def create_daily_article(user_id, content):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute("INSERT INTO daily_articles (user_id, content, created_at) VALUES (?, ?, ?)", 
                       (user_id, content, date))
        conn.commit()

def get_latest_article(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM daily_articles WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

# --- DAILY NEWS ---
def save_daily_news(user_id, news_json):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute("INSERT INTO daily_news (user_id, news_json, created_at) VALUES (?, ?, ?)", 
                       (user_id, news_json, date))
        conn.commit()

def get_daily_news(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT news_json FROM daily_news WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

# --- FOCUS SESSIONS ---
def save_focus_session(user_id, duration_minutes, task_description=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("INSERT INTO focus_sessions (user_id, duration_minutes, task_description, completed_at) VALUES (?, ?, ?, ?)", 
                       (user_id, duration_minutes, task_description, timestamp))
        # Also add to rewards (XP)
        conn.execute("INSERT INTO user_rewards (user_id, reward_type, earned_at, duration_minutes) VALUES (?, ?, ?, ?)", 
                       (user_id, "FOCUS_SESSION", timestamp, duration_minutes))
        conn.commit()

def get_focus_stats(user_id):
    """
    Get focus stats for the last 7 days.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    daily_minutes = []
    days = []
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get total for week
        cursor.execute("""
            SELECT SUM(duration_minutes), COUNT(*) FROM focus_sessions 
            WHERE user_id=? AND completed_at >= ?
        """, (user_id, start_date.strftime("%Y-%m-%d")))
        
        row = cursor.fetchone()
        total_minutes = row[0] if row and row[0] else 0
        total_sessions = row[1] if row and row[1] else 0
        
        # Get daily breakdown
        current = start_date
        while current <= end_date:
            day_str = current.strftime("%Y-%m-%d")
            day_label = current.strftime("%a")
            
            # SQLite string comparison for date part of timestamp
            cursor.execute("""
                SELECT SUM(duration_minutes) FROM focus_sessions 
                WHERE user_id=? AND completed_at LIKE ?
            """, (user_id, f"{day_str}%"))
            
            row = cursor.fetchone()
            mins = row[0] if row and row[0] else 0
            daily_minutes.append(mins)
            days.append(day_label)
            
            current += timedelta(days=1)
            
    return {
        'total_minutes': total_minutes,
        'total_sessions': total_sessions,
        'daily_minutes': daily_minutes,
        'days': days
    }

# ==========================================
# COMPREHENSIVE ROUTINE ANALYSIS
# ==========================================

def aggregate_user_routine(user_id, days=7):
    """
    Aggregate ALL user activity data for comprehensive AI analysis
    Returns complete routine profile including habits, focus, tasks, and patterns
    """
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. HABITS DATA
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', completed_at) as day, 
                   COUNT(*) as completed,
                   COUNT(DISTINCT habit_id) as unique_habits
            FROM habit_completions
            WHERE user_id = ? AND completed_at >= ?
            GROUP BY day
            ORDER BY day
        """, (user_id, start_date.isoformat()))
        habits_data = cursor.fetchall()
        
        habit_completion_rate = 0
        if habits_data:
            total_daily = sum(row[1] for row in habits_data)
            habit_completion_rate = round((total_daily / (len(habits_data) * 5)) * 100, 1) if len(habits_data) > 0 else 0
        
        # 2. FOCUS SESSIONS
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', started_at) as day,
                   SUM(duration_minutes) as total_minutes,
                   COUNT(*) as sessions,
                   AVG(focus_score) as avg_score,
                   strftime('%H', started_at) as hour
            FROM focus_sessions
            WHERE user_id = ? AND started_at >= ?
            GROUP BY day
        """, (user_id, start_date.isoformat()))
        focus_data = cursor.fetchall()
        
        total_focus_minutes = sum(row[1] or 0 for row in focus_data)
        total_focus_sessions = sum(row[2] or 0 for row in focus_data)
        avg_focus_score = round(sum(row[3] or 0 for row in focus_data) / len(focus_data), 1) if focus_data else 0
        
        # 3. DAILY TASKS
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', created_at) as day,
                   COUNT(*) as total,
                   SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
            FROM daily_tasks
            WHERE user_id = ? AND created_at >= ?
            GROUP BY day
        """, (user_id, start_date.isoformat()))
        tasks_data = cursor.fetchall()
        
        total_tasks = sum(row[1] or 0 for row in tasks_data)
        completed_tasks = sum(row[2] or 0 for row in tasks_data)
        task_completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        
        # 4. AI DAILY TASKS
        cursor.execute("""
            SELECT task_date,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status = 'rolled_over' THEN 1 ELSE 0 END) as rolled
            FROM ai_daily_tasks
            WHERE user_id = ? AND task_date >= ?
            GROUP BY task_date
        """, (user_id, start_date.date().isoformat()))
        ai_tasks_data = cursor.fetchall()
        
        total_ai_tasks = sum(row[1] or 0 for row in ai_tasks_data)
        completed_ai_tasks = sum(row[2] or 0 for row in ai_tasks_data)
        rolled_ai_tasks = sum(row[3] or 0 for row in ai_tasks_data)
        ai_task_completion_rate = round((completed_ai_tasks / total_ai_tasks * 100), 1) if total_ai_tasks > 0 else 0
        
        # 5. ACTIVITY TIMESTAMPS (for pattern detection)
        cursor.execute("""
            SELECT strftime('%H', completed_at) as hour, COUNT(*) as activity_count
            FROM (
                SELECT completed_at as created_at FROM habit_completions WHERE user_id = ? AND completed_at >= ?
                UNION ALL
                SELECT started_at as created_at FROM focus_sessions WHERE user_id = ? AND started_at >= ?
                UNION ALL
                SELECT created_at FROM daily_tasks WHERE user_id = ? AND created_at >= ?
            )
            GROUP BY hour
            ORDER BY activity_count DESC
            LIMIT 3
        """, (user_id, start_date.isoformat(), user_id, start_date.isoformat(), user_id, start_date.isoformat()))
        peak_hours = cursor.fetchall()
        
        # 6. CHAT ACTIVITY
        cursor.execute("""
            SELECT COUNT(*) as messages
            FROM chat_history
            WHERE user_id = ? AND timestamp >= ?
        """, (user_id, start_date.isoformat()))
        chat_activity = cursor.fetchone()[0]
        
    # Compile comprehensive profile
    return {
        'period': f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
        'days_analyzed': days,
        
        # Habits
        'habit_completion_rate': habit_completion_rate,
        'habit_days_active': len(habits_data),
        
        # Focus
        'total_focus_minutes': total_focus_minutes,
        'total_focus_sessions': total_focus_sessions,
        'avg_focus_score': avg_focus_score,
        
        # Tasks
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'task_completion_rate': task_completion_rate,
        
        # AI Tasks
        'ai_tasks_total': total_ai_tasks,
        'ai_tasks_completed': completed_ai_tasks,
        'ai_tasks_rolled': rolled_ai_tasks,
        'ai_task_completion_rate': ai_task_completion_rate,
        
        # Patterns
        'peak_hours': [f"{row[0]}:00" for row in peak_hours] if peak_hours else [],
        'chat_activity': chat_activity,
        
        # Raw data for detailed analysis
        'habits_by_day': habits_data,
        'focus_by_day': focus_data,
        'tasks_by_day': tasks_data,
        'ai_tasks_by_day': ai_tasks_data
    }

# --- AI DAILY TASKS ---
def create_ai_task(user_id, task_content, task_date=None):
    """Create a new AI-generated task"""
    if not task_date:
        task_date = datetime.now().strftime("%Y-%m-%d")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO ai_daily_tasks (user_id, task_content, task_date, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (user_id, task_content, task_date, created_at)
        )
        conn.commit()

def get_ai_tasks_for_date(user_id, task_date=None):
    """Get all AI tasks for a specific date"""
    if not task_date:
        task_date = datetime.now().strftime("%Y-%m-%d")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task_content, status, created_at, completed_at FROM ai_daily_tasks WHERE user_id=? AND task_date=? ORDER BY id ASC",
            (user_id, task_date)
        )
        rows = cursor.fetchall()
        return [{
            'id': r[0],
            'task': r[1],
            'status': r[2],
            'created_at': r[3],
            'completed_at': r[4]
        } for r in rows]

def complete_ai_task(task_id):
    """Mark an AI task as completed"""
    completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(
            "UPDATE ai_daily_tasks SET status='completed', completed_at=?WHERE id=?",
            (completed_at, task_id)
        )
        conn.commit()

def get_incomplete_ai_tasks(user_id, task_date=None):
    """Get all incomplete tasks for a date"""
    if not task_date:
        task_date = datetime.now().strftime("%Y-%m-%d")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task_content FROM ai_daily_tasks WHERE user_id=? AND task_date=? AND status='pending' ORDER BY id ASC",
            (user_id, task_date)
        )
        rows = cursor.fetchall()
        return [{'id': r[0], 'task': r[1]} for r in rows]

def rollover_incomplete_tasks():
    """Roll over all incomplete tasks from yesterday to today"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Find all incomplete tasks from yesterday
        cursor.execute(
            "SELECT user_id, task_content FROM ai_daily_tasks WHERE task_date=? AND status='pending'",
            (yesterday,)
        )
        incomplete_tasks = cursor.fetchall()
        
        # Mark old tasks as rolled_over
        cursor.execute(
            "UPDATE ai_daily_tasks SET status='rolled_over' WHERE task_date=? AND status='pending'",
            (yesterday,)
        )
        
        # Create new tasks for today
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for user_id, task_content in incomplete_tasks:
            cursor.execute(
                "INSERT INTO ai_daily_tasks (user_id, task_content, task_date, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
                (user_id, task_content, today, created_at)
            )
        
        conn.commit()
        return len(incomplete_tasks)

def get_all_active_users():
    """Get all users with active accounts and email addresses"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, email, career FROM users WHERE state='ACTIVE' AND email IS NOT NULL AND email != ''"
        )
        rows = cursor.fetchall()
        return [{'user_id': r[0], 'name': r[1], 'email': r[2], 'goal': r[3] if r[3] else 'Personal Growth'} for r in rows]

def clear_ai_tasks_for_date(user_id, task_date=None):
    """Clear all AI tasks for a specific date (used when regenerating)"""
    if not task_date:
        task_date = datetime.now().strftime("%Y-%m-%d")
    
    with get_db() as conn:
        conn.execute(
            "DELETE FROM ai_daily_tasks WHERE user_id=? AND task_date=?",
            (user_id, task_date)
        )
        conn.commit()


# --- IN-APP REMINDERS ---

def save_reminder(user_id, content, trigger_at):
    """Save a reminder that will fire at trigger_at (ISO string)"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO reminders (user_id, content, trigger_at, triggered, dismissed, created_at) VALUES (?, ?, ?, 0, 0, ?)",
            (user_id, content, trigger_at, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

def get_pending_reminders(user_id):
    """Get reminders that have fired (trigger_at <= now) but not dismissed"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, content, trigger_at, created_at FROM reminders WHERE user_id=? AND trigger_at <= ? AND dismissed=0",
            (user_id, now)
        )
        rows = cursor.fetchall()
        return [{'id': r[0], 'content': r[1], 'trigger_at': r[2], 'created_at': r[3]} for r in rows]

def dismiss_reminder(reminder_id):
    """Mark a reminder as dismissed"""
    with get_db() as conn:
        conn.execute("UPDATE reminders SET dismissed=1, triggered=1 WHERE id=?", (reminder_id,))
        conn.commit()

