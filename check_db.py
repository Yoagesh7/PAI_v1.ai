
import sqlite3
import os

DB_NAME = "partnerai.db"

def check_db():
    if not os.path.exists(DB_NAME):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("--- Users Table ---")
    cursor.execute("PRAGMA table_info(users)")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Habits Table ---")
    cursor.execute("PRAGMA table_info(habits)")
    for row in cursor.fetchall():
        # Encode to ascii to avoid terminal crashes with emojis
        safe_row = [str(col).encode('ascii', 'ignore').decode() if isinstance(col, str) else col for col in row]
        print(safe_row)
        
    print("\n--- Habit Completions Table ---")
    cursor.execute("PRAGMA table_info(habit_completions)")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_db()
