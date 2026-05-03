import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# --- CONFIG ---
DB_NAME = "partnerai.db"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "dreamsyncai07@gmail.com"
EMAIL_PASSWORD = "whcvbcvflkgsnicj"

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        print(f" Email sent to {to_email}", flush=True)
        return True
    except Exception as e:
        print(f" Email failed for {to_email}: {e}", flush=True)
        return False

def main():
    print(" Starting Welcome Email Blast...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if email column exists by trying to select it
    # Schema check: index 17 was assumed, but better to select by name if possible.
    # The users table has named columns.
    
    try:
        cursor.execute("SELECT user_id, name, email, career FROM users")
        users = cursor.fetchall()
    except Exception as e:
        print(f"Error reading DB: {e}")
        return

    count = 0
    for user in users:
        user_id = user[0]
        name = user[1]
        email = user[2]
        goal = user[3] if user[3] else "your goals"
        
        if email and "@" in email:
            print(f"Preparing email for {name} ({email})...")
            
            subject = " Welcome to PartnerAI - Let's Crush Your Goals!"
            body = f"""Hi {name}!
            
Welcome to PartnerAI/PartnerAI! I'm thrilled to be your productivity partner. 

I see you're working on: "{goal}".
I'm ready to help you every step of the way.

Here's what you can do to get started:
1. Check your Dashboard for your daily tasks.
2. Use Focus Mode to crush your work sessions.
3. Chat with me anytime for advice or motivation.

Let's make it happen! 

- Your PartnerAI Mentor
"""
            if send_email(email, subject, body):
                count += 1
            
            # Avoid spamming rate limits
            time.sleep(1.5)
            
    print(f"\n Done! Sent {count} welcome emails.")
    conn.close()

if __name__ == "__main__":
    main()
