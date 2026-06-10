import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
# --- CONFIG ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "dreamsyncai07@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "whcvbcvflkgsnicj")

TO_EMAIL = os.getenv("TO_EMAIL", "haniffazalm@gmail.com")

def send_test_email():
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL
        msg['Subject'] = "PartnerAI Email Test (Forced IPv4)"
        msg.attach(MIMEText("This is a test email from PartnerAI Debugger with forced IPv4 resolution.", 'plain'))

        # Force IPv4
        try:
            resolved_ip = socket.gethostbyname(SMTP_SERVER)
            print(f"Resolved {SMTP_SERVER} to IPv4: {resolved_ip}")
            server = smtplib.SMTP(resolved_ip, SMTP_PORT, timeout=10)
            server.set_debuglevel(1)
            server.host = SMTP_SERVER # Force SSL to verify domain
            server.starttls()
        except Exception as dns_err:
            print(f"Forced IPv4 resolution failed: {dns_err}. Falling back to default.")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.set_debuglevel(1)
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
