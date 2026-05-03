import sys
import os

# Add parent dir to path to find config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("--- DIAGNOSTIC START ---")

try:
    from config import MAIN_MODEL
    print(f"Configured Model (MAIN_MODEL): '{MAIN_MODEL}'")
except ImportError:
    MAIN_MODEL = "meta/llama-3.1-8b-instruct"
    print(f"WARNING: Could not import config.py. Defaulting to '{MAIN_MODEL}'")

try:
    from nvidia_llm import rag_system
    print(f"Attempting to chat with model '{MAIN_MODEL}'...")
    response = rag_system.generate_response([{'role': 'user', 'content': 'Hello, are you online? Respond with YES.'}])
    print("CONNECTION SUCCESSFUL!")
    print(f"AI Response: {response['message']['content']}")
except Exception as e:
    print("CONNECTION FAILED!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Details: {e}")

print("--- DIAGNOSTIC END ---")
