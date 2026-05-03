import os
import sqlite3
from datetime import datetime, timedelta
import threading

from contextlib import contextmanager


def _default_db_path():
    """
    Get the database path. On Vercel, use the project directory.
    /tmp is ephemeral in Vercel serverless; data is wiped between deployments.
    Instead, store in the project root which persists within a deployment.
    
    NOTE: Vercel is fully serverless. Data in files only persists within a single deployment.
    For true persistence across deployments, use Vercel KV (Redis) or a hosted database.
    """
    if os.getenv("VERCEL"):
        # On Vercel, use /tmp which persists within the current execution
        # This is better than trying to write to the project root (read-only)
        tmp_path = "/tmp/partnerai_data.db"
        return tmp_path
    
    # Local development: use PARTNERAI_DB_PATH env or default to project root
    return os.getenv("PARTNERAI_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "partnerai.db"))


DB_NAME = _default_db_path()
PL = "%s" if os.getenv("DATABASE_URL") else "?"



@contextmanager
def get_db():
    # Priority: 1. DATABASE_URL (PostgreSQL), 2. Local SQLite
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Clean common mistakes like brackets in env vars
        db_url = db_url.replace('[', '').replace(']', '')
        
    if db_url and (db_url.startswith("postgres") or db_url.startswith("postgresql")):
        try:
            import psycopg2
            # Use sslmode=require for cloud DBs like Supabase/Neon
            conn = psycopg2.connect(db_url, sslmode='require')
            try:
                yield conn
            finally:
                conn.close()
        except ImportError:
            # Fallback if psycopg2 is missing but URL is provided
            print(" DATABASE_URL provided but psycopg2 not installed. Falling back to SQLite.")
            conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            try:
                yield conn
            finally:
                conn.close()
    else:
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
                conn.commit()
                print(f"Added column {column} to {table}")
            except Exception as e:
                # Rollback transaction to prevent "current transaction is aborted" errors in PG
                try:
                    conn.rollback()
                except:
                    pass
                
                # Column likely exists, but let's check the error message
                err_msg = str(e).lower()
                if "already exists" in err_msg or "duplicate column" in err_msg:
                    pass
                else:
                    print(f"Error adding column {column} to {table}: {e}")

        # Determine ID type for auto-increment based on DB connection type
        is_pg = os.getenv("DATABASE_URL") is not None or "psycopg" in str(type(conn)).lower()
        id_type_ai = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

        # 1. Base Users Table
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            user_id {id_type_ai},
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

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS group_tasks (
            id {id_type_ai},
            group_id INTEGER,
            assigned_user_id INTEGER,
            task_content TEXT,
            status TEXT DEFAULT 'PENDING'
        )
        """)

        # 4. Knowledge Blocks (AI Workspace)
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS knowledge_blocks (
            id {id_type_ai},
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
        cursor.execute(f"CREATE TABLE IF NOT EXISTS group_chat_messages (id {id_type_ai}, group_id INTEGER, user_id INTEGER, role TEXT, content TEXT, timestamp TEXT)")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS chat_history (id {id_type_ai}, user_id INTEGER, role TEXT, content TEXT, timestamp TEXT)")
        
        # Rewards & Daily
        cursor.execute(f"CREATE TABLE IF NOT EXISTS user_rewards (id {id_type_ai}, user_id INTEGER, reward_type TEXT, earned_at TEXT)")
        
        # Add duration column
        add_column('user_rewards', 'duration_minutes', 'INTEGER', 25)
        
        cursor.execute(f"CREATE TABLE IF NOT EXISTS daily_tasks (id {id_type_ai}, user_id INTEGER, task_content TEXT, is_completed INTEGER DEFAULT 0, created_at TEXT)")
        
        cursor.execute(f"CREATE TABLE IF NOT EXISTS daily_articles (id {id_type_ai}, user_id INTEGER, content TEXT, created_at TEXT)")
        
        cursor.execute(f"CREATE TABLE IF NOT EXISTS daily_news (id {id_type_ai}, user_id INTEGER, news_json TEXT, created_at TEXT)")
        
        # --- SMART BLOCKS SYSTEM ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS smart_blocks (id {id_type_ai}, user_id INTEGER NOT NULL, block_type TEXT NOT NULL, title TEXT, content TEXT, metadata TEXT, created_at TEXT, updated_at TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")
        
        cursor.execute(f"CREATE TABLE IF NOT EXISTS block_relationships (id {id_type_ai}, block_id_1 INTEGER NOT NULL, block_id_2 INTEGER NOT NULL, relationship_type TEXT, created_at TEXT, FOREIGN KEY (block_id_1) REFERENCES smart_blocks(id), FOREIGN KEY (block_id_2) REFERENCES smart_blocks(id))")
        
        # --- AI MEMORY SYSTEM ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS ai_user_memory (id {id_type_ai}, user_id INTEGER NOT NULL, memory_key TEXT NOT NULL, memory_value TEXT, confidence_score REAL DEFAULT 0.5, last_updated TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")
        
        # --- HABIT ANALYTICS ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS habit_analytics (id {id_type_ai}, user_id INTEGER NOT NULL, habit_name TEXT NOT NULL, completed INTEGER DEFAULT 0, scheduled_time TEXT, actual_time TEXT, completion_duration INTEGER, created_at TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")
        
        # --- WEEKLY REPORTS ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS weekly_reports (id {id_type_ai}, user_id INTEGER NOT NULL, week_start_date TEXT, progress_score INTEGER, strengths TEXT, weaknesses TEXT, strategy TEXT, report_data TEXT, created_at TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")
        
        # --- FOCUS SESSIONS ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS focus_sessions (id {id_type_ai}, user_id INTEGER NOT NULL, task_description TEXT, micro_tasks TEXT, duration_minutes INTEGER, completed_tasks INTEGER, focus_score REAL, feedback TEXT, started_at TEXT, completed_at TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")
        
        # --- AI DAILY TASKS ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS ai_daily_tasks (id {id_type_ai}, user_id INTEGER NOT NULL, task_content TEXT NOT NULL, task_date TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TEXT, completed_at TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")
        
        # --- IN-APP REMINDERS ---
        cursor.execute(f"CREATE TABLE IF NOT EXISTS reminders (id {id_type_ai}, user_id INTEGER NOT NULL, content TEXT NOT NULL, trigger_at TEXT NOT NULL, triggered INTEGER DEFAULT 0, dismissed INTEGER DEFAULT 0, created_at TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id))")

        # --- AUTH VERIFICATIONS ---
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS signup_verifications (
            id {id_type_ai},
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS login_verifications (
            id {id_type_ai},
            username TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS password_resets (
            id {id_type_ai},
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()

# Initialize DB immediately (with error handling for serverless environments)
try:
    init_db()
    print(f"Database initialized at: {DB_NAME}", flush=True)
except Exception as e:
    print(f"Warning: DB initialization failed: {e}. Will retry on first query.", flush=True)


# --- AUTH ---
def create_account(username, password, email):
    import logging
    username = username.strip() if username else ""
    email = email.strip() if email else ""
    
    logging.info(f" Creating account: username='{username}', email='{email}'")
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if username or email already exists (case-insensitive)
        cursor.execute(f"SELECT user_id FROM users WHERE LOWER(username)=LOWER({PL}) OR LOWER(email)=LOWER({PL})", (username, email))
        if cursor.fetchone():
            logging.warning(f" Account already exists: username='{username}' or email='{email}'")
            return None
            
        # Hash password before storing
        hashed = _hash_password(password)
        
        is_pg = os.getenv("DATABASE_URL") is not None or "psycopg" in str(type(conn)).lower()
        logging.info(f" is_pg detection: {is_pg} (DATABASE_URL present: {os.getenv('DATABASE_URL') is not None})")
        
        try:
            if is_pg:
                cursor.execute(f"INSERT INTO users (username, password, email, name, flow_day, state) VALUES ({PL}, {PL}, {PL}, {PL}, 1, 'NEW') RETURNING user_id", (username, hashed, email, username))
                user_id = cursor.fetchone()[0]
            else:
                cursor.execute(f"INSERT INTO users (username, password, email, name, flow_day, state) VALUES ({PL}, {PL}, {PL}, {PL}, 1, 'NEW')", (username, hashed, email, username))
                user_id = cursor.lastrowid
                
            conn.commit()
            logging.info(f" Account created successfully: user_id={user_id}, username='{username}'")
            return user_id
        except Exception as e:
            logging.error(f" Failed to insert user into DB: {e}")
            conn.rollback()
            return None

def verify_user(username_or_email, password):
    if not username_or_email: return None
    val = username_or_email.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        # Fetch all potential matches (case-insensitive)
        cursor.execute(f"SELECT user_id, password FROM users WHERE LOWER(username)=LOWER({PL}) OR LOWER(email)=LOWER({PL})", (val, val))
        rows = cursor.fetchall()
        
        for row in rows:
            user_id, stored = row[0], row[1]
            match = _verify_password(stored, password)
            import logging
            # Log only the start of the hash for security
            stored_preview = (stored[:15] + "...") if stored else "None"
            logging.info(f" Verify attempt for user_id={user_id}: match={match}, stored_preview='{stored_preview}'")
            if match:
                return user_id
                
        logging.warning(f" Login failed: Password mismatch or user not found for identifier='{val}'")
        return None


def get_user(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic, work_time, free_time, age, last_task_date, username, password, email, flow_day FROM users WHERE user_id={PL}",
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
            updates.append(f"{key}={PL}")
            values.append(value)
    if not updates:
        return True
    values.append(user_id)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id={PL}", values)
        if cursor.rowcount == 0:
            # PostgreSQL doesn't support named parameters with list in the same way, but this should work for basic INSERT
            placeholders = ", ".join([PL] * 19)
            cursor.execute(
                f"INSERT INTO users (user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic, work_time, free_time, age, last_task_date, username, password, email, flow_day) VALUES ({placeholders})",
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
        if '$' not in stored:
            # Fallback for older plaintext passwords
            return stored == password
            
        algo, iterations, salt_hex, dk_hex = stored.split('$')
        iterations = int(iterations)
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(dk_hex)
        test = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hashlib.compare_digest(test, expected)
    except Exception:
        return False


def username_exists(username_or_email):
    if not username_or_email: return False
    val = username_or_email.strip()
    with get_db() as conn:
        cursor = conn.cursor()
        # Check both username and email (case-insensitive)
        cursor.execute(f"SELECT user_id FROM users WHERE LOWER(username)=LOWER({PL}) OR LOWER(email)=LOWER({PL})", (val, val))
        return cursor.fetchone() is not None


def save_signup_verification(username, password, email, code, expires_at):
    """Store signup attempt for OTP verification."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Delete any existing verification for this email/username to avoid duplicates
        cursor.execute(f"DELETE FROM signup_verifications WHERE username={PL} OR email={PL}", (username, email))
        cursor.execute(
            f"""
            INSERT INTO signup_verifications (username, password, email, code, expires_at)
            VALUES ({PL}, {PL}, {PL}, {PL}, {PL})
            """,
            (username, password, email, code, expires_at),
        )
        conn.commit()


def verify_signup_code(username, email, password, code):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, expires_at, password, email
            FROM signup_verifications
            WHERE LOWER(username)=LOWER({PL}) AND code={PL}
            """,
            (username, code),
        )
        row = cursor.fetchone()
        if not row:
            return False, "Verification code is invalid. Request a new code."

        _, expires_at, saved_password, saved_email = row

        # Handle both string (SQLite) and datetime (PG)
        if isinstance(expires_at, str):
            try:
                exp_dt = datetime.fromisoformat(expires_at)
            except:
                try:
                    exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                except:
                    return False, "Verification code format error."
        else:
            exp_dt = expires_at

        if exp_dt < datetime.utcnow():
            return False, "Verification code expired. Please request a new code."

        if (saved_email or "").strip().lower() != (email or "").strip().lower():
            return False, "Email does not match verification request."

        if saved_password != password:
            return False, "Password changed. Request a new verification code."

        return True, None


def clear_signup_verification(username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM signup_verifications WHERE LOWER(username)=LOWER({PL})", (username,))
        conn.commit()


def cleanup_expired_signup_verifications():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM signup_verifications WHERE expires_at < {PL}", (now_str,))
        conn.commit()


def save_login_verification(username, code, expires_at):
    """Store login OTP."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM login_verifications WHERE LOWER(username)=LOWER({PL})", (username,))
        cursor.execute(
            f"INSERT INTO login_verifications (username, code, expires_at) VALUES ({PL}, {PL}, {PL})",
            (username, code, expires_at)
        )
        conn.commit()


def verify_login_code(username, code):
    """Verify login OTP."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, expires_at FROM login_verifications WHERE LOWER(username)=LOWER({PL}) AND code={PL}", (username, code))
        row = cursor.fetchone()
        if not row:
            return False, 'Invalid verification code.'

        _, expires_at = row
        # Handle both string (SQLite) and datetime (PG)
        if isinstance(expires_at, str):
            try:
                exp_dt = datetime.fromisoformat(expires_at)
            except:
                try:
                    exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                except:
                    return False, 'Verification code format error.'
        else:
            exp_dt = expires_at

        if exp_dt < datetime.utcnow():
            return False, 'Verification code expired.'

        return True, None


def clear_login_verification(username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM login_verifications WHERE LOWER(username)=LOWER({PL})", (username,))
        conn.commit()


def cleanup_expired_login_verifications():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM login_verifications WHERE expires_at < {PL}", (now_str,))
        conn.commit()


def save_password_reset(username, email, code, expires_at):
    """Store password reset OTP."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM password_resets WHERE username={PL} OR email={PL}", (username, email))
        cursor.execute(
            f"INSERT INTO password_resets (username, email, code, expires_at) VALUES ({PL}, {PL}, {PL}, {PL})",
            (username, email, code, expires_at)
        )
        conn.commit()


    import logging
    logging.info(f" Verifying reset code for identifier='{username_or_email}', code='{code}'")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, expires_at, username FROM password_resets WHERE (LOWER(username)=LOWER({PL}) OR LOWER(email)=LOWER({PL})) AND code={PL}",
            (username_or_email, username_or_email, code)
        )
        row = cursor.fetchone()
        if not row:
            logging.warning(f" Reset code not found in DB for identifier='{username_or_email}' and code='{code}'")
            return False, "Invalid reset code.", None

        _, expires_at, username = row
        # Handle both string (SQLite) and datetime (PG)
        if isinstance(expires_at, str):
            try:
                exp_dt = datetime.fromisoformat(expires_at)
            except:
                try:
                    exp_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                except:
                    return False, "Reset code format error.", None
        else:
            exp_dt = expires_at

        if exp_dt < datetime.utcnow():
            return False, "Reset code expired.", None

        return True, None, username


def update_password(username, new_password):
    """Update user password with hashing."""
    hashed = _hash_password(new_password)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET password={PL} WHERE LOWER(username)=LOWER({PL})", (hashed, username))
        conn.commit()
        return cursor.rowcount > 0


def clear_password_reset(username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM password_resets WHERE LOWER(username)=LOWER({PL})", (username,))
        conn.commit()


def get_user_email(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT email FROM users WHERE user_id={PL}", (user_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else None


def get_user_by_username(username_or_email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT user_id, name, career, hobbies, last_task, task_status, state, tasks_completed, streak, last_active_date, daily_topic, work_time, free_time, age, last_task_date, username, password, email, flow_day FROM users WHERE LOWER(username)=LOWER({PL}) OR LOWER(email)=LOWER({PL})",
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
    """Resets user data (chat, streaks, goals) without deleting the account row."""
    with get_db() as conn:
        # Clear chat
        conn.execute(f"DELETE FROM chat_history WHERE user_id={PL}", (user_id,))
        # Reset user fields
        conn.execute(f"UPDATE users SET state='NEW', career=NULL, streak=0, tasks_completed=0, last_task=NULL, flow_day=1 WHERE user_id={PL}", (user_id,))
        conn.commit()
    import logging
    logging.info(f" user_id {user_id} has been fully reset (account preserved)")

# --- POSTS ---
def create_post(user_name, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(f"INSERT INTO community_posts (user_name, content, timestamp) VALUES ({PL}, {PL}, {PL})", (user_name, content, timestamp))
        conn.commit()

def get_posts(limit=20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM community_posts ORDER BY id DESC LIMIT {PL}", (limit,))
        return cursor.fetchall()

# --- GROUPS ---
def create_group(name, leader_id, goal=None):
    with get_db() as conn:
        cursor = conn.cursor()
        is_pg = os.getenv("DATABASE_URL") is not None or "psycopg" in str(type(conn)).lower()
        if is_pg:
            cursor.execute(f"INSERT INTO groups (name, leader_id, status, goal) VALUES ({PL}, {PL}, 'PLANNING', {PL}) RETURNING id", (name, leader_id, goal))
            group_id = cursor.fetchone()[0]
        else:
            cursor.execute(f"INSERT INTO groups (name, leader_id, status, goal) VALUES ({PL}, {PL}, 'PLANNING', {PL})", (name, leader_id, goal))
            group_id = cursor.lastrowid
        cursor.execute(f"INSERT INTO group_members (group_id, user_id) VALUES ({PL}, {PL})", (group_id, leader_id))
        conn.commit()
        return group_id

def join_group(group_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM group_members WHERE group_id={PL} AND user_id={PL}", (group_id, user_id))
        if cursor.fetchone(): return True
        cursor.execute(f"INSERT INTO group_members (group_id, user_id) VALUES ({PL}, {PL})", (group_id, user_id))
        conn.commit()
        return True

def get_user_group(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT g.* FROM groups g
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = {PL} ORDER BY g.id DESC LIMIT 1
        """, (user_id,))
        return cursor.fetchone()

def get_group_members(group_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT user_id FROM group_members WHERE group_id={PL}", (group_id,))
        return [row[0] for row in cursor.fetchall()]

def set_group_goal(group_id, goal):
    with get_db() as conn:
        conn.execute(f"UPDATE groups SET goal={PL}, status='ACTIVE' WHERE id={PL}", (goal, group_id))
        conn.commit()

def update_group(group_id, name, goal):
    with get_db() as conn:
        conn.execute(f"UPDATE groups SET name={PL}, goal={PL} WHERE id={PL}", (name, goal, group_id))
        conn.commit()

def add_group_task(group_id, user_id, task):
    with get_db() as conn:
        conn.execute(f"INSERT INTO group_tasks (group_id, assigned_user_id, task_content) VALUES ({PL}, {PL}, {PL})", 
                       (group_id, user_id, task))
        conn.commit()

def get_group_tasks(group_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM group_tasks WHERE group_id={PL}", (group_id,))
        return cursor.fetchall() 

def complete_group_task(task_id):
    with get_db() as conn:
        conn.execute(f"UPDATE group_tasks SET status='DONE' WHERE id={PL}", (task_id,))
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
        conn.execute(f"UPDATE groups SET project_name={PL}, deadline={PL} WHERE id={PL}", 
                   (project_name, deadline, group_id))
        conn.commit()

def  get_or_create_invite_code(group_id):
    """Get existing or create new invite code for group"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT invite_code FROM groups WHERE id={PL}", (group_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        
        # Generate new code
        code = generate_invite_code()
        cursor.execute(f"UPDATE groups SET invite_code={PL} WHERE id={PL}", (code, group_id))
        conn.commit()
        return code

def join_group_by_invite(invite_code, user_id):
    """Join group using invite code"""
    from datetime import datetime
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM groups WHERE invite_code={PL}", (invite_code,))
        row = cursor.fetchone()
        if not row:
            return None
        
        group_id = row[0]
        # Check if already member
        cursor.execute(f"SELECT * FROM group_members WHERE group_id={PL} AND user_id={PL}", (group_id, user_id))
        if cursor.fetchone():
            return group_id
        
        # Add as member
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"INSERT INTO group_members (group_id, user_id, role, joined_at) VALUES ({PL}, {PL}, 'member', {PL})",
                     (group_id, user_id, timestamp))
        conn.commit()
        return group_id

def update_task_status(task_id, new_status):
    """Update task status (PENDING, IN_PROGRESS, DONE)"""
    with get_db() as conn:
        conn.execute(f"UPDATE group_tasks SET status={PL} WHERE id={PL}", (new_status, task_id))
        conn.commit()

def get_group_with_details(group_id):
    """Get group with all details including members and tasks"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM groups WHERE id={PL}", (group_id,))
        group = cursor.fetchone()
        
        if not group:
            return None
        
        # Get members with names
        cursor.execute(f"""
            SELECT u.user_id, u.name, gm.role 
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = {PL}
        """, (group_id,))
        members = cursor.fetchall()
        
        # Get tasks
        cursor.execute(f"""
            SELECT gt.id, gt.task_content, gt.status, gt.assigned_user_id, u.name
            FROM group_tasks gt
            LEFT JOIN users u ON gt.assigned_user_id = u.user_id
            WHERE gt.group_id = {PL}
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
        conn.execute(f"INSERT INTO group_chat_messages (group_id, user_id, role, content, timestamp) VALUES ({PL}, {PL}, {PL}, {PL}, {PL})",
                       (group_id, user_id, role, content, timestamp))
        conn.commit()

def get_group_messages(group_id, limit=50):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT m.user_id, m.role, m.content, m.timestamp, u.name 
            FROM group_chat_messages m
            LEFT JOIN users u ON m.user_id = u.user_id
            WHERE m.group_id={PL} ORDER BY m.id ASC
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
        conn.execute(f"INSERT INTO chat_history (user_id, role, content, timestamp) VALUES ({PL}, {PL}, {PL}, {PL})", 
                       (user_id, role, content, timestamp))
        conn.commit()

def get_chat_history(user_id, limit=50):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT role, content FROM chat_history WHERE user_id={PL} ORDER BY id ASC", (user_id,))
        rows = cursor.fetchall()
        if len(rows) > limit:
            rows = rows[-limit:]
        return [{'role': r[0], 'content': r[1]} for r in rows]

def clear_chat_history(user_id):
    with get_db() as conn:
        conn.execute(f"DELETE FROM chat_history WHERE user_id={PL}", (user_id,))
        conn.commit()

# --- REWARDS ---
def add_reward(user_id, reward_type, duration_minutes=25):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(f"INSERT INTO user_rewards (user_id, reward_type, earned_at, duration_minutes) VALUES ({PL}, {PL}, {PL}, {PL})", 
                       (user_id, reward_type, timestamp, duration_minutes))
        conn.commit()

def get_rewards(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT reward_type, earned_at, duration_minutes FROM user_rewards WHERE user_id={PL} ORDER BY id DESC", (user_id,))
        return [{'type': r[0], 'date': r[1], 'duration': r[2] if len(r) > 2 and r[2] else 25} for r in cursor.fetchall()]

# --- DAILY TASKS ---
def create_daily_task(user_id, task_content):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(f"INSERT INTO daily_tasks (user_id, task_content, is_completed, created_at) VALUES ({PL}, {PL}, 0, {PL})", 
                       (user_id, task_content, date))
        conn.commit()

def get_daily_tasks(user_id):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, task_content, is_completed FROM daily_tasks WHERE user_id={PL} AND created_at={PL}", (user_id, date))
        return [{'id': r[0], 'task': r[1], 'is_completed': bool(r[2])} for r in cursor.fetchall()]

def toggle_daily_task(task_id, status):
    val = 1 if status else 0
    with get_db() as conn:
        conn.execute(f"UPDATE daily_tasks SET is_completed={PL} WHERE id={PL}", (val, task_id))
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
            
            cursor.execute(f"""
                SELECT COUNT(*) FROM daily_tasks 
                WHERE user_id={PL} AND is_completed=1 AND created_at={PL}
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
        conn.execute(f"INSERT INTO daily_articles (user_id, content, created_at) VALUES ({PL}, {PL}, {PL})", 
                       (user_id, content, date))
        conn.commit()

def get_latest_article(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT content FROM daily_articles WHERE user_id={PL} ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

# --- DAILY NEWS ---
def save_daily_news(user_id, news_json):
    date = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(f"INSERT INTO daily_news (user_id, news_json, created_at) VALUES ({PL}, {PL}, {PL})", 
                       (user_id, news_json, date))
        conn.commit()

def get_daily_news(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT news_json FROM daily_news WHERE user_id={PL} ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

# --- FOCUS SESSIONS ---
def save_focus_session(user_id, duration_minutes, task_description=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(f"INSERT INTO focus_sessions (user_id, duration_minutes, task_description, completed_at) VALUES ({PL}, {PL}, {PL}, {PL})", 
                       (user_id, duration_minutes, task_description, timestamp))
        # Also add to rewards (XP)
        conn.execute(f"INSERT INTO user_rewards (user_id, reward_type, earned_at, duration_minutes) VALUES ({PL}, {PL}, {PL}, {PL})", 
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
        cursor.execute(f"""
            SELECT SUM(duration_minutes), COUNT(*) FROM focus_sessions 
            WHERE user_id={PL} AND completed_at >= {PL}
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
            cursor.execute(f"""
                SELECT SUM(duration_minutes) FROM focus_sessions 
                WHERE user_id={PL} AND completed_at LIKE {PL}
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
        cursor.execute(f"""
            SELECT strftime('%Y-%m-%d', completed_at) as day, 
                   COUNT(*) as completed,
                   COUNT(DISTINCT habit_id) as unique_habits
            FROM habit_completions
            WHERE user_id = {PL} AND completed_at >= {PL}
            GROUP BY day
            ORDER BY day
        """, (user_id, start_date.isoformat()))
        habits_data = cursor.fetchall()
        
        habit_completion_rate = 0
        if habits_data:
            total_daily = sum(row[1] for row in habits_data)
            habit_completion_rate = round((total_daily / (len(habits_data) * 5)) * 100, 1) if len(habits_data) > 0 else 0
        
        # 2. FOCUS SESSIONS
        cursor.execute(f"""
            SELECT strftime('%Y-%m-%d', started_at) as day,
                   SUM(duration_minutes) as total_minutes,
                   COUNT(*) as sessions,
                   AVG(focus_score) as avg_score,
                   strftime('%H', started_at) as hour
            FROM focus_sessions
            WHERE user_id = {PL} AND started_at >= {PL}
            GROUP BY day
        """, (user_id, start_date.isoformat()))
        focus_data = cursor.fetchall()
        
        total_focus_minutes = sum(row[1] or 0 for row in focus_data)
        total_focus_sessions = sum(row[2] or 0 for row in focus_data)
        avg_focus_score = round(sum(row[3] or 0 for row in focus_data) / len(focus_data), 1) if focus_data else 0
        
        # 3. DAILY TASKS
        cursor.execute(f"""
            SELECT strftime('%Y-%m-%d', created_at) as day,
                   COUNT(*) as total,
                   SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
            FROM daily_tasks
            WHERE user_id = {PL} AND created_at >= {PL}
            GROUP BY day
        """, (user_id, start_date.isoformat()))
        tasks_data = cursor.fetchall()
        
        total_tasks = sum(row[1] or 0 for row in tasks_data)
        completed_tasks = sum(row[2] or 0 for row in tasks_data)
        task_completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        
        # 4. AI DAILY TASKS
        cursor.execute(f"""
            SELECT task_date,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status = 'rolled_over' THEN 1 ELSE 0 END) as rolled
            FROM ai_daily_tasks
            WHERE user_id = {PL} AND task_date >= {PL}
            GROUP BY task_date
        """, (user_id, start_date.date().isoformat()))
        ai_tasks_data = cursor.fetchall()
        
        total_ai_tasks = sum(row[1] or 0 for row in ai_tasks_data)
        completed_ai_tasks = sum(row[2] or 0 for row in ai_tasks_data)
        rolled_ai_tasks = sum(row[3] or 0 for row in ai_tasks_data)
        ai_task_completion_rate = round((completed_ai_tasks / total_ai_tasks * 100), 1) if total_ai_tasks > 0 else 0
        
        # 5. ACTIVITY TIMESTAMPS (for pattern detection)
        cursor.execute(f"""
            SELECT strftime('%H', completed_at) as hour, COUNT(*) as activity_count
            FROM (
                SELECT completed_at as created_at FROM habit_completions WHERE user_id = {PL} AND completed_at >= {PL}
                UNION ALL
                SELECT started_at as created_at FROM focus_sessions WHERE user_id = {PL} AND started_at >= {PL}
                UNION ALL
                SELECT created_at FROM daily_tasks WHERE user_id = {PL} AND created_at >= {PL}
            )
            GROUP BY hour
            ORDER BY activity_count DESC
            LIMIT 3
        """, (user_id, start_date.isoformat(), user_id, start_date.isoformat(), user_id, start_date.isoformat()))
        peak_hours = cursor.fetchall()
        
        # 6. CHAT ACTIVITY
        cursor.execute(f"""
            SELECT COUNT(*) as messages
            FROM chat_history
            WHERE user_id = {PL} AND timestamp >= {PL}
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
            f"INSERT INTO ai_daily_tasks (user_id, task_content, task_date, status, created_at) VALUES ({PL}, {PL}, {PL}, 'pending', {PL})",
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
            f"SELECT id, task_content, status, created_at, completed_at FROM ai_daily_tasks WHERE user_id={PL} AND task_date={PL} ORDER BY id ASC",
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
            f"UPDATE ai_daily_tasks SET status='completed', completed_at={PL} WHERE id={PL}",
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
            f"SELECT id, task_content FROM ai_daily_tasks WHERE user_id={PL} AND task_date={PL} AND status='pending' ORDER BY id ASC",
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
            f"SELECT user_id, task_content FROM ai_daily_tasks WHERE task_date={PL} AND status='pending'",
            (yesterday,)
        )
        incomplete_tasks = cursor.fetchall()
        
        # Mark old tasks as rolled_over
        cursor.execute(
            f"UPDATE ai_daily_tasks SET status='rolled_over' WHERE task_date={PL} AND status='pending'",
            (yesterday,)
        )
        
        # Create new tasks for today
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for user_id, task_content in incomplete_tasks:
            cursor.execute(
                f"INSERT INTO ai_daily_tasks (user_id, task_content, task_date, status, created_at) VALUES ({PL}, {PL}, {PL}, 'pending', {PL})",
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
            f"DELETE FROM ai_daily_tasks WHERE user_id={PL} AND task_date={PL}",
            (user_id, task_date)
        )
        conn.commit()


# --- IN-APP REMINDERS ---

def save_reminder(user_id, content, trigger_at):
    """Save a reminder that will fire at trigger_at (ISO string)"""
    with get_db() as conn:
        conn.execute(
            f"INSERT INTO reminders (user_id, content, trigger_at, triggered, dismissed, created_at) VALUES ({PL}, {PL}, {PL}, 0, 0, {PL})",
            (user_id, content, trigger_at, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

def get_pending_reminders(user_id):
    """Get reminders that have fired (trigger_at <= now) but not dismissed"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, content, trigger_at, created_at FROM reminders WHERE user_id={PL} AND trigger_at <= {PL} AND dismissed=0",
            (user_id, now)
        )
        rows = cursor.fetchall()
        return [{'id': r[0], 'content': r[1], 'trigger_at': r[2], 'created_at': r[3]} for r in rows]

def dismiss_reminder(reminder_id):
    """Mark a reminder as dismissed"""
    with get_db() as conn:
        conn.execute(f"UPDATE reminders SET dismissed=1, triggered=1 WHERE id={PL}", (reminder_id,))
        conn.commit()

