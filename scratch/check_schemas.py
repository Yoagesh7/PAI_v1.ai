import sqlite3
import os

db_path = 'partnerai.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = ['users', 'chat_history', 'signup_verifications', 'ai_daily_tasks', 'reminders']

for table in tables:
    print(f"--- Schema for {table} ---")
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
    row = cursor.fetchone()
    if row:
        print(row[0])
    else:
        print("Not found")

conn.close()
