"""
Execution Coach - Flask API Routes
Add these routes to your web/app.py file
"""

# ============================================================================
# ADD THESE IMPORTS TO TOP OF web/app.py:
# ============================================================================
"""
from execution_planner import ExecutionPlanner, DailyExecutionPlan
from execution_metrics import ExecutionMetrics, MomentumStatus
from execution_recovery import ExecutionRecovery
from execution_personalizer import ExecutionPersonalizer, UserPreferences
"""

# ============================================================================
# ADD THESE ROUTES TO web/app.py (around line 2500+)
# ============================================================================

"""
# EXECUTION COACH ROUTES
# ====================

@app.route('/api/execution/today', methods=['GET'])
def get_execution_plan_today():
    '''Get today's execution plan'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = user['user_id']
        today = datetime.now().strftime('%Y-%m-%d')

        # Get user's task and habit data
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all tasks
            cursor.execute(
                "SELECT id, title, description, priority, type, category, "
                "estimated_duration_minutes, due_date, status FROM ai_daily_tasks WHERE user_id = ? ORDER BY due_date",
                (user_id,)
            )
            all_tasks = [dict(zip(['id', 'title', 'description', 'priority', 'type', 'category', 
                                   'estimated_duration_minutes', 'due_date', 'status'], row)) 
                        for row in cursor.fetchall()]
            
            # Get habits for today
            cursor.execute(
                "SELECT id, name, duration_minutes, scheduled_time FROM habits WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            habits_today = [dict(zip(['id', 'name', 'duration_minutes', 'scheduled_time'], row))
                           for row in cursor.fetchall()]
            
            # Get focus history
            cursor.execute(
                "SELECT AVG(duration_minutes) as avg_duration, MAX(duration_minutes) as max_duration "
                "FROM focus_sessions WHERE user_id = ? LIMIT 20",
                (user_id,)
            )
            focus_row = cursor.fetchone()
            focus_history = {
                'average_duration_minutes': focus_row[0] or 25,
                'max_duration_minutes': focus_row[1] or 50
            }
            
            # Get streak data
            cursor.execute(
                "SELECT streak, last_active_date FROM users WHERE user_id = ?",
                (user_id,)
            )
            user_row = cursor.fetchone()
            current_streak = user_row[0] if user_row else 0
            
            streak_data = {
                'current_streak': current_streak,
                'streak_at_risk': False,  # TODO: Calculate based on last_active_date
                'daily_completion_rate': 0.6  # TODO: Calculate from history
            }

        # Generate plan
        user_profile = {
            'user_id': user_id,
            'work_time': user.get('work_time', '09:00-17:00'),
            'free_time': user.get('free_time', '18:00-22:00'),
            'career': user.get('career', ''),
        }

        planner = ExecutionPlanner(user_profile, all_tasks, habits_today, focus_history, streak_data)
        plan = planner.generate_plan(today)

        # Personalize plan
        personalizer = ExecutionPersonalizer(user_profile)
        personalized_plan = personalizer.adjust_plan_for_user(plan.to_dict())

        return jsonify(personalized_plan), 200

    except Exception as e:
        logging.error(f"Error getting execution plan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/rebuild-day', methods=['POST'])
def rebuild_execution_day():
    '''Activate recovery mode and rebuild day'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = user['user_id']
        today = datetime.now().strftime('%Y-%m-%d')

        # Get current execution state
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all incomplete tasks
            cursor.execute(
                "SELECT id, title, description, priority, type, category, "
                "estimated_duration_minutes, due_date, status FROM ai_daily_tasks "
                "WHERE user_id = ? AND status != 'completed' ORDER BY due_date",
                (user_id,)
            )
            all_tasks = [dict(zip(['id', 'title', 'description', 'priority', 'type', 'category',
                                   'estimated_duration_minutes', 'due_date', 'status'], row))
                        for row in cursor.fetchall()]
            
            # Get habits
            cursor.execute(
                "SELECT id, name, duration_minutes, scheduled_time FROM habits "
                "WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            habits_today = [dict(zip(['id', 'name', 'duration_minutes', 'scheduled_time'], row))
                           for row in cursor.fetchall()]
            
            # Get metrics
            cursor.execute(
                "SELECT streak FROM users WHERE user_id = ?",
                (user_id,)
            )
            user_row = cursor.fetchone()
            current_streak = user_row[0] if user_row else 0
            
            streak_data = {
                'current_streak': current_streak,
                'streak_at_risk': True,  # We're in recovery, so assume at risk
                'daily_completion_rate': 0.5
            }

        # Generate recovery plan
        user_profile = {
            'user_id': user_id,
            'work_time': user.get('work_time', '09:00-17:00'),
            'free_time': user.get('free_time', '18:00-22:00'),
        }

        recovery_engine = ExecutionRecovery(user_profile)
        recovery_plan = recovery_engine.generate_recovery_plan(
            all_tasks=all_tasks,
            habits_today=habits_today,
            missed_count=len([t for t in all_tasks if t.get('status') == 'missed']),
            current_streak=current_streak,
            momentum_score=40,  # Assumed low for recovery mode
            plan_date=today
        )

        # Save recovery plan
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO execution_recovery_plans "
                "(user_id, plan_date, must_do_task, easy_win_task, streak_protecting_habit, "
                "focus_sprint, recovery_message, estimated_recovery_time, created_at, activated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, today, json.dumps(recovery_plan.must_do_task),
                 json.dumps(recovery_plan.easy_win_task),
                 json.dumps(recovery_plan.streak_protecting_habit),
                 json.dumps(recovery_plan.focus_sprint),
                 recovery_plan.recovery_message,
                 recovery_plan.estimated_recovery_time,
                 datetime.now().isoformat(),
                 datetime.now().isoformat())
            )
            conn.commit()

        return jsonify(recovery_plan.to_dict()), 200

    except Exception as e:
        logging.error(f"Error rebuilding day: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/momentum', methods=['GET'])
def get_execution_momentum():
    '''Get today's momentum status'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = user['user_id']
        today = datetime.now().strftime('%Y-%m-%d')

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get completed tasks today
            cursor.execute(
                "SELECT id, title, priority, category FROM ai_daily_tasks "
                "WHERE user_id = ? AND status = 'completed' AND DATE(completed_at) = ?",
                (user_id, today)
            )
            completed_today = [dict(zip(['id', 'title', 'priority', 'category'], row))
                              for row in cursor.fetchall()]
            
            # Get missed tasks today
            cursor.execute(
                "SELECT id, title, priority, category FROM ai_daily_tasks "
                "WHERE user_id = ? AND status = 'missed' AND task_date = ?",
                (user_id, today)
            )
            missed_today = [dict(zip(['id', 'title', 'priority', 'category'], row))
                           for row in cursor.fetchall()]
            
            # Get completed habits today
            cursor.execute(
                "SELECT id, name FROM habits WHERE user_id = ? AND last_completed = ?",
                (user_id, today)
            )
            completed_habits = [dict(zip(['id', 'name'], row))
                               for row in cursor.fetchall()]
            
            # Get focus sessions today
            cursor.execute(
                "SELECT id, duration_minutes FROM focus_sessions "
                "WHERE user_id = ? AND DATE(started_at) = ?",
                (user_id, today)
            )
            focus_sessions = [dict(zip(['id', 'duration_minutes'], row))
                             for row in cursor.fetchall()]
            
            # Get streak data
            cursor.execute(
                "SELECT streak FROM users WHERE user_id = ?",
                (user_id,)
            )
            user_row = cursor.fetchone()
            current_streak = user_row[0] if user_row else 0
            
            streak_data = {
                'current_streak': current_streak,
                'streak_at_risk': False,
                'daily_completion_rate': 0.6
            }

        # Calculate momentum
        metrics = ExecutionMetrics(user)
        momentum_status = metrics.compute_momentum_status(
            completed_today=completed_today,
            missed_today=missed_today,
            completed_habits_today=completed_habits,
            focus_sessions_today=focus_sessions,
            streak_data=streak_data,
            planned_tasks=len(completed_today) + len(missed_today)
        )

        return jsonify(momentum_status.to_dict()), 200

    except Exception as e:
        logging.error(f"Error getting momentum: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/start-block', methods=['POST'])
def start_execution_block():
    '''Start a focus block'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.json
        block_id = data.get('block_id')
        task_id = data.get('task_id')

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Update block status
            cursor.execute(
                "UPDATE execution_blocks SET status = 'active' WHERE id = ?",
                (block_id,)
            )
            
            # Log event
            cursor.execute(
                "INSERT INTO execution_events (user_id, event_type, block_id, event_data, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (user['user_id'], 'block_started', block_id, json.dumps({'task_id': task_id}),
                 datetime.now().isoformat())
            )
            
            conn.commit()

        return jsonify({'success': True, 'message': 'Block started'}), 200

    except Exception as e:
        logging.error(f"Error starting block: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/complete-block', methods=['POST'])
def complete_execution_block():
    '''Mark a block as complete'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.json
        block_id = data.get('block_id')
        actual_duration = data.get('actual_duration_minutes', 0)
        notes = data.get('notes', '')

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Update block status
            cursor.execute(
                "UPDATE execution_blocks SET status = 'completed', "
                "completed_at = ?, actual_duration_minutes = ?, completion_notes = ? "
                "WHERE id = ?",
                (datetime.now().isoformat(), actual_duration, notes, block_id)
            )
            
            # Log event
            cursor.execute(
                "INSERT INTO execution_events (user_id, event_type, block_id, event_data, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (user['user_id'], 'block_completed', block_id,
                 json.dumps({'duration': actual_duration, 'notes': notes}),
                 datetime.now().isoformat())
            )
            
            conn.commit()

        return jsonify({'success': True, 'message': 'Block completed'}), 200

    except Exception as e:
        logging.error(f"Error completing block: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/preferences', methods=['GET'])
def get_execution_preferences():
    '''Get user execution preferences'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = user['user_id']

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chronotype, task_style, preferred_focus_duration, "
                "preferred_message_tone, enable_notifications FROM execution_preferences "
                "WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                prefs = {
                    'chronotype': row[0],
                    'task_style': row[1],
                    'preferred_focus_duration': row[2],
                    'preferred_message_tone': row[3],
                    'enable_notifications': row[4]
                }
            else:
                # Return defaults
                prefs = {
                    'chronotype': 'standard',
                    'task_style': 'mixed',
                    'preferred_focus_duration': 25,
                    'preferred_message_tone': 'supportive',
                    'enable_notifications': 1
                }

        return jsonify(prefs), 200

    except Exception as e:
        logging.error(f"Error getting preferences: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/preferences', methods=['POST'])
def set_execution_preferences():
    '''Update user execution preferences'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.json
        user_id = user['user_id']

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Try update first
            cursor.execute(
                "UPDATE execution_preferences SET "
                "chronotype = ?, task_style = ?, preferred_focus_duration = ?, "
                "preferred_message_tone = ?, enable_notifications = ?, updated_at = ? "
                "WHERE user_id = ?",
                (data.get('chronotype', 'standard'),
                 data.get('task_style', 'mixed'),
                 data.get('preferred_focus_duration', 25),
                 data.get('preferred_message_tone', 'supportive'),
                 data.get('enable_notifications', 1),
                 datetime.now().isoformat(),
                 user_id)
            )
            
            # If no rows updated, insert
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO execution_preferences "
                    "(user_id, chronotype, task_style, preferred_focus_duration, "
                    "preferred_message_tone, enable_notifications, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, data.get('chronotype', 'standard'),
                     data.get('task_style', 'mixed'),
                     data.get('preferred_focus_duration', 25),
                     data.get('preferred_message_tone', 'supportive'),
                     data.get('enable_notifications', 1),
                     datetime.now().isoformat(),
                     datetime.now().isoformat())
                )
            
            conn.commit()

        return jsonify({'success': True, 'message': 'Preferences updated'}), 200

    except Exception as e:
        logging.error(f"Error setting preferences: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/reflection', methods=['POST'])
def save_execution_reflection():
    '''Save daily execution reflection'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.json
        today = datetime.now().strftime('%Y-%m-%d')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO execution_reflections "
                "(user_id, plan_date, went_well, challenges, improvements, "
                "energy_level, focus_quality, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user['user_id'], today,
                 data.get('went_well', ''),
                 data.get('challenges', ''),
                 data.get('improvements', ''),
                 data.get('energy_level', 3),
                 data.get('focus_quality', 3),
                 datetime.now().isoformat())
            )
            conn.commit()

        return jsonify({'success': True, 'message': 'Reflection saved'}), 200

    except Exception as e:
        logging.error(f"Error saving reflection: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/execution/summary', methods=['GET'])
def get_execution_summary():
    '''Get weekly/monthly execution summary'''
    try:
        user = get_user()
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401

        period = request.args.get('period', 'week')  # week, month
        user_id = user['user_id']
        
        today = datetime.now()
        if period == 'week':
            start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        else:
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
        end_date = today.strftime('%Y-%m-%d')

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get summary stats
            cursor.execute(
                "SELECT "
                "COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed, "
                "COUNT(CASE WHEN status = 'missed' THEN 1 END) as missed, "
                "COUNT(DISTINCT plan_date) as days_planned "
                "FROM ai_daily_tasks "
                "WHERE user_id = ? AND task_date BETWEEN ? AND ?",
                (user_id, start_date, end_date)
            )
            task_stats = cursor.fetchone()
            
            # Get focus stats
            cursor.execute(
                "SELECT COUNT(*) as sessions, SUM(duration_minutes) as total_minutes "
                "FROM focus_sessions "
                "WHERE user_id = ? AND started_at BETWEEN ? AND ?",
                (user_id, start_date, end_date)
            )
            focus_stats = cursor.fetchone()
            
            # Get habit stats
            cursor.execute(
                "SELECT COUNT(*) as completed "
                "FROM habit_analytics "
                "WHERE user_id = ? AND completed = 1 AND created_at BETWEEN ? AND ?",
                (user_id, start_date, end_date)
            )
            habit_stats = cursor.fetchone()

        summary = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'tasks_completed': task_stats[0] if task_stats else 0,
            'tasks_missed': task_stats[1] if task_stats else 0,
            'days_planned': task_stats[2] if task_stats else 0,
            'focus_sessions': focus_stats[0] if focus_stats else 0,
            'total_focus_minutes': focus_stats[1] if focus_stats else 0,
            'habits_completed': habit_stats[0] if habit_stats else 0,
            'completion_rate': 0.0  # Calculate if tasks_completed + missed > 0
        }
        
        if summary['tasks_completed'] + summary['tasks_missed'] > 0:
            summary['completion_rate'] = summary['tasks_completed'] / (summary['tasks_completed'] + summary['tasks_missed'])

        return jsonify(summary), 200

    except Exception as e:
        logging.error(f"Error getting execution summary: {e}")
        return jsonify({'error': str(e)}), 500
"""
