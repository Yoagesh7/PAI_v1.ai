import sqlite3
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

DB_NAME = "partnerai.db"

def list_users():
    if not os.path.exists(DB_NAME):
        print(f" Database {DB_NAME} not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(users)")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        
        email_idx = -1
        if 'email' in col_names:
            email_idx = col_names.index('email')
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        print(f"\nFound {len(users)} users:")
        for u in users:
            uid = u[0]
            name = u[1]
            email = u[email_idx] if email_idx != -1 and len(u) > email_idx else "N/A"
            
            print("--------------------------------------------------")
            print(f"ID:    {uid}")
            print(f"Name:  {name}")
            print(f"Email: {email}")
            print("--------------------------------------------------")
            sys.stdout.flush() 
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_users()
