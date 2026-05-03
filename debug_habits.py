import sqlite3
import os

DB_PATH = 'partnerai.db'

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n--- Habits Columns ---")
    try:
        cursor.execute("PRAGMA table_info(habits)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[1]} ({col[2]})")
            
        print("\n--- Existing Habits ---")
        cursor.execute("SELECT * FROM habits")
        rows = cursor.fetchall()
        if not rows:
            print("No habits found in DB.")
        else:
            for r in rows:
                print(r)
                
    except Exception as e:
        print(f"Error reading DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db()
