import os
import sys

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory import get_db

def migrate_production():
    print("Running production migration...")
    
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL is not set. Please set it to your Supabase URL.")
        return

    columns_to_add = [
        ('users', 'career', 'TEXT', None),
        ('users', 'hobbies', 'TEXT', None),
        ('users', 'last_task', 'TEXT', None),
        ('users', 'task_status', 'TEXT', None),
        ('users', 'state', 'TEXT', None),
        ('users', 'tasks_completed', 'INTEGER', 0),
        ('users', 'streak', 'INTEGER', 0),
        ('users', 'last_active_date', 'TEXT', None),
        ('users', 'daily_topic', 'TEXT', None),
        ('users', 'work_time', 'TEXT', None),
        ('users', 'free_time', 'TEXT', None),
        ('users', 'age', 'TEXT', None),
        ('users', 'last_task_date', 'TEXT', None),
        ('users', 'username', 'TEXT', None),
        ('users', 'password', 'TEXT', None),
        ('users', 'email', 'TEXT', None),
        ('users', 'flow_day', 'INTEGER', 0)
    ]

    with get_db() as conn:
        cursor = conn.cursor()
        for table, col, col_type, default in columns_to_add:
            print(f"Adding column {col} to {table}...")
            try:
                if default is not None:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}")
                else:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                conn.commit()
                print(f"  Successfully added {col}")
            except Exception as e:
                err_msg = str(e).lower()
                if "already exists" in err_msg or "duplicate column" in err_msg:
                    print(f"  Column {col} already exists.")
                else:
                    print(f"  Error adding {col}: {e}")

    print("\nMigration complete.")

if __name__ == "__main__":
    migrate_production()
