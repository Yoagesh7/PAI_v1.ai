import sqlite3
conn = sqlite3.connect('partnerai.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(signup_verifications)")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
