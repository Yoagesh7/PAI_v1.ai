import os
import sys
from datetime import datetime

# Add root to path to import memory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory import get_db

def wipe_everything():
    print("CRITICAL: You are about to wipe ALL user data and accounts.")
    # In this environment, we'll bypass interactive input and just do it if run with --force
    force = "--force" in sys.argv
    
    if not force:
        print("Please run with --force to confirm deletion.")
        return

    tables = [
        'users', 'chat_history', 'community_posts', 'groups', 'group_members', 'group_tasks',
        'daily_tasks', 'daily_articles', 'daily_news', 'user_rewards', 'ai_user_memory',
        'smart_blocks', 'block_relationships', 'knowledge_blocks', 'focus_sessions', 'ai_daily_tasks',
        'reminders', 'signup_verifications', 'login_verifications', 'password_resets', 'group_chat_messages'
    ]

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            for table in tables:
                print(f"Dropping {table}...")
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                except Exception as e:
                    print(f"   (Failed {table}: {e})")
            
            conn.commit()
            print("\nSUCCESS: All user data and accounts have been wiped.")
            
    except Exception as e:
        print(f"Error during wipe: {e}")

if __name__ == "__main__":
    wipe_everything()
