from .storage import log_feedback, update_strategy_score
from .reward_engine import RewardEngine
from .strategy_selector import StrategySelector

class FeedbackManager:
    @staticmethod
    def process_feedback(user_input, ai_response, strategy_type, feedback_label):
        """
        Main entry point for recording feedback.
        1. Calculate Score
        2. Log to DB
        3. Update Strategy Score
        4. Inform Selector of Negative Feedback
        """
        # 1. Calculate
        score = RewardEngine.calculate_score(feedback_label)
        
        # 2. Log
        log_feedback(user_input, ai_response, strategy_type, feedback_label, score)
        
        # 3. Update Aggregates
        update_strategy_score(strategy_type, score)
        
        # 4. Handle Negative Logic
        if score < 0:
            StrategySelector.mark_negative_feedback()
            
        return {
            "status": "success",
            "score_assigned": score,
            "strategy_adjusted": strategy_type
        }
