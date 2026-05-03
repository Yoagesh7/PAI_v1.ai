import os
import sys
from datetime import datetime, timedelta

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory import get_user, save_chat_message, get_chat_history
from nvidia_llm import rag_system
from rlhf.strategy_selector import StrategySelector
from rag_engine_cloud import build_rag_context

def simulate_chat(user_id, text):
    print(f"Simulating chat for user {user_id} with text: {text}")
    
    # 1. Save user message
    save_chat_message(user_id, 'user', text)
    print("User message saved.")
    
    # 2. Get user
    user = get_user(user_id)
    if not user:
        print("User not found.")
        return
    
    name = user[1]
    career = user[2]
    goal = career or "General Productivity"
    
    # 3. Build context
    try:
        rag_context = build_rag_context(user_id, text, user_goal=goal)
        print(f"RAG context built (len={len(rag_context)})")
    except Exception as e:
        print(f"RAG Error: {e}")
        rag_context = ""

    # 4. Strategy
    selected_strategy = StrategySelector.get_best_strategy()
    print(f"Strategy: {selected_strategy}")
    
    # 5. Prompt
    system_prompt = f"You are PartnerAI. User goal: {goal}. Context: {rag_context}"
    
    # 6. History
    raw_history = get_chat_history(user_id, limit=14)
    history_messages = []
    for h in raw_history[:-1]:
        role = 'assistant' if h['role'] == 'ai' else 'user'
        content = h['content']
        # The bugged condition from app.py
        if content and len(content.strip()) > 0 and not content.startswith('') and len(content) < 1200:
            history_messages.append({"role": role, "content": content})
    
    print(f"History messages: {len(history_messages)}")
    
    messages_to_send = (
        [{"role": "system", "content": system_prompt}]
        + history_messages
        + [{"role": "user", "content": text}]
    )
    
    # 7. LLM Call
    print("Calling LLM...")
    try:
        response = rag_system.generate_response(messages=messages_to_send)
        ai_reply = response['message']['content']
        print(f"AI Reply: {ai_reply[:100]}...")
        
        # 8. Save AI message
        save_chat_message(user_id, 'ai', ai_reply)
        print("AI message saved.")
    except Exception as e:
        print(f"LLM Error: {e}")

if __name__ == "__main__":
    # Use a user_id that exists. I'll check user_id 1.
    simulate_chat(1, "hi")
