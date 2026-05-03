import requests
import json

BASE_URL = "http://localhost:5000"

def verify_chat():
    session = requests.Session()
    
    # Login
    print("Logging in...", flush=True)
    username = "chat_tester"
    password = "password"
    session.post(f"{BASE_URL}/api/login", json={"username": username, "password": password})
    
    # Send "hi"
    print("Sending 'hi' to chat...", flush=True)
    try:
        res = session.post(f"{BASE_URL}/api/chat", json={"message": "hi"})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        
        if "Plan for: hi" in res.text:
            print("FAILED: Still receiving heuristic plan.")
        else:
            print("SUCCESS: Received AI response (likely).")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_chat()
