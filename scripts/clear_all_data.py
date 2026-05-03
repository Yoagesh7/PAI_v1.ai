"""Utility script to clear user data from the PartnerAI SQLite database.
Run this locally (it will DELETE data)."""
from memory import get_db

def clear_all():
    tables = [
        'users','chat_history','community_posts','groups','group_members','group_tasks',
        'daily_tasks','daily_articles','daily_news','user_rewards','ai_user_memory',
        'smart_blocks','block_relationships','knowledge_blocks','focus_sessions','ai_daily_tasks',
        'reminders','signup_verifications','login_verifications'
    ]
    with get_db() as conn:
        cur = conn.cursor()
        for t in tables:
            try:
                cur.execute(f"DELETE FROM {t}")
                print(f"Cleared {t}")
            except Exception as e:
                print(f"Could not clear {t}: {e}")
        conn.commit()

if __name__ == '__main__':
    confirm = input("This will delete ALL user data. Type 'YES' to continue: ")
    if confirm == 'YES':
        clear_all()
        print('All data cleared.')
    else:
        print('Aborted.')
