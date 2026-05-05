"""
Execution Coach - Recovery Mode Engine
Generates lighter rescue plans when user is falling behind
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RecoveryPlan:
    """Lightweight plan to recover and rebuild momentum"""
    
    def __init__(self, user_id: int, plan_date: str):
        self.user_id = user_id
        self.plan_date = plan_date
        self.must_do_task: Optional[Dict] = None           # 1 critical task
        self.easy_win_task: Optional[Dict] = None          # 1 quick victory
        self.streak_protecting_habit: Optional[Dict] = None # 1 habit to keep streak
        self.focus_sprint: Optional[Dict] = None           # 1 short focus block
        self.recovery_message: str = ""
        self.estimated_recovery_time: int = 0  # Total minutes
        self.next_checkpoint: str = ""  # Next milestone

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'plan_date': self.plan_date,
            'must_do_task': self.must_do_task,
            'easy_win_task': self.easy_win_task,
            'streak_protecting_habit': self.streak_protecting_habit,
            'focus_sprint': self.focus_sprint,
            'recovery_message': self.recovery_message,
            'estimated_recovery_time': self.estimated_recovery_time,
            'next_checkpoint': self.next_checkpoint
        }


class ExecutionRecovery:
    """Recovery mode - generates rescue plans for falling-behind users"""

    def __init__(self, user_data: Dict):
        self.user_data = user_data

    def generate_recovery_plan(self, 
                               all_tasks: List[Dict],
                               habits_today: List[Dict],
                               missed_count: int,
                               current_streak: int,
                               momentum_score: float,
                               plan_date: str = None) -> RecoveryPlan:
        """
        Generate a recovery plan with 4 focused items:
        1. Must-do (most critical)
        2. Easy win (quick morale boost)
        3. Streak-protecting habit (maintain continuity)
        4. Short focus sprint (rebuild discipline)
        
        Args:
            all_tasks: List of all tasks (done and not done)
            habits_today: Habits for today
            missed_count: Number of tasks already missed today
            current_streak: Current habit/task streak
            momentum_score: Current momentum 0-100
            plan_date: Date for recovery plan
            
        Returns:
            RecoveryPlan object with 4 focused items
        """
        if plan_date is None:
            plan_date = datetime.now().strftime('%Y-%m-%d')

        plan = RecoveryPlan(self.user_data.get('user_id', 0), plan_date)

        # 1. Select the MUST-DO task (most critical, shortest)
        plan.must_do_task = self._select_must_do_task(all_tasks, missed_count)

        # 2. Select an EASY WIN (quick task, high confidence)
        plan.easy_win_task = self._select_easy_win_task(all_tasks, plan.must_do_task)

        # 3. Select a HABIT to protect streak
        plan.streak_protecting_habit = self._select_streak_protecting_habit(habits_today, current_streak)

        # 4. Suggest a SHORT FOCUS SPRINT
        plan.focus_sprint = self._create_short_focus_sprint(plan.must_do_task)

        # Calculate total time needed
        plan.estimated_recovery_time = self._calculate_recovery_time(plan)

        # Generate recovery message
        plan.recovery_message = self._generate_recovery_message(
            momentum_score, missed_count, current_streak
        )

        # Set next checkpoint
        plan.next_checkpoint = self._get_next_checkpoint(plan.estimated_recovery_time)

        return plan

    def _select_must_do_task(self, all_tasks: List[Dict], missed_count: int) -> Optional[Dict]:
        """
        Select the single most critical task
        
        Criteria:
        - Due today or overdue
        - Required for streak/main goal
        - Shortest duration (maximize completion chance)
        - Not already completed
        """
        if not all_tasks:
            return None

        # Filter: only incomplete, critical tasks
        critical_tasks = [
            task for task in all_tasks
            if task.get('status') != 'completed'
            and (task.get('priority') == 'high' or task.get('due_date') == datetime.now().strftime('%Y-%m-%d'))
        ]

        if not critical_tasks:
            # If no urgent tasks, just pick any incomplete task
            critical_tasks = [task for task in all_tasks if task.get('status') != 'completed']

        if not critical_tasks:
            return None

        # Sort by: priority, then duration (shortest first)
        critical_tasks.sort(key=lambda t: (
            0 if t.get('priority') == 'high' else 1,
            t.get('estimated_duration_minutes', 30)
        ))

        selected = critical_tasks[0]

        # Reduce estimated time for recovery (user will focus hard)
        original_duration = selected.get('estimated_duration_minutes', 30)
        reduced_duration = max(15, int(original_duration * 0.7))  # Optimistic 70% of original

        return {
            'id': selected.get('id', 0),
            'title': selected.get('title', 'Task'),
            'description': selected.get('description', ''),
            'original_duration': original_duration,
            'recovery_duration': reduced_duration,
            'priority': selected.get('priority', 'high'),
            'category': selected.get('category', 'general'),
            'why_critical': self._explain_criticality(selected, missed_count)
        }

    def _select_easy_win_task(self, all_tasks: List[Dict], must_do: Optional[Dict]) -> Optional[Dict]:
        """
        Select a task that user can complete quickly for morale
        
        Criteria:
        - Very short duration (< 20 minutes)
        - High completion confidence (based on history)
        - Not the must-do task
        - Clear/well-defined
        """
        if not all_tasks:
            return None

        # Filter short, incomplete tasks (excluding must-do)
        easy_tasks = [
            task for task in all_tasks
            if task.get('status') != 'completed'
            and task.get('estimated_duration_minutes', 30) <= 20
            and (not must_do or task.get('id') != must_do.get('id'))
        ]

        if not easy_tasks:
            # Fallback: any short task
            easy_tasks = [
                task for task in all_tasks
                if task.get('estimated_duration_minutes', 30) <= 30
            ]

        if not easy_tasks:
            return None

        # Pick shortest one
        selected = min(easy_tasks, key=lambda t: t.get('estimated_duration_minutes', 30))

        return {
            'id': selected.get('id', 0),
            'title': selected.get('title', 'Quick Task'),
            'duration': selected.get('estimated_duration_minutes', 15),
            'priority': selected.get('priority', 'low'),
            'reason': 'Quick win to rebuild confidence'
        }

    def _select_streak_protecting_habit(self, habits_today: List[Dict], current_streak: int) -> Optional[Dict]:
        """
        Select a single habit that protects the streak
        
        Criteria:
        - Shortest habit (easiest to complete)
        - Most important for streak maintenance
        - Doable in remaining time
        """
        if not habits_today or current_streak == 0:
            # If no streak, pick any quick habit
            if habits_today:
                shortest = min(habits_today, key=lambda h: h.get('duration_minutes', 15))
                return {
                    'id': shortest.get('id', 0),
                    'name': shortest.get('name', 'Habit'),
                    'duration': shortest.get('duration_minutes', 15),
                    'scheduled_time': shortest.get('scheduled_time', '21:00'),
                    'reason': f"Building a streak - start with small habits"
                }
            return None

        # If streak exists, prioritize most important habit
        # Usually the first/main habit
        selected = habits_today[0] if habits_today else None

        if not selected:
            return None

        return {
            'id': selected.get('id', 0),
            'name': selected.get('name', 'Habit'),
            'duration': selected.get('duration_minutes', 15),
            'scheduled_time': selected.get('scheduled_time', '21:00'),
            'reason': f"Protect your {current_streak}-day streak - just this one habit keeps it alive"
        }

    def _create_short_focus_sprint(self, must_do_task: Optional[Dict]) -> Optional[Dict]:
        """
        Create a short, intense focus sprint to get started
        
        Recommendation:
        - 15 minute Pomodoro (shorter than normal for quick win)
        - No breaks or distractions
        - For the must-do task
        """
        if not must_do_task:
            return None

        return {
            'duration_minutes': 15,
            'task': must_do_task.get('title', 'Focus Sprint'),
            'task_id': must_do_task.get('id', 0),
            'type': 'pomodoro',
            'intensity': 'high',
            'instruction': f"Just 15 minutes on {must_do_task.get('title')}. Turn off notifications. Go!",
            'auto_start': True
        }

    def _calculate_recovery_time(self, plan: RecoveryPlan) -> int:
        """Calculate total estimated time for recovery"""
        total = 0

        if plan.must_do_task:
            total += plan.must_do_task.get('recovery_duration', 30)

        if plan.easy_win_task:
            total += plan.easy_win_task.get('duration', 15)

        if plan.streak_protecting_habit:
            total += plan.streak_protecting_habit.get('duration', 15)

        if plan.focus_sprint:
            total += plan.focus_sprint.get('duration_minutes', 15)

        return total

    def _generate_recovery_message(self, momentum_score: float, missed_count: int, streak: int) -> str:
        """
        Generate empathetic recovery message
        
        Tone: Compassionate, action-oriented, not judgmental
        """
        # Empathy based on situation
        if momentum_score < 30:
            empathy = "Days like this happen to everyone. No judgment."
        elif momentum_score < 50:
            empathy = "You've hit a bump, but it's recoverable right now."
        else:
            empathy = "You can still turn this day around."

        # Action suggestion
        if missed_count == 1:
            action = f"One task slipped - let's prevent more."
        elif missed_count <= 3:
            action = f"{missed_count} tasks missed. No panic - reset and focus."
        else:
            action = "Many things fell off. Let's simplify and rebuild."

        # Streak motivation
        if streak > 0:
            streak_msg = f"\n\nYour {streak}-day streak is still active. Complete your daily habit tonight to keep it going 🔥"
        else:
            streak_msg = "\n\nStart fresh tomorrow or today - it's not too late."

        return f"{empathy} {action}{streak_msg}"

    def _explain_criticality(self, task: Dict, missed_count: int) -> str:
        """Explain why this task is critical in recovery"""
        if task.get('priority') == 'high':
            return "This is high-priority - completing it matters most."
        elif missed_count > 0:
            return "Already missed other tasks - this one can't slip."
        else:
            return "This task has the most impact on your day."

    def _get_next_checkpoint(self, recovery_time: int) -> str:
        """Get next checkpoint time"""
        # Estimate completion
        hours = recovery_time // 60
        minutes = recovery_time % 60

        if hours == 0:
            return f"Next checkpoint in {minutes} minutes"
        elif hours == 1:
            return f"Next checkpoint in about 1 hour"
        else:
            return f"Next checkpoint in ~{hours} hours {minutes} minutes"


class RecoveryStrategies:
    """Collection of recovery strategies for different situations"""

    @staticmethod
    def get_recovery_tip(momentum_score: float, missed_count: int) -> str:
        """Get contextual recovery tip"""
        
        if momentum_score < 20:
            return "💡 Tip: Close all tabs. Phone away. Just do the one must-do task. Nothing else matters right now."
        elif momentum_score < 40:
            return "💡 Tip: Start with the easiest item - quick win builds momentum."
        elif momentum_score < 60:
            return "💡 Tip: Focus on the high-impact task. Skip the low-value items for today."
        else:
            return "💡 Tip: You're close - push through with one more solid effort."

    @staticmethod
    def estimate_recovery_feasibility(recovery_time: int, remaining_hours: float) -> Tuple[bool, float, str]:
        """
        Estimate if recovery is possible with remaining time
        
        Returns:
            (is_feasible, confidence_percent, message)
        """
        remaining_minutes = remaining_hours * 60

        # Add buffer for transitions, breaks
        required_with_buffer = recovery_time * 1.3

        if required_with_buffer <= remaining_minutes:
            confidence = 100.0
            message = "✅ Full recovery is possible with focus."
        elif recovery_time <= remaining_minutes:
            confidence = 75.0
            message = "⚡ Recovery is tight but doable if you stay focused."
        elif (recovery_time * 0.7) <= remaining_minutes:
            confidence = 50.0
            message = "⚠️ Partial recovery - do the must-do + habit to save the day."
        else:
            confidence = 30.0
            message = "🆘 Time is very limited - just protect your streak with the habit."

        return (confidence >= 50, confidence, message)
