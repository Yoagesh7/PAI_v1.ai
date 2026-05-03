import requests
import sys

BASE_URL = "http://localhost:5000"
S = requests.Session()

def run_test():
    print(f"Testing against {BASE_URL}")
    
    # 1. Register/Login
    username = "debug_user_v2"
    password = "password123"
    email = "debug@test.com"
    
    # Try login first
    print("Logging in...")
    res = S.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    
    if "Dashboard" not in res.text and "Redirecting" not in res.text:
        # Try register
        print("Registering...")
        res = S.post(f"{BASE_URL}/register", data={"username": username, "password": password, "email": email, "confirm_password": password})
        
    # Check if logged in (session cookie)
    if not S.cookies:
        print(" Login Failed: No cookies")
        return
        
    print(" Logged In")
    
    # 2. Create Habit
    print("Creating Habit...")
    res = S.post(f"{BASE_URL}/api/habits", json={
        "title": "Persistence Test Habit",
        "category": "Test",
        "icon": "",
        "time_of_day": "Morning"
    })
    
    if res.status_code != 200:
        print(f" Create Failed: {res.text}")
        return
        
    habit_data = res.json()
    habit_id = habit_data.get('id')
    print(f" Created Habit ID: {habit_id}")
    
    # 3. Verify Initial State (Should be False)
    res = S.get(f"{BASE_URL}/api/habits")
    habits = res.json()
    my_habit = next((h for h in habits if h['id'] == habit_id), None)
    print(f"Initial State: {my_habit['completed_today']}")
    
    # 4. Toggle ON
    print("Toggling ON...")
    res = S.post(f"{BASE_URL}/api/habits/{habit_id}/toggle")
    print(f"Toggle Response: {res.json()}")
    
    # 5. Verify Persistence (Immediate)
    print("Verifying Immediate Persistence...")
    res = S.get(f"{BASE_URL}/api/habits")
    habits = res.json()
    my_habit = next((h for h in habits if h['id'] == habit_id), None)
    print(f"State After Toggle: {my_habit['completed_today']}")
    
    if my_habit['completed_today']:
        print(" PASSED: Server persisted state.")
    else:
        print(" FAILED: Server returned False after toggle!")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"CRASH: {e}")
