"""
AI Daily Task Email Reminders and Scheduling System
"""
from datetime import datetime
from memory import (
    get_all_active_users, get_ai_tasks_for_date, 
    get_incomplete_ai_tasks, rollover_incomplete_tasks
)

def send_email(to_email, subject, body):
    """Email sending function (imported from app.py)"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "dreamsyncai07@gmail.com"
    EMAIL_PASSWORD = "whcvbcvflkgsnicj"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}", flush=True)
        return True
    except Exception as e:
        print(f"❌ Email failed to {to_email}: {e}", flush=True)
        return False

def send_morning_reminders():
    """Send morning task reminders to all active users at 8:30 AM"""
    print("🌅 Running morning reminder job...", flush=True)
    users = get_all_active_users()
    
    import random
    motivational_quotes = [
        "Every morning is a fresh start. Make today count!",
        "Success is the sum of small efforts repeated day in and day out.",
        "The secret of getting ahead is getting started.",
        "Don't wait for opportunity. Create it!",
        "Your only limit is you."
    ]
    
    for user in users:
        try:
            tasks = get_ai_tasks_for_date(user['user_id'])
            if not tasks:
                continue  # Skip users with no tasks
            
            task_list = "\n".join([f"✅ {task['task']}" for task in tasks])
            quote = random.choice(motivational_quotes)
            
            subject = f"🌅 Good Morning {user['name']}! Your Tasks for Today"
            body = f"""Hey {user['name']}!

Hope you're ready for an amazing day! 🚀

Here are your AI-recommended tasks for {datetime.now().strftime('%B %d, %Y')}:

{task_list}

💪 {quote}

Let's crush it today!

- PartnerAI
"""
            
            send_email(user['email'], subject, body)
            
        except Exception as e:
            print(f"Error sending morning email to {user['email']}: {e}", flush=True)
    
    print(f"✅ Morning reminders sent to {len(users)} users", flush=True)

def send_incomplete_reminders():
    """Send evening reminders for incomplete tasks at 8:00 PM"""
    print("⏰ Running incomplete task reminder job...", flush=True)
    users = get_all_active_users()
    sent_count = 0
    
    motivational_messages = [
        "Don't worry if you didn't finish everything today. Progress, not perfection! 💪",
        "Remember: Every step forward counts, even if it's small. Keep pushing! 🔥",
        "It's okay to have tasks carry over. What matters is that you keep showing up! 🌟",
        "Tomorrow is another opportunity. These tasks will be waiting for you! 🚀"
    ]
    
    for user in users:
        try:
            incomplete = get_incomplete_ai_tasks(user['user_id'])
            
            if not incomplete:
                continue  # Only send if there are incomplete tasks
            
            task_list = "\n".join([f"⚠️ {task['task']}" for task in incomplete])
            motivation = motivational_messages[sent_count % len(motivational_messages)]
            
            subject = f"⏰ {user['name']}, You Still Have Tasks Pending!"
            body = f"""Hey {user['name']},

I noticed you haven't completed all your tasks today:

{task_list}

{motivation}

These will automatically carry over to tomorrow along with new tasks!

Keep pushing! 💪

- PartnerAI
"""
            
            send_email(user['email'], subject, body)
            sent_count += 1
            
        except Exception as e:
            print(f"Error sending incomplete reminder to {user['email']}: {e}", flush=True)
    
    print(f"✅ Incomplete reminders sent to {sent_count} users", flush=True)

def run_midnight_rollover():
    """Roll over incomplete tasks at midnight"""
    print("🌙 Running midnight task rollover...", flush=True)
    try:
        count = rollover_incomplete_tasks()
        print(f"✅ Rolled over {count} incomplete tasks to today", flush=True)
    except Exception as e:
        print(f"❌ Rollover failed: {e}", flush=True)

# APScheduler setup
def init_scheduler(app):
    """Initialize background scheduler for automated tasks"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BackgroundScheduler()
    
    # Daily 8:30 AM IST - Morning reminders
    scheduler.add_job(
        send_morning_reminders,
        CronTrigger(hour=8, minute=30, timezone='Asia/Kolkata'),
        id='morning_reminders',
        name='Send morning task reminders',
        replace_existing=True
    )
    
    # Daily 8:00 PM IST - Evening incomplete reminders
    scheduler.add_job(
        send_incomplete_reminders,
        CronTrigger(hour=20, minute=0, timezone='Asia/Kolkata'),
        id='evening_reminders',
        name='Send incomplete task remind ers',
        replace_existing=True
    )
    
    # Daily midnight - Task rollover
    scheduler.add_job(
        run_midnight_rollover,
        CronTrigger(hour=0, minute=0, timezone='Asia/Kolkata'),
        id='midnight_rollover',
        name='Rollover incomplete tasks',
        replace_existing=True
    )
    
    scheduler.start()
    print("🔄 Scheduler initialized with 3 jobs:", flush=True)
    print("  - Morning reminders: 8:30 AM", flush=True)
    print("  - Evening reminders: 8:00 PM", flush=True)
    print("  - Midnight rollover: 12:00 AM", flush=True)
    
    return scheduler
