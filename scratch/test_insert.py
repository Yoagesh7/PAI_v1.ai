import sqlite3
import datetime

conn = sqlite3.connect('partnerai.db')
cursor = conn.cursor()
try:
    cursor.execute(
        "INSERT INTO signup_verifications (username, password, email, code, expires_at) VALUES (?, ?, ?, ?, ?)",
        ("test", "test", "test@example.com", "123456", datetime.datetime.now())
    )
    conn.commit()
    print("Insert successful")
except Exception as e:
    print(f"Insert failed: {e}")
conn.close()
