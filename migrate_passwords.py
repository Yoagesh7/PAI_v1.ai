
import sqlite3
import os
import hashlib
import binascii

DB_NAME = "partnerai.db"

def _hash_password(password: str, iterations: int = 180000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f"pbkdf2_sha256${iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

def migrate_passwords():
    if not os.path.exists(DB_NAME):
        print(f"❌ Database {DB_NAME} not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, username, password FROM users")
    users = cursor.fetchall()
    
    migrated = 0
    for user_id, username, password in users:
        if '$' not in str(password):
            print(f"Migrating password for user: {username}")
            hashed = _hash_password(str(password))
            cursor.execute("UPDATE users SET password=? WHERE user_id=?", (hashed, user_id))
            migrated += 1
            
    conn.commit()
    conn.close()
    print(f"Migration complete. {migrated} passwords hashed.")

if __name__ == "__main__":
    migrate_passwords()
