import sqlite3
import os

DB_PATH = 'partnerai.db'

def fix_schema():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Check existing columns
    cursor.execute("PRAGMA table_info(habits)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Existing columns: {columns}")
    
    # 2. Add missing columns
    needed_columns = {
        'user_id': 'INTEGER',
        'title': 'TEXT',
        'category': 'TEXT DEFAULT "General"',
        'icon': 'TEXT DEFAULT "📝"',
        'frequency': 'TEXT DEFAULT "Daily"',
        'time_of_day': 'TEXT DEFAULT "Anytime"',
        'streak': 'INTEGER DEFAULT 0',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
    
    for col, type_def in needed_columns.items():
        if col not in columns:
            print(f"Adding column: {col}...")
            try:
                cursor.execute(f"ALTER TABLE habits ADD COLUMN {col} {type_def}")
                print("Done.")
            except Exception as e:
                print(f"Failed to add {col}: {e}")
                
    conn.commit()
    print("Schema update complete.")
    conn.close()

if __name__ == "__main__":
    fix_schema()
