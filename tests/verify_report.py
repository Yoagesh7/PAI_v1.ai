import requests
import json

BASE_URL = "http://127.0.0.1:5000"
SESSION_COOKIE = None

def login():
    global SESSION_COOKIE
    print("Logging in...", flush=True)
    # Using a known test user or creating one would be best, but we'll try to use existing session if possible or login
    # For now, let's assume we need to login as 'yo405' if it exists, or create.
    # Actually, let's just use the 'test_habits.py' approach of creating a session.
    
    # Login as a test user
    s = requests.Session()
    # The app uses /api/login (POST) which returns JSON
    try:
        res = s.post(f"{BASE_URL}/api/login", json={"username": "test_report", "password": "password"})
        
        if res.status_code != 200:
             # Try signup
             print("Login failed, trying signup...", flush=True)
             res = s.post(f"{BASE_URL}/api/signup", json={"username": "test_report", "password": "password", "email": "test@test.com"})
        
        if res.status_code == 200:
            print("Login/Signup successful.")
            return s
        else:
            print(f"Login failed: {res.text}")
            return None
    except Exception as e:
        print(f"Login Exception: {e}")
        return None

def verify_report():
    session = login()
    if not session: return

    # 1. Simulate Focus Session
    print("Simulating Focus Session...", flush=True)
    res = session.post(f"{BASE_URL}/api/focus/complete", json={"duration": 45, "task": "Report Testing"})
    print(f"Focus Save Status: {res.status_code}")
    print(f"Focus Save Response: {res.text}")
    
    if res.status_code != 200:
        print("Failed to save focus session.")
        return

    # 2. Get Report Page
    print("Fetching Report Page...", flush=True)
    res = session.get(f"{BASE_URL}/report")
    print(f"Report Status: {res.status_code}")
    
    if "Weekly Performance Report" in res.text:
        print("✅ Report Page Loaded Successfully.")
    else:
        print("❌ Report Page Load Failed.")
        
    if "45m" in res.text or "45" in res.text:
         print("✅ Focus Data found in Report.")
    else:
         print("❌ Focus Data NOT found in Report.")

    if "Top Strength" in res.text:
         print("✅ AI Section found.")
    
if __name__ == "__main__":
    verify_report()
