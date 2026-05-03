import requests
import json

BASE_URL = "http://localhost:5000"

def verify_insights():
    session = requests.Session()
    
    print("Step 1: Logging in...", flush=True)
    username = "insight_tester"
    password = "password"
    
    # Try login/signup
    res = session.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
    if res.status_code != 200:
        session.post(f"{BASE_URL}/api/signup", json={"username": username, "password": password})
        session.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
    
    print("Step 2: Calling /api/habits/insights (POST)...", flush=True)
    payload = {
        "habits": [{"name": "Exercise"}, {"name": "Read"}],
        "stats": {"currentStreak": 5, "completionRate": 80}
    }
    
    try:
        res = session.post(f"{BASE_URL}/api/habits/insights", json=payload)
        
        print(f"Status: {res.status_code}", flush=True)
        if res.status_code == 200:
            print("Response:", flush=True)
            print(json.dumps(res.json(), indent=2), flush=True)
            print("SUCCESS: Insights received.", flush=True)
        else:
            print(f"FAILED: {res.text}", flush=True)
            
    except Exception as e:
        print(f"Request Error: {e}", flush=True)

if __name__ == "__main__":
    verify_insights()
