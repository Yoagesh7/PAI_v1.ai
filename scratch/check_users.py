import sqlite3
conn = sqlite3.connect('partnerai.db')
cursor = conn.cursor()
cursor.execute("SELECT user_id, username, password FROM users LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
