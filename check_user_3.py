import sqlite3
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

DB_NAME = "partnerai.db"

def check_user_3():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=3")
    u = cursor.fetchone()
    conn.close()
    
    if u:
        # Assuming email is index 17 based on previous checks, but let's check schema again if needed.
        # Actually, let's just print the whole tuple cleanly
        print(f"User 3: {u}")
        
        # dynamic find
        cursor = sqlite3.connect(DB_NAME).cursor()
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'email' in cols:
             idx = cols.index('email')
             print(f"Email Column Index: {idx}")
             print(f"Email Value: {u[idx]}")
        else:
             print("Email column missing")

if __name__ == "__main__":
    check_user_3()
