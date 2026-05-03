class RewardEngine:
    SCORE_MAP = {
        "very_helpful": 2,
        "helpful": 1,
        "not_helpful": -1
    }

    @staticmethod
    def calculate_score(feedback_label):
        """
        Converts a text label into a numeric score.
        Defaults to 0 if unknown label.
        """
        return RewardEngine.SCORE_MAP.get(feedback_label, 0)

    @staticmethod
    def get_adjustment_factor(current_score, feedback_score):
        """
        Optional: Implement dampening or boosting logic here.
        For now, returns raw feedback score.
        """
        return feedback_score
