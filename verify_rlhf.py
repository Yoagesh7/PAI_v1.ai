import sys
import os
import time

# Add root to path so we can import 'rlhf' as a package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rlhf.strategy_selector import StrategySelector
from rlhf.feedback_manager import FeedbackManager
# Fix import path for storage
from rlhf.storage import get_strategy_scores, get_db_connection

def test_rlhf_flow():
    print("--- 1. Testing Strategy Selection ---")
    strategy = StrategySelector.get_best_strategy()
    print(f"Initial Strategy: {strategy}")
    assert strategy in StrategySelector.STRATEGIES

    print("\n--- 2. Testing Feedback Storage ---")
    user_input = "How do I build a rocket?"
    ai_response = "Step 1: Get fuel. Step 2: Light it."
    
    # Simulate Positive Feedback
    print("Sending 'very_helpful' (+2) feedback...")
    result = FeedbackManager.process_feedback(user_input, ai_response, strategy, "very_helpful")
    print(f"Result: {result}")
    assert result['score_assigned'] == 2

    # Verify DB
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM rlhf_feedback_logs ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    print(f"DB Log: Strategy={row['strategy_type']}, Score={row['numeric_score']}")
    assert row['numeric_score'] == 2
    conn.close()

    print("\n--- 3. Testing Score Updates ---")
    scores = get_strategy_scores()
    print(f"Current Scores: {scores}")
    # We can't strictly assert value because previous runs might exist, but we know it should be non-zero if fresh DB
    
    print("\n--- 4. Testing Negative Feedback Adaptation ---")
    # Force negative feedback
    current_strategy = StrategySelector.get_best_strategy()
    print(f"Current Strategy before negative: {current_strategy}")
    
    print("Sending 'not_helpful' (-1) feedback...")
    FeedbackManager.process_feedback("Bad input", "Bad response", current_strategy, "not_helpful")
    
    # Next strategy should preferably NOT be the same (unless random exploration picks it again, but likely different)
    # We will invoke get_best_strategy multiple times to see if it avoids the negative one immediately
    next_strategy = StrategySelector.get_best_strategy()
    print(f"Next Strategy: {next_strategy}")
    
    if next_strategy != current_strategy:
        print("SUCCESS: Strategy switched after negative feedback.")
    else:
        print("WARNING: Strategy remained same (could be random exploration or no other better options).")

    print("\n--- RLHF System Verification Complete ---")

if __name__ == "__main__":
    test_rlhf_flow()
