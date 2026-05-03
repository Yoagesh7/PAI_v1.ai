import sqlite3
import json
from datetime import datetime
from memory import get_db

def create_knowledge_block(user_id, type, title, content, tags="[]", meta="{}"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_blocks (user_id, type, title, content, tags, meta)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, type, title, content, json.dumps(tags), json.dumps(meta)))
        conn.commit()
        return cursor.lastrowid

def get_user_knowledge_blocks(user_id, type_filter=None):
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if type_filter and type_filter != 'all':
            cursor.execute("SELECT * FROM knowledge_blocks WHERE user_id=? AND type=? ORDER BY created_at DESC", (user_id, type_filter))
        else:
            cursor.execute("SELECT * FROM knowledge_blocks WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_knowledge_block(user_id, block_id):
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_blocks WHERE id=? AND user_id=?", (block_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None
        
def delete_knowledge_block(user_id, block_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_blocks WHERE id=? AND user_id=?", (block_id, user_id))
        conn.commit()

def update_knowledge_block(user_id, block_id, title=None, content=None, type=None, tags=None, meta=None):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Build dynamic query
        fields = []
        values = []
        if title is not None: fields.append("title=?"); values.append(title)
        if content is not None: fields.append("content=?"); values.append(content)
        if type is not None: fields.append("type=?"); values.append(type)
        if tags is not None: fields.append("tags=?"); values.append(json.dumps(tags))
        if meta is not None: fields.append("meta=?"); values.append(json.dumps(meta))
        
        if not fields: return
        
        values.append(block_id)
        values.append(user_id)
        
        sql = f"UPDATE knowledge_blocks SET {', '.join(fields)} WHERE id=? AND user_id=?"
        cursor.execute(sql, tuple(values))
        conn.commit()
