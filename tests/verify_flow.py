import requests
import sys

BASE_URL = "http://localhost:5000"

def verify_flow():
    session = requests.Session()
    
    # 1. Login/Create User
    print("Step 1: Logging in...", flush=True)
    # Using a test user
    username = "flow_tester_v2" # New user to force Day 1
    password = "password"
    
    # Try login
    try:
        res = session.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
        if res.status_code != 200:
            print(f"Login failed ({res.status_code}). Attempting signup...")
            res_signup = session.post(f"{BASE_URL}/api/signup", json={"username": username, "password": password})
            if res_signup.status_code == 200:
                print("Signup successful. Logging in again...")
                res = session.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
            else:
                print(f"Signup failed: {res_signup.text}")
                return
        
        if res.status_code == 200:
             print("Login successful.")
        else:
             print(f"Login still failed: {res.text}")
             return

    except Exception as e:
        print(f"Connection Error: {e}")
        return

    # 2. Clear existing tasks (Simulate new day/user)
    print("Step 2: Checking for Day 1 Tasks...")
    try:
        res = session.get(f"{BASE_URL}/api/daily")
        tasks = res.json()
        
        if not tasks:
            print("INFO: No tasks returned. Force creating via /api/daily logic check...")
            # The logic in app.py runs on GET, so if valid user + no tasks + flow_day <= 14, it should create them.
            # If it didn't, maybe flow_day > 14 or user has tasks already?
            # Let's inspect user profile if possible or just assume it worked?
            pass
        
        # Re-fetch just in case
        res = session.get(f"{BASE_URL}/api/daily")
        tasks = res.json()
        
        print(f"Current Tasks: {[t.get('task', 'Unknown') for t in tasks]}")
        
        day1_task = "Drink a glass of water immediately upon waking up"
        found_task = False
        for t in tasks:
            if day1_task in t.get('task', ''):
                found_task = True
                break
        
        if found_task:
            print("SUCCESS: Day 1 Flow Task Detected.")
        else:
            print("WARNING: Day 1 Flow Task NOT detected.")
            
    except Exception as e:
        print(f"Error checking tasks: {e}")
        return

    # 3. Simulate Completion
    print("Step 3: Completing all tasks...")
    completed_count = 0
    for t in tasks:
        print(f"Completing: {t.get('task', 'Unknown')}")
        res = session.post(f"{BASE_URL}/api/daily/{t['id']}/toggle", json={"status": True})
        if res.status_code == 200:
            completed_count += 1
            
    print(f"Completed {completed_count}/{len(tasks)} tasks.")
    
    # 4. Verify Flow Day Increment
    print("Step 4: Checking Chat for Success Message...")
    try:
        res = session.get(f"{BASE_URL}/api/init")
        data = res.json()
        history = data.get('history', [])
        
        success_msg = "Day 1 Complete"
        found_msg = False
        for msg in history:
            content = msg.get('content', '')
            if success_msg in content:
                print(f"SUCCESS: Found completion message: {content}")
                found_msg = True
                break
        
        if not found_msg:
             print("WARNING: Completion message not found in chat history.")
             
    except Exception as e:
        print(f"Error checking chat: {e}")

if __name__ == "__main__":
    verify_flow()
