import sqlite3
from habits_db import get_user_habits
from memory import get_db

def verify():
    print("--- Users ---")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name FROM users")
        for r in cursor.fetchall():
            print(f"{r[0]}: {r[1]}")
            
    print("\n--- Habits for User 32 ---")
    habits = get_user_habits(32)
    print(f"Found {len(habits)} habits.")
    for h in habits:
        print(h)

if __name__ == "__main__":
    verify()
