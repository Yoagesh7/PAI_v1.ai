"""
Widgets Database Helper Functions
Handles CRUD operations for dashboard widgets and their configurations.
"""
import sqlite3
from datetime import datetime
import json
from memory import get_db

def init_widgets_db():
    """Initialize widgets table if it doesn't exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if we are on PostgreSQL
        id_type = "SERIAL" if "psycopg2" in str(type(conn)) else "INTEGER PRIMARY KEY AUTOINCREMENT"
        
        # Widgets Table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS widgets (
                id {id_type},
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                config TEXT DEFAULT '{{}}',
                position_x INTEGER DEFAULT 0,
                position_y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 4,
                height INTEGER DEFAULT 4,
                is_visible BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_widgets_user_id 
            ON widgets(user_id)
        """)
        
        conn.commit()
        print("DEBUG_WIDGETS: Database initialized successfully")

def create_widget(user_id, widget_type, config=None, position_x=0, position_y=0, width=4, height=4):
    """Create a new widget for user's dashboard."""
    try:
        init_widgets_db()
        
        if config is None:
            config = {}
        
        config_json = json.dumps(config) if isinstance(config, dict) else config
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO widgets (user_id, type, config, position_x, position_y, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, widget_type, config_json, position_x, position_y, width, height))
            conn.commit()
            widget_id = cursor.lastrowid
            print(f"DEBUG_WIDGETS: Created widget ID {widget_id} for user {user_id}, type={widget_type}")
            return widget_id
    except Exception as e:
        import logging
        logging.error(f"Error creating widget: {e}")
        raise e

def get_user_widgets(user_id):
    """Get all widgets for a user."""
    try:
        init_widgets_db()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, type, config, position_x, position_y, width, height, is_visible, created_at
                FROM widgets
                WHERE user_id = ? AND is_visible = 1
                ORDER BY position_y, position_x
            """, (user_id,))
            
            widgets = []
            for row in cursor.fetchall():
                try:
                    config = json.loads(row[2]) if row[2] else {}
                except:
                    config = {}
                
                widgets.append({
                    'id': row[0],
                    'type': row[1],
                    'config': config,
                    'position_x': row[3],
                    'position_y': row[4],
                    'width': row[5],
                    'height': row[6],
                    'is_visible': row[7],
                    'created_at': row[8]
                })
            
            print(f"DEBUG_WIDGETS: Fetched {len(widgets)} widgets for user {user_id}")
            return widgets
    except Exception as e:
        import logging
        logging.error(f"Error fetching widgets: {e}")
        raise e

def update_widget(widget_id, user_id, **kwargs):
    """Update widget configuration, position, or size."""
    try:
        init_widgets_db()
        
        # Allowed fields to update
        allowed_fields = ['type', 'config', 'position_x', 'position_y', 'width', 'height', 'is_visible']
        
        # Build update query
        update_parts = []
        update_values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'config' and isinstance(value, dict):
                    value = json.dumps(value)
                update_parts.append(f"{field} = ?")
                update_values.append(value)
        
        if not update_parts:
            raise ValueError("No valid fields to update")
        
        update_parts.append("updated_at = ?")
        update_values.extend([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), widget_id, user_id])
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Verify ownership
            cursor.execute("SELECT id FROM widgets WHERE id=? AND user_id=?", (widget_id, user_id))
            if not cursor.fetchone():
                raise ValueError("Widget not found or unauthorized")
            
            query = f"""
                UPDATE widgets
                SET {', '.join(update_parts)}
                WHERE id = ? AND user_id = ?
            """
            
            cursor.execute(query, update_values)
            conn.commit()
            
            print(f"DEBUG_WIDGETS: Updated widget ID {widget_id} for user {user_id}")
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating widget: {e}")
        raise e

def delete_widget(widget_id, user_id):
    """Delete a widget (soft delete - sets is_visible to 0)."""
    try:
        init_widgets_db()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Verify ownership
            cursor.execute("SELECT id FROM widgets WHERE id=? AND user_id=?", (widget_id, user_id))
            if not cursor.fetchone():
                return False
            
            # Soft delete
            cursor.execute("""
                UPDATE widgets SET is_visible = 0, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), widget_id, user_id))
            
            conn.commit()
            print(f"DEBUG_WIDGETS: Deleted widget ID {widget_id} for user {user_id}")
            return True
    except Exception as e:
        import logging
        logging.error(f"Error deleting widget: {e}")
        raise e

def update_widget_positions(user_id, positions):
    """
    Update positions for multiple widgets at once.
    
    Args:
        user_id: User ID
        positions: List of dicts with 'id', 'position_x', 'position_y'
    """
    try:
        init_widgets_db()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            for pos in positions:
                widget_id = pos.get('id')
                x = pos.get('position_x', 0)
                y = pos.get('position_y', 0)
                
                # Verify ownership
                cursor.execute("SELECT id FROM widgets WHERE id=? AND user_id=?", (widget_id, user_id))
                if not cursor.fetchone():
                    continue
                
                cursor.execute("""
                    UPDATE widgets
                    SET position_x = ?, position_y = ?, updated_at = ?
                    WHERE id = ?
                """, (x, y, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), widget_id))
            
            conn.commit()
            print(f"DEBUG_WIDGETS: Updated positions for {len(positions)} widgets for user {user_id}")
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating widget positions: {e}")
        raise e

def get_widget_by_id(widget_id, user_id):
    """Get a single widget by ID."""
    try:
        init_widgets_db()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, type, config, position_x, position_y, width, height, is_visible
                FROM widgets
                WHERE id = ? AND user_id = ?
            """, (widget_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            try:
                config = json.loads(row[2]) if row[2] else {}
            except:
                config = {}
            
            return {
                'id': row[0],
                'type': row[1],
                'config': config,
                'position_x': row[3],
                'position_y': row[4],
                'width': row[5],
                'height': row[6],
                'is_visible': row[7]
            }
    except Exception as e:
        import logging
        logging.error(f"Error fetching widget: {e}")
        raise e

def reset_user_dashboard(user_id):
    """Reset user's dashboard to defaults (soft delete all widgets)."""
    try:
        init_widgets_db()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE widgets
                SET is_visible = 0, updated_at = ?
                WHERE user_id = ?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
            conn.commit()
            print(f"DEBUG_WIDGETS: Reset dashboard for user {user_id}")
            return True
    except Exception as e:
        import logging
        logging.error(f"Error resetting dashboard: {e}")
        raise e
