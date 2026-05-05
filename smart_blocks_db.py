"""
Smart Blocks, AI Memory, and Intelligence System
Database helper functions for advanced PartnerAI features
"""
import json
import logging
import os
from datetime import datetime, timedelta
from memory import get_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detect environment
IS_VERCEL = bool(os.getenv("VERCEL"))
IS_PRODUCTION = bool(os.getenv("PRODUCTION"))

# ===== SMART BLOCKS SYSTEM =====

def create_smart_block(user_id, block_type, title, content, metadata=None):
    """Create a new smart block.
    
    Args:
        user_id: User ID
        block_type: 'idea', 'task', 'learning', 'habit', 'reflection'
        title: Block title
        content: Block content
        metadata: Optional JSON metadata
    
    Returns:
        block_id or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_str = json.dumps(metadata) if metadata else None
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO smart_blocks (user_id, block_type, title, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, block_type, title, content, metadata_str, timestamp, timestamp))
            conn.commit()
            block_id = cursor.lastrowid
            
            logger.info(f"✅ Block {block_id} created for user {user_id}")
            return block_id
    except Exception as e:
        logger.error(f"❌ Error creating block: {e}", exc_info=True)
        return None


def get_user_blocks(user_id, block_type=None, limit=50):
    """Get blocks for a user, optionally filtered by type."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if block_type:
                cursor.execute("""
                    SELECT id, block_type, title, content, metadata, created_at, updated_at
                    FROM smart_blocks WHERE user_id=? AND block_type=?
                    ORDER BY updated_at DESC LIMIT ?
                """, (user_id, block_type, limit))
            else:
                cursor.execute("""
                    SELECT id, block_type, title, content, metadata, created_at, updated_at
                    FROM smart_blocks WHERE user_id=?
                    ORDER BY updated_at DESC LIMIT ?
                """, (user_id, limit))
            
            rows = cursor.fetchall()
            return [{
                'id': r[0],
                'type': r[1],
                'title': r[2],
                'content': r[3],
                'metadata': json.loads(r[4]) if r[4] else {},
                'created_at': r[5],
                'updated_at': r[6]
            } for r in rows]
    except Exception as e:
        logger.error(f"❌ Error getting blocks for user {user_id}: {e}", exc_info=True)
        return []


def update_smart_block(block_id, title=None, content=None, metadata=None):
    """Update an existing block.
    
    Returns: True if successful, False otherwise
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with get_db() as conn:
            cursor = conn.cursor()
            updates = []
            values = []
            
            if title is not None:
                updates.append("title=?")
                values.append(title)
            if content is not None:
                updates.append("content=?")
                values.append(content)
            if metadata is not None:
                updates.append("metadata=?")
                values.append(json.dumps(metadata))
            
            if not updates:
                logger.warning(f"No updates provided for block {block_id}")
                return True
            
            updates.append("updated_at=?")
            values.append(timestamp)
            values.append(block_id)
            
            cursor.execute(f"UPDATE smart_blocks SET {', '.join(updates)} WHERE id=?", values)
            conn.commit()
            
            # Verify update
            cursor.execute("SELECT id FROM smart_blocks WHERE id=?", (block_id,))
            if cursor.fetchone():
                logger.info(f"✅ Block {block_id} updated successfully")
                return True
            else:
                logger.warning(f"⚠️ Block {block_id} not found after update")
                return False
    except Exception as e:
        logger.error(f"❌ Error updating block {block_id}: {e}", exc_info=True)
        if IS_VERCEL:
            logger.error(f"Vercel detected - check DATABASE_URL or KV_URL environment variables")
        return False


def delete_smart_block(block_id):
    """Delete a block and its relationships.
    
    Returns: True if successful, False otherwise
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Delete relationships first
            cursor.execute("DELETE FROM block_relationships WHERE block_id_1=? OR block_id_2=?", (block_id, block_id))
            # Delete block
            cursor.execute("DELETE FROM smart_blocks WHERE id=?", (block_id,))
            conn.commit()
            
            logger.info(f"✅ Block {block_id} deleted successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Error deleting block {block_id}: {e}", exc_info=True)
        return False


def link_blocks(block_id_1, block_id_2, relationship_type='related'):
    """Create a relationship between two blocks.
    
    Args:
        relationship_type: 'related', 'depends_on', 'part_of', 'leads_to'
    
    Returns: True if successful, False otherwise
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with get_db() as conn:
            cursor = conn.cursor()
            # Check if relationship already exists
            cursor.execute("""
                SELECT id FROM block_relationships 
                WHERE (block_id_1=? AND block_id_2=?) OR (block_id_1=? AND block_id_2=?)
            """, (block_id_1, block_id_2, block_id_2, block_id_1))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO block_relationships (block_id_1, block_id_2, relationship_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (block_id_1, block_id_2, relationship_type, timestamp))
                conn.commit()
                logger.info(f"✅ Linked blocks {block_id_1} ↔ {block_id_2}")
                return True
            else:
                logger.info(f"ℹ️ Relationship already exists between {block_id_1} and {block_id_2}")
                return True
    except Exception as e:
        logger.error(f"❌ Error linking blocks {block_id_1} and {block_id_2}: {e}", exc_info=True)
        return False


def get_block_relationships(block_id):
    """Get all blocks related to a given block."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT br.id, br.block_id_1, br.block_id_2, br.relationship_type, 
                       b1.title as title_1, b2.title as title_2
                FROM block_relationships br
                LEFT JOIN smart_blocks b1 ON br.block_id_1 = b1.id
                LEFT JOIN smart_blocks b2 ON br.block_id_2 = b2.id
                WHERE br.block_id_1=? OR br.block_id_2=?
            """, (block_id, block_id))
            
            rows = cursor.fetchall()
            return [{
                'rel_id': r[0],
                'block_1': r[1],
                'block_2': r[2],
                'type': r[3],
                'other_block_id': r[2] if r[1] == block_id else r[1],
                'other_block_title': r[5] if r[1] == block_id else r[4]
            } for r in rows]
    except Exception as e:
        logger.error(f"❌ Error getting relationships for block {block_id}: {e}", exc_info=True)
        return []


def search_blocks(user_id, query):
    """Search blocks by title or content."""
    with get_db() as conn:
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT id, block_type, title, content, created_at
            FROM smart_blocks 
            WHERE user_id=? AND (title LIKE ? OR content LIKE ?)
            ORDER BY updated_at DESC LIMIT 20
        """, (user_id, search_term, search_term))
        
        rows = cursor.fetchall()
        return [{
            'id': r[0],
            'type': r[1],
            'title': r[2],
            'content': r[3],
            'created_at': r[4]
        } for r in rows]


# ===== AI MEMORY SYSTEM =====

def save_ai_memory(user_id, memory_key, memory_value, confidence=0.5):
    """Store or update AI memory about the user.
    
    Args:
        memory_key: e.g., 'best_work_time', 'weak_habit', 'skill_level', 'goal_focus'
        memory_value: JSON-serializable value
        confidence: 0.0 to 1.0, how confident the AI is
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value_str = json.dumps(memory_value) if not isinstance(memory_value, str) else memory_value
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if memory key exists
        cursor.execute("SELECT id FROM ai_user_memory WHERE user_id=? AND memory_key=?", (user_id, memory_key))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE ai_user_memory 
                SET memory_value=?, confidence_score=?, last_updated=?
                WHERE user_id=? AND memory_key=?
            """, (value_str, confidence, timestamp, user_id, memory_key))
        else:
            cursor.execute("""
                INSERT INTO ai_user_memory (user_id, memory_key, memory_value, confidence_score, last_updated)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, memory_key, value_str, confidence, timestamp))
        conn.commit()


def get_ai_memory(user_id, memory_key=None):
    """Retrieve AI memory for a user.
    
    Returns: dict of {memory_key: memory_value} if memory_key is None,
             else returns single value
    """
    with get_db() as conn:
        cursor = conn.cursor()
        if memory_key:
            cursor.execute("""
                SELECT memory_value FROM ai_user_memory 
                WHERE user_id=? AND memory_key=?
            """, (user_id, memory_key))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
            return None
        else:
            cursor.execute("""
                SELECT memory_key, memory_value, confidence_score 
                FROM ai_user_memory WHERE user_id=?
            """, (user_id,))
            rows = cursor.fetchall()
            result = {}
            for r in rows:
                try:
                    result[r[0]] = {'value': json.loads(r[1]), 'confidence': r[2]}
                except:
                    result[r[0]] = {'value': r[1], 'confidence': r[2]}
            return result


# ===== HABIT ANALYTICS =====

def log_habit_event(user_id, habit_name, completed, scheduled_time=None, actual_time=None, duration=None):
    """Log a habit completion or miss event."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO habit_analytics 
            (user_id, habit_name, completed, scheduled_time, actual_time, completion_duration, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, habit_name, 1 if completed else 0, scheduled_time, actual_time, duration, timestamp))
        conn.commit()


def analyze_habit_patterns(user_id, habit_name, days=30):
    """Analyze habit completion patterns over the last N days.
    
    Returns:
        {
            'completion_rate': float,
            'best_time': str,
            'worst_time': str,
            'streak': int,
            'failure_reasons': list
        }
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT completed, scheduled_time, actual_time, created_at
            FROM habit_analytics
            WHERE user_id=? AND habit_name=? AND created_at >= ?
            ORDER BY created_at ASC
        """, (user_id, habit_name, cutoff))
        
        events = cursor.fetchall()
        
        if not events:
            return {'completion_rate': 0, 'total_attempts': 0}
        
        total = len(events)
        completed = sum(1 for e in events if e[0] == 1)
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        # Time of day analysis
        time_success = {}
        for event in events:
            if event[2]:  # actual_time exists
                hour = event[2].split(':')[0] if ':' in event[2] else 'unknown'
                if hour not in time_success:
                    time_success[hour] = {'success': 0, 'total': 0}
                time_success[hour]['total'] += 1
                if event[0] == 1:
                    time_success[hour]['success'] += 1
        
        best_time = max(time_success.items(), key=lambda x: x[1]['success']/x[1]['total']) if time_success else None
        
        # Current streak
        streak = 0
        for event in reversed(events):
            if event[0] == 1:
                streak += 1
            else:
                break
        
        return {
            'completion_rate': round(completion_rate, 1),
            'total_attempts': total,
            'total_completed': completed,
            'best_time': f"{best_time[0]}:00" if best_time else None,
            'current_streak': streak
        }


# ===== WEEKLY REPORTS =====

def save_weekly_report(user_id, progress_score, strengths, weaknesses, strategy, report_data=None):
    """Save a generated weekly report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    
    data_str = json.dumps(report_data) if report_data else None
    strengths_str = json.dumps(strengths) if isinstance(strengths, (list, dict)) else strengths
    weaknesses_str = json.dumps(weaknesses) if isinstance(weaknesses, (list, dict)) else weaknesses
    strategy_str = json.dumps(strategy) if isinstance(strategy, (list, dict)) else strategy
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weekly_reports 
            (user_id, week_start_date, progress_score, strengths, weaknesses, strategy, report_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, week_start, progress_score, strengths_str, weaknesses_str, strategy_str, data_str, timestamp))
        conn.commit()
        return cursor.lastrowid


def get_weekly_reports(user_id, limit=10):
    """Get recent weekly reports for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, week_start_date, progress_score, strengths, weaknesses, strategy, created_at
            FROM weekly_reports
            WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        return [{
            'id': r[0],
            'week_start': r[1],
            'progress_score': r[2],
            'strengths': r[3],
            'weaknesses': r[4],
            'strategy': r[5],
            'created_at': r[6]
        } for r in rows]


# ===== FOCUS SESSIONS =====

def create_focus_session(user_id, task_description, micro_tasks, duration_minutes):
    """Start a new focus session."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks_str = json.dumps(micro_tasks) if isinstance(micro_tasks, list) else micro_tasks
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO focus_sessions 
            (user_id, task_description, micro_tasks, duration_minutes, started_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, task_description, tasks_str, duration_minutes, timestamp))
        conn.commit()
        return cursor.lastrowid


def complete_focus_session(session_id, completed_tasks, focus_score, feedback=None):
    """Mark a focus session as complete with analytics."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE focus_sessions
            SET completed_tasks=?, focus_score=?, feedback=?, completed_at=?
            WHERE id=?
        """, (completed_tasks, focus_score, feedback, timestamp, session_id))
        conn.commit()


def get_focus_sessions(user_id, limit=10):
    """Get recent focus sessions for analysis."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, task_description, micro_tasks, duration_minutes, 
                   completed_tasks, focus_score, feedback, started_at, completed_at
            FROM focus_sessions
            WHERE user_id=?
            ORDER BY started_at DESC LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        return [{
            'id': r[0],
            'task': r[1],
            'micro_tasks': json.loads(r[2]) if r[2] else [],
            'duration': r[3],
            'completed': r[4],
            'score': r[5],
            'feedback': r[6],
            'started_at': r[7],
            'completed_at': r[8]
        } for r in rows]
