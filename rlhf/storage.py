import sqlite3
import os
import datetime


def _default_db_path():
    if os.getenv("VERCEL"):
        return os.getenv("PARTNERAI_DB_PATH", "/tmp/partnerai.db")
    return os.getenv("PARTNERAI_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'partnerai.db'))


DB_PATH = _default_db_path()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_rlhf_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Feedback Logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS rlhf_feedback_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            ai_response TEXT,
            strategy_type TEXT,
            feedback_label TEXT,
            numeric_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Strategy Scores (Aggregated)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rlhf_strategy_scores (
            strategy_type TEXT PRIMARY KEY,
            total_score INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    
    # Initialize default strategies if empty
    strategies = [
        "direct_action", "step_by_step", "deep_explanation",
        "technical_breakdown", "motivational_push", "strategic_analysis"
    ]
    
    for s in strategies:
        c.execute('INSERT OR IGNORE INTO rlhf_strategy_scores (strategy_type, total_score, usage_count) VALUES (?, 0, 0)', (s,))

    conn.commit()
    conn.close()

def log_feedback(user_input, ai_response, strategy_type, feedback_label, numeric_score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO rlhf_feedback_logs 
        (user_input, ai_response, strategy_type, feedback_label, numeric_score)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_input, ai_response, strategy_type, feedback_label, numeric_score))
    conn.commit()
    conn.close()

def update_strategy_score(strategy_type, score_delta):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE rlhf_strategy_scores
        SET total_score = total_score + ?, usage_count = usage_count + 1
        WHERE strategy_type = ?
    ''', (score_delta, strategy_type))
    conn.commit()
    conn.close()

def get_strategy_scores():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT strategy_type, total_score FROM rlhf_strategy_scores')
    rows = c.fetchall()
    conn.close()
    return {row['strategy_type']: row['total_score'] for row in rows}

# Initialize on import to ensure tables exist
init_rlhf_db()
