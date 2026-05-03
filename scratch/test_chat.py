import requests
import json

def test_chat():
    url = "http://127.0.0.1:5000/api/chat"
    payload = {
        "message": "hi",
        "deep_think": False
    }
    
    # We need a session. Since we're testing locally, we might need to log in first
    # or manually set a session cookie.
    # But let's see if it fails with 401 first as expected.
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chat()
