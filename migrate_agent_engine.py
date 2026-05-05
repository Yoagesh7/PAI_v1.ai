"""
Database Migration Script for Agent Actions Log
Adds the agent_actions_log table if it doesn't exist
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory import get_db


def migrate_agent_actions_log():
    """Create agent_actions_log table for autonomous agent logging."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Determine ID type
            is_pg = os.getenv("DATABASE_URL") is not None
            id_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
            
            # Create table
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
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_actions_user_timestamp 
                ON agent_actions_log(user_id, timestamp)
            """)
            
            conn.commit()
            print("✅ Migration: agent_actions_log table created/verified successfully")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("Running database migrations...")
    if migrate_agent_actions_log():
        print("✅ All migrations completed successfully")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        sys.exit(1)
