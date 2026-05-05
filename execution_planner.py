"""
Execution Coach - Daily Planning Engine
Generates intelligent daily plans based on user profile, tasks, habits, and focus patterns
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TimeBlock:
    """Represents a scheduled time block for the user"""
    def __init__(self, start_time: str, end_time: str, task_id: int, task_title: str, 
                 priority: str, duration_minutes: int, block_type: str = "work"):
        self.start_time = start_time      # "09:00"
        self.end_time = end_time          # "10:30"
        self.task_id = task_id
        self.task_title = task_title
        self.priority = priority          # "high", "medium", "low"
        self.duration_minutes = duration_minutes
        self.block_type = block_type      # "work", "focus", "habit", "break", "review"

    def to_dict(self) -> Dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'task_id': self.task_id,
            'task_title': self.task_title,
            'priority': self.priority,
            'duration_minutes': self.duration_minutes,
            'block_type': self.block_type
        }


class DailyExecutionPlan:
    """Complete daily execution plan for a user"""
    def __init__(self, user_id: int, plan_date: str):
        self.user_id = user_id
        self.plan_date = plan_date
        self.top_priorities: List[Dict] = []  # Top 3 tasks
        self.time_blocks: List[TimeBlock] = []
        self.current_block: Optional[TimeBlock] = None
        self.suggested_focus_duration: int = 25  # Default Pomodoro
        self.coaching_message: str = ""
        self.do_now_task: Optional[Dict] = None
        self.total_planned_minutes: int = 0
        self.estimated_completion_rate: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'plan_date': self.plan_date,
            'top_priorities': self.top_priorities,
            'time_blocks': [block.to_dict() for block in self.time_blocks],
            'current_block': self.current_block.to_dict() if self.current_block else None,
            'do_now_task': self.do_now_task,
            'suggested_focus_duration': self.suggested_focus_duration,
            'coaching_message': self.coaching_message,
            'total_planned_minutes': self.total_planned_minutes,
            'estimated_completion_rate': self.estimated_completion_rate
        }


class ExecutionPlanner:
    """Daily planning engine - generates realistic execution plans"""

    def __init__(self, user_data: Dict, all_tasks: List[Dict], habits_today: List[Dict],
                 focus_history: Dict, streak_data: Dict):
        """
        Initialize planner with user context
        
        Args:
            user_data: User profile (work_time, free_time, career, main_goal, etc.)
            all_tasks: All pending/upcoming tasks
            habits_today: Habits scheduled for today
            focus_history: User's focus session patterns
            streak_data: Current streaks and completion patterns
        """
        self.user_data = user_data
        self.all_tasks = all_tasks
        self.habits_today = habits_today
        self.focus_history = focus_history
        self.streak_data = streak_data

    def generate_plan(self, plan_date: str = None) -> DailyExecutionPlan:
        """
        Generate a complete daily execution plan
        
        Returns:
            DailyExecutionPlan object with priorities, time blocks, coaching message
        """
        if plan_date is None:
            plan_date = datetime.now().strftime('%Y-%m-%d')

        plan = DailyExecutionPlan(self.user_data.get('user_id', 0), plan_date)

        # Step 1: Prioritize tasks
        plan.top_priorities = self._select_top_priorities()

        # Step 2: Build time blocks
        plan.time_blocks = self._build_time_blocks(plan.top_priorities)

        # Step 3: Set current block
        plan.current_block = self._get_current_block(plan.time_blocks)

        # Step 4: Set do-now task
        plan.do_now_task = self._get_do_now_task(plan.top_priorities, plan.current_block)

        # Step 5: Suggest focus duration
        plan.suggested_focus_duration = self._suggest_focus_duration()

        # Step 6: Calculate total planned time
        plan.total_planned_minutes = sum(block.duration_minutes for block in plan.time_blocks)

        # Step 7: Estimate completion rate
        plan.estimated_completion_rate = self._estimate_completion_rate(plan.top_priorities)

        # Step 8: Generate coaching message
        plan.coaching_message = self._generate_coaching_message(plan)

        return plan

    def _select_top_priorities(self) -> List[Dict]:
        """
        Select top 3 priority tasks using multi-factor scoring
        
        Factors:
        - Due date (urgent tasks first)
        - Dependency on other tasks
        - Impact on main goal
        - Completable in available time
        - User completion history with similar tasks
        """
        now = datetime.now()
        scored_tasks = []

        for task in self.all_tasks:
            score = self._score_task_priority(task, now)
            if score > 0:
                scored_tasks.append({
                    'task': task,
                    'score': score
                })

        # Sort by score descending and take top 3
        scored_tasks.sort(key=lambda x: x['score'], reverse=True)
        top_3 = [item['task'] for item in scored_tasks[:3]]

        return top_3

    def _score_task_priority(self, task: Dict, now: datetime) -> float:
        """
        Calculate priority score for a single task (0-100)
        
        Scoring factors:
        - Due date urgency (40 points)
        - Estimated duration fit (30 points)
        - Task importance/type (20 points)
        - User completion history (10 points)
        """
        score = 0.0

        # Factor 1: Due date urgency (40 points max)
        due_date_str = task.get('due_date')
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                days_until = (due_date - now).days
                
                if days_until < 0:
                    score += 40  # Overdue
                elif days_until == 0:
                    score += 35  # Due today
                elif days_until == 1:
                    score += 30  # Due tomorrow
                elif days_until <= 3:
                    score += 20
                elif days_until <= 7:
                    score += 10
                else:
                    score += 2
            except:
                score += 5

        # Factor 2: Duration fit (30 points max)
        duration = task.get('estimated_duration_minutes', 30)
        available_time = self._get_available_time_today()
        if duration <= available_time:
            score += 30
        elif duration <= available_time + 30:
            score += 15
        # else: 0 additional points for tasks that don't fit

        # Factor 3: Task importance (20 points max)
        task_type = task.get('type', 'regular')
        priority = task.get('priority', 'medium')
        
        if task_type == 'goal-related':
            score += 15
        elif task_type == 'project':
            score += 12
        elif task_type == 'learning':
            score += 8
        
        if priority == 'high':
            score += 5
        elif priority == 'medium':
            score += 2

        # Factor 4: Completion history (10 points max)
        category = task.get('category', 'general')
        completion_rate = self.streak_data.get(f'{category}_completion_rate', 0.5)
        score += completion_rate * 10

        return min(score, 100)

    def _build_time_blocks(self, top_priorities: List[Dict]) -> List[TimeBlock]:
        """
        Create intelligent time blocks based on:
        - Work hours and free time preferences
        - Task durations and dependencies
        - Natural energy patterns
        - Break/recovery time
        - Habit scheduled times
        """
        blocks = []
        
        # Parse work and free time
        work_time = self.user_data.get('work_time', '09:00-17:00')
        free_time = self.user_data.get('free_time', '18:00-22:00')
        
        work_start, work_end = self._parse_time_range(work_time)
        free_start, free_end = self._parse_time_range(free_time)

        # Get current time
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        # Build morning blocks (highest energy)
        morning_start = self._time_to_minutes(work_start)
        morning_end = morning_start + 180  # 3 hours for peak focus

        # Allocate top priority tasks to morning
        time_cursor = morning_start
        for i, task in enumerate(top_priorities[:2]):
            duration = min(
                task.get('estimated_duration_minutes', 30),
                morning_end - time_cursor
            )
            
            if duration > 0:
                block_start = self._minutes_to_time(time_cursor)
                block_end = self._minutes_to_time(time_cursor + duration)
                
                blocks.append(TimeBlock(
                    start_time=block_start,
                    end_time=block_end,
                    task_id=task.get('id', 0),
                    task_title=task.get('title', 'Task'),
                    priority=task.get('priority', 'medium'),
                    duration_minutes=duration,
                    block_type='focus'
                ))
                
                time_cursor += duration + 15  # 15 min buffer

        # Add lunch break if in work hours
        if morning_end < self._time_to_minutes(work_end):
            blocks.append(TimeBlock(
                start_time=self._minutes_to_time(morning_end),
                end_time=self._minutes_to_time(morning_end + 60),
                task_id=0,
                task_title='Lunch Break',
                priority='medium',
                duration_minutes=60,
                block_type='break'
            ))

        # Afternoon blocks (medium energy)
        afternoon_start = morning_end + 75  # After lunch
        afternoon_end = self._time_to_minutes(work_end)
        
        if len(top_priorities) > 2:
            for task in top_priorities[2:]:
                duration = min(
                    task.get('estimated_duration_minutes', 30),
                    afternoon_end - afternoon_start
                )
                
                if duration > 0:
                    block_start = self._minutes_to_time(afternoon_start)
                    block_end = self._minutes_to_time(afternoon_start + duration)
                    
                    blocks.append(TimeBlock(
                        start_time=block_start,
                        end_time=block_end,
                        task_id=task.get('id', 0),
                        task_title=task.get('title', 'Task'),
                        priority=task.get('priority', 'medium'),
                        duration_minutes=duration,
                        block_type='work'
                    ))
                    
                    afternoon_start += duration + 10

        # Add habits if scheduled
        for habit in self.habits_today:
            habit_time = habit.get('scheduled_time', '20:00')
            habit_duration = habit.get('duration_minutes', 15)
            
            try:
                habit_hour, habit_minute = map(int, habit_time.split(':'))
                habit_minutes = habit_hour * 60 + habit_minute
                
                blocks.append(TimeBlock(
                    start_time=habit_time,
                    end_time=self._minutes_to_time(habit_minutes + habit_duration),
                    task_id=habit.get('id', 0),
                    task_title=habit.get('name', 'Habit'),
                    priority='medium',
                    duration_minutes=habit_duration,
                    block_type='habit'
                ))
            except:
                continue

        # Add evening review block
        review_start = self._time_to_minutes(free_end) - 30
        blocks.append(TimeBlock(
            start_time=self._minutes_to_time(review_start),
            end_time=self._minutes_to_time(review_start + 30),
            task_id=0,
            task_title='Daily Review & Reflection',
            priority='medium',
            duration_minutes=30,
            block_type='review'
        ))

        return sorted(blocks, key=lambda b: self._time_to_minutes(b.start_time))

    def _get_current_block(self, time_blocks: List[TimeBlock]) -> Optional[TimeBlock]:
        """
        Determine which time block the user is currently in
        (or should be in if in between blocks)
        """
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute

        for block in time_blocks:
            block_start = self._time_to_minutes(block.start_time)
            block_end = self._time_to_minutes(block.end_time)
            
            if block_start <= current_minutes < block_end:
                return block

        # If not in any block, return the next upcoming block
        for block in time_blocks:
            block_start = self._time_to_minutes(block.start_time)
            if block_start > current_minutes:
                return block

        # If no upcoming block today, return the first block tomorrow
        return time_blocks[0] if time_blocks else None

    def _get_do_now_task(self, top_priorities: List[Dict], current_block: Optional[TimeBlock]) -> Optional[Dict]:
        """
        Determine the single most important task to do RIGHT NOW
        """
        if not current_block or current_block.task_id == 0:
            # No active task block, recommend first priority
            return top_priorities[0] if top_priorities else None

        # Match current block to task
        for task in top_priorities:
            if task.get('id') == current_block.task_id:
                return {
                    'id': task['id'],
                    'title': task['title'],
                    'description': task.get('description', ''),
                    'block_duration': current_block.duration_minutes,
                    'priority': current_block.priority,
                    'action': 'start_focus'
                }

        return None

    def _suggest_focus_duration(self) -> int:
        """
        Suggest optimal Pomodoro/focus duration based on:
        - User's historical focus patterns
        - Task complexity
        - Available uninterrupted time
        """
        # Check user's average focus session duration
        avg_focus = self.focus_history.get('average_duration_minutes', 25)
        
        # User tends toward longer or shorter sessions?
        max_focus = self.focus_history.get('max_duration_minutes', 50)
        
        # Balance between their capability and optimal range
        if avg_focus < 20:
            suggested = 20  # Too short, suggest 20
        elif avg_focus > 45:
            suggested = min(avg_focus, 50)  # Cap at 50 for sustainability
        else:
            suggested = int(avg_focus)

        return suggested

    def _estimate_completion_rate(self, top_priorities: List[Dict]) -> float:
        """
        Estimate realistic completion rate based on:
        - Number of tasks vs available time
        - User's historical completion rate
        - Task difficulty and user proficiency
        """
        if not top_priorities:
            return 0.0

        available_time = self._get_available_time_today()
        required_time = sum(t.get('estimated_duration_minutes', 30) for t in top_priorities)

        # Time-based estimation
        if required_time == 0:
            time_feasibility = 1.0
        else:
            time_feasibility = min(available_time / required_time, 1.0)

        # User history based estimation
        user_completion_rate = self.streak_data.get('daily_completion_rate', 0.6)

        # Combine factors
        estimated_rate = (time_feasibility * 0.6) + (user_completion_rate * 0.4)

        return min(estimated_rate, 1.0)

    def _generate_coaching_message(self, plan: DailyExecutionPlan) -> str:
        """
        Generate a personalized coaching message for the user
        """
        if not plan.top_priorities:
            return "📋 Today looks light! You might have breathing room. Use this to review goals or get ahead on important projects."

        first_task = plan.top_priorities[0]
        task_title = first_task.get('title', 'your first task')
        
        # Personalize based on context
        if plan.estimated_completion_rate > 0.8:
            message = f"🚀 You've got this! {task_title} is your #1 priority. Tackle it fresh, while your energy is high."
        elif plan.estimated_completion_rate > 0.5:
            message = f"⚡ Solid day ahead! Focus on {task_title} first. You've got enough time if you stay focused."
        else:
            message = f"🎯 It's a busy day. Prioritize {task_title}, then adapt as you go. Quality over quantity."

        # Add streak motivation
        current_streak = self.streak_data.get('current_streak', 0)
        if current_streak > 0 and current_streak % 7 == 0:
            message += f"\n\n🔥 You're on a {current_streak}-day streak! Today keeps it alive."

        return message

    def _get_available_time_today(self) -> int:
        """Calculate available work minutes remaining today"""
        work_time = self.user_data.get('work_time', '09:00-17:00')
        start, end = self._parse_time_range(work_time)
        
        total_minutes = self._time_to_minutes(end) - self._time_to_minutes(start)
        # Subtract 60 min for lunch, 30 min for breaks
        return total_minutes - 90

    @staticmethod
    def _parse_time_range(time_range: str) -> Tuple[str, str]:
        """Parse time range string like '09:00-17:00' to ('09:00', '17:00')"""
        parts = time_range.split('-')
        if len(parts) == 2:
            return (parts[0].strip(), parts[1].strip())
        return ('09:00', '17:00')

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert time string '09:30' to minutes (570)"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except:
            return 0

    @staticmethod
    def _minutes_to_time(minutes: int) -> str:
        """Convert minutes (570) to time string '09:30'"""
        hour = minutes // 60
        minute = minutes % 60
        return f"{hour:02d}:{minute:02d}"
