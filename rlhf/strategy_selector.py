import random
from .storage import get_strategy_scores

class StrategySelector:
    STRATEGIES = [
        "direct_action",
        "step_by_step",
        "deep_explanation",
        "technical_breakdown",
        "motivational_push",
        "strategic_analysis"
    ]

    last_strategy = None
    last_feedback_negative = False

    @classmethod
    def get_best_strategy(cls):
        """
        Selects the best strategy based on:
        1. Highest score (exploitation)
        2. Random exploration (epsilon-greedy-ish, kept simple)
        3. Negative feedback avoidance
        """
        scores = get_strategy_scores()

        # Filter out last strategy if it received negative feedback
        available_strategies = cls.STRATEGIES.copy()
        if cls.last_feedback_negative and cls.last_strategy in available_strategies:
            available_strategies.remove(cls.last_strategy)
            # Reset flag after handling
            cls.last_feedback_negative = False
        
        # Sort available by score descending
        # Default 0 if not found
        ranked = sorted(available_strategies, key=lambda s: scores.get(s, 0), reverse=True)
        
        # Simple Logic: 80% Top Score, 20% Random Exploration
        import random
        if random.random() < 0.2:
            selected = random.choice(available_strategies)
        else:
            selected = ranked[0]
            
        cls.last_strategy = selected
        return selected

    @classmethod
    def mark_negative_feedback(cls):
        """
        Signals that the last strategy failed.
        """
        cls.last_feedback_negative = True

    @staticmethod
    def get_prompt_instruction(strategy_type):
        """
        Returns the system instruction for the selected strategy.
        """
        instructions = {
            "direct_action": "Provide a direct, no-nonsense answer. Focus on immediate action and results. Avoid fluff.",
            "step_by_step": "Break down the solution into clear, numbered steps. Ensure each step is easy to follow.",
            "deep_explanation": "Provide a comprehensive and detailed explanation. Cover the 'why' and 'how' in depth.",
            "technical_breakdown": "Focus on the technical details, code structure, and underlying mechanics. Use technical terminology.",
            "motivational_push": "Be encouraging and high-energy. Focus on motivating the user to take action. Use emojis.",
            "strategic_analysis": "Analyze the situation from a high-level perspective. Discuss pros, cons, and long-term implications."
        }
        return instructions.get(strategy_type, "Answer clearly and concisely.")
