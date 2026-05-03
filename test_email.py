import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIG ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "dreamsyncai07@gmail.com"
EMAIL_PASSWORD = "whcvbcvflkgsnicj"

TO_EMAIL = "haniffazalm@gmail.com"

def send_test_email():
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL
        msg['Subject'] = "PartnerAI Email Test"
        msg.attach(MIMEText("This is a test email from PartnerAI Debugger.", 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1) # Enable verbose debug
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, TO_EMAIL, text)
        server.quit()
        print(f"\nSUCCESS: Email successfully sent to {TO_EMAIL}")
    except Exception as e:
        print(f"\nFAILURE: Email failed: {e}")

if __name__ == "__main__":
    send_test_email()
