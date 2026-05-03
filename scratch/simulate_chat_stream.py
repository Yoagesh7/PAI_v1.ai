import os
import sys
from datetime import datetime, timedelta

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory import get_user, save_chat_message, get_chat_history
from nvidia_llm import rag_system
from rlhf.strategy_selector import StrategySelector
from rag_engine_cloud import build_rag_context

def simulate_chat_stream(user_id, text):
    print(f"Simulating chat STREAM for user {user_id} with text: {text}")
    
    # 1. Save user message
    save_chat_message(user_id, 'user', text)
    
    # 2. Get user
    user = get_user(user_id)
    name = user[1]
    goal = user[2] or "General Productivity"
    
    # 3. Strategy
    selected_strategy = StrategySelector.get_best_strategy()
    
    # 4. Prompt
    system_prompt = f"You are PartnerAI. User goal: {goal}."
    
    messages_to_send = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    
    # 5. Stream
    print("Streaming tokens...")
    full_text = ""
    try:
        for token in rag_system.generate_response_stream(messages=messages_to_send):
            print(token, end="", flush=True)
            full_text += token
        print("\nStream finished.")
        
        # 6. Save AI message
        save_chat_message(user_id, 'ai', full_text)
        print("AI message saved.")
    except Exception as e:
        print(f"\nStream Error: {e}")

if __name__ == "__main__":
    simulate_chat_stream(1, "hi")
