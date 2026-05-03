import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_signup():
    print("Testing signup...")
    payload = {
        "username": "testuser_" + str(int(1000 * 1000 * 1000)),
        "password": "password123",
        "email": "test@example.com"
    }
    res = requests.post(f"{BASE_URL}/api/signup", json=payload)
    print(f"Signup Status: {res.status_code}")
    print(f"Signup Response: {res.text}")

if __name__ == "__main__":
    try:
        test_signup()
    except Exception as e:
        print(f"Error: {e}")
