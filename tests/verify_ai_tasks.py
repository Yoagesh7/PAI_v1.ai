import requests
import json

BASE_URL = "http://localhost:5000"

def verify_ai_tasks():
    session = requests.Session()
    
    # Login
    print("Logging in...", flush=True)
    session.post(f"{BASE_URL}/api/login", json={"username": "task_tester", "password": "password"})
    
    # Generate Tasks
    print("Generating AI Tasks...", flush=True)
    try:
        # Test with a specific technical goal
        res = session.post(f"{BASE_URL}/api/ai-tasks", json={"goal": "Learn Python Basics", "time": "1 hour"})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        
        data = res.json()
        if 'tasks' in data and len(data['tasks']) == 3:
            print("SUCCESS: Received 3 tasks.")
        else:
            print("FAILED: Did not receive 3 tasks.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_ai_tasks()
