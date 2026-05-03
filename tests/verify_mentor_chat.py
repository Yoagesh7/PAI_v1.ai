import requests
import json

BASE_URL = "http://localhost:5000"

def verify_mentor():
    session = requests.Session()
    
    # Login
    print("Logging in...", flush=True)
    session.post(f"{BASE_URL}/api/login", json={"username": "mentor_tester", "password": "password"})
    
    # Send a vague goal to trigger the mentor
    print("Sending 'I want to be productive'...", flush=True)
    res = session.post(f"{BASE_URL}/api/chat", json={"message": "I want to be productive"})
    print(f"Response: {res.text}", flush=True)
    
    if "?" in res.text:
        print("SUCCESS: AI asked a question.")
    else:
        print("WARNING: AI did not ask a question.")

if __name__ == "__main__":
    verify_mentor()
