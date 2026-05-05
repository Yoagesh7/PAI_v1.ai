"""
Execution Coach - Metrics and Status Tracking
Computes momentum score and determines user status (On Track / At Risk / Recovery Mode)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class MomentumStatus:
    """User's momentum status for the day"""
    
    # Status categories
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    RECOVERY_MODE = "recovery_mode"
    
    def __init__(self, status: str, momentum_score: float, summary: str, 
                 completed_tasks: int, missed_tasks: int, streak_status: str):
        self.status = status
        self.momentum_score = momentum_score  # 0-100
        self.summary = summary
        self.completed_tasks = completed_tasks
        self.missed_tasks = missed_tasks
        self.streak_status = streak_status
        self.needs_recovery = status == self.RECOVERY_MODE
        self.progress_bar = self._calculate_progress_bar(momentum_score)

    def _calculate_progress_bar(self, score: float) -> str:
        """Generate visual progress bar"""
        filled = int(score / 10)
        empty = 10 - filled
        return '█' * filled + '░' * empty

    def to_dict(self) -> Dict:
        return {
            'status': self.status,
            'momentum_score': self.momentum_score,
            'summary': self.summary,
            'completed_tasks': self.completed_tasks,
            'missed_tasks': self.missed_tasks,
            'streak_status': self.streak_status,
            'needs_recovery': self.needs_recovery,
            'progress_bar': self.progress_bar,
            'status_emoji': self._get_status_emoji()
        }

    def _get_status_emoji(self) -> str:
        """Get emoji for status"""
        if self.status == self.ON_TRACK:
            return "✅"
        elif self.status == self.AT_RISK:
            return "⚠️"
        else:
            return "🆘"


class ExecutionMetrics:
    """Calculates momentum and execution status"""

    def __init__(self, user_data: Dict):
        self.user_data = user_data

    def compute_momentum_status(self, 
                               completed_today: List[Dict],
                               missed_today: List[Dict],
                               completed_habits_today: List[Dict],
                               focus_sessions_today: List[Dict],
                               streak_data: Dict,
                               planned_tasks: int) -> MomentumStatus:
        """
        Compute user's momentum status for today
        
        Args:
            completed_today: List of completed tasks
            missed_today: List of missed/overdue tasks
            completed_habits_today: List of completed habits
            focus_sessions_today: List of focus sessions completed
            streak_data: Current streaks and statistics
            planned_tasks: Number of tasks planned for today
            
        Returns:
            MomentumStatus object
        """
        
        # Calculate component scores
        task_completion_score = self._calculate_task_completion_score(
            completed_today, missed_today, planned_tasks
        )
        
        habit_completion_score = self._calculate_habit_completion_score(
            completed_habits_today
        )
        
        focus_score = self._calculate_focus_score(focus_sessions_today)
        
        streak_score = self._calculate_streak_score(streak_data)
        
        # Weighted overall momentum score
        momentum_score = (
            (task_completion_score * 0.40) +
            (habit_completion_score * 0.20) +
            (focus_score * 0.20) +
            (streak_score * 0.20)
        )

        # Determine status category
        status, summary = self._determine_status(
            momentum_score,
            len(completed_today),
            len(missed_today),
            streak_data.get('current_streak', 0),
            streak_data.get('streak_at_risk', False)
        )

        streak_status = self._get_streak_status(streak_data)

        return MomentumStatus(
            status=status,
            momentum_score=momentum_score,
            summary=summary,
            completed_tasks=len(completed_today),
            missed_tasks=len(missed_today),
            streak_status=streak_status
        )

    def _calculate_task_completion_score(self, 
                                        completed: List[Dict],
                                        missed: List[Dict],
                                        planned: int) -> float:
        """
        Calculate task completion score (0-100)
        
        Factors:
        - Ratio of completed to planned
        - Penalties for missed tasks
        - Priority weighting (high-priority tasks worth more)
        """
        if planned == 0:
            return 50.0  # Neutral if no tasks planned

        completed_count = len(completed)
        missed_count = len(missed)

        # Base score: completion ratio
        completion_ratio = completed_count / planned
        base_score = completion_ratio * 100

        # Penalty for missed high-priority tasks
        missed_high_priority = sum(1 for task in missed if task.get('priority') == 'high')
        penalty = missed_high_priority * 10

        final_score = max(base_score - penalty, 0)
        return min(final_score, 100)

    def _calculate_habit_completion_score(self, completed_habits: List[Dict]) -> float:
        """
        Calculate habit completion score (0-100)
        
        A few completed habits = good momentum
        If most habits are done = excellent momentum
        """
        if completed_habits is None or len(completed_habits) == 0:
            return 40.0  # Low if no habits completed

        # 1-2 habits = 60, 3+ = 100
        if len(completed_habits) >= 3:
            return 100.0
        elif len(completed_habits) == 2:
            return 80.0
        else:
            return 60.0

    def _calculate_focus_score(self, focus_sessions: List[Dict]) -> float:
        """
        Calculate focus score based on focus sessions completed
        
        Factors:
        - Number of sessions
        - Total duration
        - Quality/completion of focused work
        """
        if not focus_sessions or len(focus_sessions) == 0:
            return 30.0

        num_sessions = len(focus_sessions)
        total_duration = sum(session.get('duration_minutes', 0) for session in focus_sessions)
        
        # 1 session = 50, 2+ = 80, 3+ = 100
        if num_sessions >= 3:
            score = 100.0
        elif num_sessions >= 2:
            score = 80.0
        else:
            score = 50.0

        # Bonus for total duration > 90 minutes
        if total_duration > 90:
            score = min(score + 10, 100.0)

        return score

    def _calculate_streak_score(self, streak_data: Dict) -> float:
        """
        Calculate streak momentum bonus/penalty
        
        - Active streak: +10 bonus to overall momentum
        - At-risk streak: -15 penalty
        - Broken streak: -10 penalty
        """
        current_streak = streak_data.get('current_streak', 0)
        streak_at_risk = streak_data.get('streak_at_risk', False)
        streak_just_broken = streak_data.get('streak_just_broken', False)

        if streak_just_broken:
            return 40.0  # Low momentum after break
        elif streak_at_risk:
            return 50.0  # Caution zone
        elif current_streak > 0:
            # Active streak boosts momentum
            if current_streak >= 30:
                return 100.0  # Excellent momentum
            elif current_streak >= 7:
                return 85.0
            else:
                return 70.0
        else:
            return 60.0  # No streak but not penalized yet

    def _determine_status(self, 
                         momentum_score: float,
                         completed: int,
                         missed: int,
                         current_streak: int,
                         streak_at_risk: bool) -> Tuple[str, str]:
        """
        Determine status category and message
        
        ON_TRACK: momentum > 70, no missed high-priority tasks
        AT_RISK: momentum 40-70 or streak at risk
        RECOVERY_MODE: momentum < 40 or 2+ missed important tasks
        """
        
        # Recovery Mode conditions
        if momentum_score < 40 or (missed >= 2 and streak_at_risk):
            return MomentumStatus.RECOVERY_MODE, self._recovery_message(completed, missed, momentum_score)

        # At Risk conditions
        if momentum_score < 70 or streak_at_risk or missed > 0:
            return MomentumStatus.AT_RISK, self._at_risk_message(momentum_score, completed, missed)

        # On Track
        return MomentumStatus.ON_TRACK, self._on_track_message(current_streak, completed)

    def _get_streak_status(self, streak_data: Dict) -> str:
        """Get human-readable streak status"""
        current_streak = streak_data.get('current_streak', 0)
        streak_at_risk = streak_data.get('streak_at_risk', False)
        
        if streak_at_risk:
            return f"🔥 {current_streak} day streak at risk - complete today to save it!"
        elif current_streak > 0:
            return f"🔥 {current_streak}-day streak going strong!"
        else:
            return "Start a new streak today!"

    def _on_track_message(self, streak: int, completed: int) -> str:
        """Generate on-track status message"""
        messages = [
            f"🎯 On track! You've completed {completed} tasks and kept momentum.",
            f"✅ Great pace today! You're crushing it.",
            f"💪 Excellent execution! Stay focused and finish strong.",
            f"🚀 Perfect rhythm! You're in the zone.",
        ]
        return messages[min(completed, len(messages) - 1)]

    def _at_risk_message(self, score: float, completed: int, missed: int) -> str:
        """Generate at-risk status message"""
        if score > 60:
            return f"⚠️ Slowing down - you've completed {completed} but {missed} tasks are at risk. Refocus to catch up."
        else:
            return f"⚠️ You're falling behind - {missed} missed tasks. Time to rebuild momentum with smaller wins."

    def _recovery_message(self, completed: int, missed: int, score: float) -> str:
        """Generate recovery mode status message"""
        return f"🆘 Recovery mode activated - you've missed {missed} tasks. Let's rebuild with a lighter plan and get back on track."


class ExecutionInsights:
    """Generate actionable insights from execution data"""

    @staticmethod
    def identify_blockers(missed_tasks: List[Dict]) -> List[str]:
        """
        Identify patterns in missed tasks
        
        Returns list of potential blockers:
        - Unclear priorities
        - Underestimated time
        - Too many simultaneous tasks
        - Low energy/motivation patterns
        """
        blockers = []
        
        if not missed_tasks:
            return blockers

        # Check for pattern: tasks with short duration missed
        short_tasks = [t for t in missed_tasks if t.get('estimated_duration_minutes', 30) < 30]
        if len(short_tasks) > len(missed_tasks) * 0.5:
            blockers.append("Unclear priorities - consider breaking down tasks better")

        # Check for pattern: similar category repeatedly missed
        categories = [t.get('category') for t in missed_tasks]
        if categories and len(set(categories)) == 1:
            blockers.append(f"Recurring struggle in {categories[0]} tasks - might need help or breaking down")

        # Check for time underestimation
        avg_planned = sum(t.get('estimated_duration_minutes', 30) for t in missed_tasks) / len(missed_tasks)
        if avg_planned < 30:
            blockers.append("Tasks might be underestimated - add buffer time to estimates")

        return blockers

    @staticmethod
    def identify_strengths(completed_tasks: List[Dict]) -> List[str]:
        """
        Identify execution strengths
        
        Returns:
        - Categories user excels at
        - Time-of-day patterns
        - Task types completed successfully
        """
        strengths = []
        
        if not completed_tasks or len(completed_tasks) < 3:
            return strengths

        # Check for strong categories
        categories = [t.get('category') for t in completed_tasks if t.get('category')]
        if categories:
            category_counts = {}
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            top_category = max(category_counts, key=category_counts.get)
            if category_counts[top_category] >= 2:
                strengths.append(f"Strong execution in {top_category} tasks")

        # Check for high-priority completion
        high_priority_count = len([t for t in completed_tasks if t.get('priority') == 'high'])
        if high_priority_count >= 2:
            strengths.append("Excellent at prioritizing important work")

        return strengths
