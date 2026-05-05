"""
Widget Renderers
Logic for rendering and managing different widget types
"""
from datetime import datetime
from memory import get_daily_tasks, get_user, get_focus_stats
from habits_db import get_user_habits, get_weekly_stats

class WidgetRenderer:
    """Base widget renderer"""
    
    @staticmethod
    def render_todo_widget(user_id, config=None):
        """Render TODO widget with today's tasks"""
        try:
            tasks = get_daily_tasks(user_id)
            
            if not tasks:
                return {
                    'type': 'todo',
                    'status': 'empty',
                    'message': 'No tasks yet. Add one to get started!',
                    'tasks': [],
                    'count': 0,
                    'completed': 0
                }
            
            completed = sum(1 for t in tasks if t.get('status') == 'completed')
            total = len(tasks)
            completion_pct = int((completed / total * 100)) if total > 0 else 0
            
            # Format tasks for widget
            formatted_tasks = []
            for task in tasks:
                formatted_tasks.append({
                    'id': task.get('id'),
                    'task': task.get('task', ''),
                    'status': task.get('status', 'pending'),
                    'completed': task.get('status') == 'completed'
                })
            
            return {
                'type': 'todo',
                'status': 'loaded',
                'tasks': formatted_tasks,
                'count': total,
                'completed': completed,
                'completion_pct': completion_pct,
                'emoji': '🎉' if completion_pct == 100 else ('✓' if completed > 0 else '📋')
            }
        except Exception as e:
            return {
                'type': 'todo',
                'status': 'error',
                'error': str(e),
                'tasks': []
            }
    
    @staticmethod
    def render_habit_widget(user_id, config=None):
        """Render HABIT widget with today's habits and streak"""
        try:
            habits = get_user_habits(user_id)
            stats = get_weekly_stats(user_id)
            
            if not habits:
                return {
                    'type': 'habit',
                    'status': 'empty',
                    'message': 'No habits yet. Create one to build momentum!',
                    'habits': [],
                    'count': 0,
                    'completed': 0,
                    'completion_rate': 0
                }
            
            completed = sum(1 for h in habits if h.get('completed_today'))
            total = len(habits)
            
            # Format habits for widget
            formatted_habits = []
            for habit in habits:
                formatted_habits.append({
                    'id': habit.get('id'),
                    'title': habit.get('title', ''),
                    'icon': habit.get('icon', ''),
                    'completed': habit.get('completed_today', False),
                    'streak': habit.get('streak', 0),
                    'time_of_day': habit.get('time_of_day', 'Anytime')
                })
            
            # Determine emoji based on completion
            if completed == total and total > 0:
                emoji = '🔥'
            elif completed > 0:
                emoji = '✓'
            else:
                emoji = '🌱'
            
            return {
                'type': 'habit',
                'status': 'loaded',
                'habits': formatted_habits,
                'count': total,
                'completed': completed,
                'completion_rate': stats.get('today_rate', 0),
                'weekly_rate': stats.get('completion_rate', 0),
                'emoji': emoji,
                'chart_data': stats.get('chart_data', [])
            }
        except Exception as e:
            return {
                'type': 'habit',
                'status': 'error',
                'error': str(e),
                'habits': []
            }
    
    @staticmethod
    def render_focus_widget(user_id, config=None):
        """Render FOCUS widget with pomodoro timer and session history"""
        try:
            focus_stats = get_focus_stats(user_id)
            
            # Get today's focus sessions
            today_sessions = 0
            total_minutes = 0
            
            if focus_stats:
                today_sessions = focus_stats.get('today_sessions', 0)
                total_minutes = focus_stats.get('today_minutes', 0)
            
            # Get default focus duration preference (default 25 min for Pomodoro)
            user = get_user(user_id)
            focus_duration = 25  # Default Pomodoro duration
            
            # Determine emoji based on sessions
            if today_sessions >= 4:
                emoji = '🔥'
            elif today_sessions >= 2:
                emoji = '⚡'
            elif today_sessions >= 1:
                emoji = '✓'
            else:
                emoji = '⏱️'
            
            return {
                'type': 'focus',
                'status': 'loaded',
                'today_sessions': today_sessions,
                'total_minutes': total_minutes,
                'default_duration': focus_duration,
                'emoji': emoji,
                'message': f"You've completed {today_sessions} focus sessions today" if today_sessions > 0 else "Start a focus session to build momentum",
                'stats': focus_stats or {}
            }
        except Exception as e:
            return {
                'type': 'focus',
                'status': 'error',
                'error': str(e),
                'today_sessions': 0,
                'total_minutes': 0
            }
    
    @staticmethod
    def render_widget(widget_id, widget_type, user_id, config=None):
        """Render any widget based on type"""
        if widget_type == 'todo':
            return WidgetRenderer.render_todo_widget(user_id, config)
        elif widget_type == 'habit':
            return WidgetRenderer.render_habit_widget(user_id, config)
        elif widget_type == 'focus':
            return WidgetRenderer.render_focus_widget(user_id, config)
        else:
            return {
                'type': widget_type,
                'status': 'unknown',
                'error': f'Unknown widget type: {widget_type}'
            }
