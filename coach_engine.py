
def create_weekly_report(user_id):
    """
    Generate a deterministic weekly report.
    """
    # In a real app, this would query the DB for actual stats.
    # For this No-AI version, we return a template.
    
    report = {
        'summary': "This week was productive! You focused on your core tasks.",
        'score': 85,
        'wins': [
            "Consistent login streak",
            "Updated Smart Blocks",
            "Checked News"
        ],
        'improvements': [
            "Try to log 1 more habit per day",
            "Review 'Python' notes"
        ]
    }
    return report

def calculate_progress_score(user_id):
    """Deterministic progress score."""
    # Mock calculation
    return 80
