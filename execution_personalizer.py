"""
Execution Coach - Personalization Engine
Tailors execution plans based on user preferences, work style, and patterns
"""

from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class ExecutionPersonalizer:
    """Personalizes execution plans based on user profile and history"""

    def __init__(self, user_data: Dict):
        """
        Initialize with user profile
        
        user_data should contain:
        - work_time, free_time (schedule)
        - career, main_goal (context)
        - preferred_focus_duration (if set)
        - chronotype (morning_person, night_owl, bimodal)
        - task_style (one_big_task, many_small_tasks, mixed)
        - energy_pattern (rising, steady, declining)
        """
        self.user_data = user_data

    def adjust_plan_for_user(self, base_plan: Dict) -> Dict:
        """
        Adjust a base execution plan to match user's work style
        
        Args:
            base_plan: Standard plan to personalize
            
        Returns:
            Personalized plan adjusted for user preferences
        """
        personalized = base_plan.copy()

        # Adjust focus duration
        personalized['suggested_focus_duration'] = self._personalize_focus_duration()

        # Adjust time blocks for chronotype
        if personalized.get('time_blocks'):
            personalized['time_blocks'] = self._adjust_blocks_for_chronotype(
                personalized['time_blocks']
            )

        # Adjust priorities for task style
        if personalized.get('top_priorities'):
            personalized['top_priorities'] = self._adjust_priorities_for_task_style(
                personalized['top_priorities']
            )

        # Adjust messaging tone
        personalized['coaching_message'] = self._personalize_message(
            personalized.get('coaching_message', ''),
            base_plan
        )

        return personalized

    def _personalize_focus_duration(self) -> int:
        """
        Suggest focus duration based on user preference and capability
        
        Defaults to 25 (Pomodoro), but adjusts to user history
        """
        preferred = self.user_data.get('preferred_focus_duration')
        if preferred and 15 <= preferred <= 60:
            return preferred

        # Default based on work intensity
        if self.user_data.get('career') in ['software_engineer', 'analyst', 'designer']:
            return 45  # Deep work roles benefit from longer focus
        else:
            return 25  # Standard Pomodoro

    def _adjust_blocks_for_chronotype(self, blocks: List[Dict]) -> List[Dict]:
        """
        Reorder blocks to match user's energy patterns
        
        Chronotypes:
        - morning_person: Schedule hard tasks 7am-11am
        - night_owl: Schedule hard tasks 4pm-11pm
        - bimodal: Two peaks (morning + evening)
        """
        chronotype = self.user_data.get('chronotype', 'standard')

        if chronotype == 'morning_person':
            # Ensure hardest tasks in morning
            return self._prioritize_morning_blocks(blocks)
        elif chronotype == 'night_owl':
            # Ensure hard tasks in afternoon/evening
            return self._prioritize_evening_blocks(blocks)
        elif chronotype == 'bimodal':
            # Use morning and evening peaks
            return self._create_bimodal_schedule(blocks)
        else:
            return blocks

    def _adjust_priorities_for_task_style(self, priorities: List[Dict]) -> List[Dict]:
        """
        Reorder priorities based on how user prefers to work
        
        Styles:
        - one_big_task: User prefers 1-2 major tasks per day
        - many_small_tasks: User prefers completing many small items
        - mixed: Balanced approach
        """
        style = self.user_data.get('task_style', 'mixed')

        if style == 'one_big_task':
            # Filter to 1-2 most impactful
            return priorities[:1]
        elif style == 'many_small_tasks':
            # Break down larger tasks, keep list longer
            return priorities  # Could expand further
        else:
            # Mixed: keep as is (2-3 items)
            return priorities[:3]

    def _personalize_message(self, base_message: str, plan: Dict) -> str:
        """
        Adjust coaching message tone to match user preference
        
        Tones:
        - direct: Just the facts, minimal emoji
        - supportive: Encouraging, friendly
        - motivational: Energetic, empowering
        """
        tone = self.user_data.get('preferred_message_tone', 'supportive')

        if tone == 'direct':
            # Remove emoji, make concise
            return base_message.replace('🚀', '').replace('⚡', '').replace('🎯', '')
        elif tone == 'motivational':
            # Add power words
            if '🚀' not in base_message:
                base_message = f"🚀 {base_message}"
            return base_message
        else:
            # supportive (default)
            return base_message

    def _prioritize_morning_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Reorder so hardest work happens in morning"""
        # Typically 7am-11am
        morning_start = 7 * 60
        morning_end = 11 * 60

        morning_blocks = []
        other_blocks = []

        for block in blocks:
            block_time = self._time_to_minutes(block.get('start_time', '09:00'))
            if morning_start <= block_time < morning_end:
                morning_blocks.append(block)
            else:
                other_blocks.append(block)

        # Sort morning blocks to put "focus" type first
        morning_blocks.sort(key=lambda b: (0 if b.get('block_type') == 'focus' else 1))

        return morning_blocks + other_blocks

    def _prioritize_evening_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """Reorder so hard work happens in evening"""
        # Typically 4pm-11pm (1600-2300)
        evening_start = 16 * 60
        evening_end = 23 * 60

        evening_blocks = []
        other_blocks = []

        for block in blocks:
            block_time = self._time_to_minutes(block.get('start_time', '09:00'))
            if evening_start <= block_time < evening_end:
                evening_blocks.append(block)
            else:
                other_blocks.append(block)

        # Put evening blocks first
        evening_blocks.sort(key=lambda b: (0 if b.get('block_type') == 'focus' else 1))

        return other_blocks + evening_blocks

    def _create_bimodal_schedule(self, blocks: List[Dict]) -> List[Dict]:
        """Create schedule with two peaks of energy"""
        # Morning peak: 7am-11am
        # Afternoon dip: 11am-4pm (administrative/easy tasks)
        # Evening peak: 4pm-8pm
        # Night wind-down: 8pm+

        morning_focus = []
        afternoon_easy = []
        evening_focus = []
        wind_down = []

        for block in blocks:
            block_time = self._time_to_minutes(block.get('start_time', '09:00'))

            if block_time < 11 * 60:
                morning_focus.append(block)
            elif block_time < 16 * 60:
                afternoon_easy.append(block)
            elif block_time < 20 * 60:
                evening_focus.append(block)
            else:
                wind_down.append(block)

        # Sort by focus type within each period
        for period in [morning_focus, evening_focus]:
            period.sort(key=lambda b: (0 if b.get('block_type') == 'focus' else 1))

        return morning_focus + afternoon_easy + evening_focus + wind_down

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert time string '09:30' to minutes"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except:
            return 0


class UserPreferences:
    """Manages user execution preferences"""

    def __init__(self, user_id: int, db_connection=None):
        self.user_id = user_id
        self.db = db_connection

    def get_preferences(self) -> Dict:
        """
        Get user's execution preferences
        
        Returns dict with keys:
        - chronotype: morning_person, night_owl, bimodal, standard
        - task_style: one_big_task, many_small_tasks, mixed
        - preferred_focus_duration: minutes (15-60)
        - preferred_message_tone: direct, supportive, motivational
        - break_after_focus: boolean
        - pomodoro_break_minutes: 5-15
        - enable_notifications: boolean
        - focus_start_time: HH:MM
        """
        # TODO: Query from execution_preferences table
        # For now, return defaults
        return {
            'chronotype': 'standard',
            'task_style': 'mixed',
            'preferred_focus_duration': 25,
            'preferred_message_tone': 'supportive',
            'break_after_focus': True,
            'pomodoro_break_minutes': 5,
            'enable_notifications': True,
            'focus_start_time': '09:00'
        }

    def set_preferences(self, preferences: Dict) -> bool:
        """
        Save user preferences
        
        Args:
            preferences: Dict with preference keys
            
        Returns:
            True if saved successfully
        """
        # TODO: Save to execution_preferences table
        logger.info(f"User {self.user_id} preferences updated: {preferences}")
        return True

    def detect_chronotype_from_history(self, completed_tasks_by_hour: Dict[int, int]) -> str:
        """
        Detect user's chronotype from completion history
        
        Args:
            completed_tasks_by_hour: Dict mapping hour of day to completed task count
            
        Returns:
            Detected chronotype: morning_person, night_owl, bimodal, or standard
        """
        if not completed_tasks_by_hour:
            return 'standard'

        # Get peak hours
        peak_hour = max(completed_tasks_by_hour, key=completed_tasks_by_hour.get)
        peak_count = completed_tasks_by_hour[peak_hour]

        # Count tasks in ranges
        morning_count = sum(completed_tasks_by_hour.get(h, 0) for h in range(5, 12))
        afternoon_count = sum(completed_tasks_by_hour.get(h, 0) for h in range(12, 17))
        evening_count = sum(completed_tasks_by_hour.get(h, 0) for h in range(17, 23))

        total = morning_count + afternoon_count + evening_count

        if total == 0:
            return 'standard'

        morning_pct = morning_count / total
        evening_pct = evening_count / total

        # Classify
        if morning_pct > 0.5:
            return 'morning_person'
        elif evening_pct > 0.5:
            return 'night_owl'
        elif morning_pct > 0.25 and evening_pct > 0.25:
            return 'bimodal'
        else:
            return 'standard'

    @staticmethod
    def detect_task_style_from_history(completed_tasks: List[Dict]) -> str:
        """
        Detect preferred task style from history
        
        Args:
            completed_tasks: List of completed tasks with durations
            
        Returns:
            Task style: one_big_task, many_small_tasks, or mixed
        """
        if not completed_tasks or len(completed_tasks) < 3:
            return 'mixed'

        avg_duration = sum(t.get('duration_minutes', 30) for t in completed_tasks) / len(completed_tasks)
        short_task_ratio = sum(1 for t in completed_tasks if t.get('duration_minutes', 30) < 30) / len(completed_tasks)

        if avg_duration > 60 and short_task_ratio < 0.3:
            return 'one_big_task'
        elif short_task_ratio > 0.7:
            return 'many_small_tasks'
        else:
            return 'mixed'
