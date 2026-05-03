import requests

BASE_URL = "http://127.0.0.1:5000"

def test_chat_real():
    session = requests.Session()
    
    # 1. Login (assuming user 'yoagesh' exists)
    print("Logging in...")
    login_res = session.post(f"{BASE_URL}/api/login", json={"username": "yoagesh", "password": "password"})
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        # Try signup if login fails
        print("Trying signup...")
        signup_res = session.post(f"{BASE_URL}/api/signup", json={"username": "test", "password": "password", "email": "test@example.com"})
        print(f"Signup res: {signup_res.status_code} - {signup_res.text}")
        # Need to verify signup? Usually it sends OTP. 
        # But maybe skip this and use an existing user.
        return

    print("Login successful.")
    
    # 2. Send Chat
    print("Sending chat...")
    chat_res = session.post(f"{BASE_URL}/api/chat", json={"message": "hi"}, stream=True)
    print(f"Chat status: {chat_res.status_code}")
    
    if chat_res.status_code == 200:
        print("Response: ", end="", flush=True)
        for chunk in chat_res.iter_content(decode_unicode=True):
            print(chunk, end="", flush=True)
        print("\nChat successful.")
    else:
        print(f"Chat failed: {chat_res.text}")

if __name__ == "__main__":
    test_chat_real()
