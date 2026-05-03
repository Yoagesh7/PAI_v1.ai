import logging
from memory import get_db

TABLES_TO_CLEAR = [
    'users',
    'chat_history',
    'community_posts',
    'groups',
    'group_members',
    'group_tasks',
    'daily_tasks',
    'daily_articles',
    'daily_news',
    'user_rewards',
    'ai_user_memory',
    'smart_blocks',
    'block_relationships',
    'knowledge_blocks',
    'focus_sessions',
    'ai_daily_tasks',
    'reminders',
    'signup_verifications',
    'login_verifications',
]


def wipe_all_user_data():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    with get_db() as conn:
        cursor = conn.cursor()
        for table in TABLES_TO_CLEAR:
            try:
                cursor.execute(f'DELETE FROM {table}')
                logging.info(f'Cleared table: {table}')
            except Exception as e:
                logging.warning(f'Could not clear {table}: {e}')
        conn.commit()
    logging.info('Done. All user data cleared.')


if __name__ == '__main__':
    wipe_all_user_data()
