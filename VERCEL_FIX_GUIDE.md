# Vercel Workspace Block Persistence Fix

## Problem

Workspace blocks (Smart Blocks) are not persisting after saving on Vercel because:

1. **SQLite on `/tmp` is ephemeral** - Each deployment wipes `/tmp`
2. **No DATABASE_URL configured** - Vercel defaults to SQLite, not PostgreSQL
3. **Connection pooling issues** - Concurrent writes fail

## Solution

### Option 1: Use Vercel KV (Redis) - RECOMMENDED ⭐

Fastest and easiest solution for Vercel.

#### Setup Steps:

1. **Create Vercel KV Store**:
   ```bash
   vercel link (if not linked)
   vercel storage create
   ```
   Choose "KV" database

2. **Environment Variables Automatically Set**:
   - `KV_URL`
   - `KV_REST_API_URL`
   - `KV_REST_API_TOKEN`

3. **Update `smart_blocks_db.py`**:

Replace the import section:
```python
# At top of smart_blocks_db.py
import os
import json
from datetime import datetime

# Check if using Vercel KV
if os.getenv('KV_REST_API_URL'):
    import redis
    kv = redis.from_url(
        os.getenv('KV_URL'),
        decode_responses=True
    )
    USE_KV = True
else:
    USE_KV = False
    from memory import get_db
```

Replace `update_smart_block()`:
```python
def update_smart_block(block_id, title=None, content=None, metadata=None):
    """Update a smart block (KV on Vercel, SQLite locally)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if USE_KV:
        # Use Vercel KV
        block_key = f"block:{block_id}"
        block = kv.hgetall(block_key)
        
        if not block:
            return False
        
        if title is not None:
            block['title'] = title
        if content is not None:
            block['content'] = content
        if metadata is not None:
            block['metadata'] = json.dumps(metadata)
        
        block['updated_at'] = timestamp
        
        # Save to KV with 30-day expiry
        kv.hset(block_key, mapping=block)
        kv.expire(block_key, 30 * 24 * 60 * 60)  # 30 days
        
        return True
    else:
        # Use SQLite (local)
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
            
            updates.append("updated_at=?")
            values.append(timestamp)
            values.append(block_id)
            
            cursor.execute(f"UPDATE smart_blocks SET {', '.join(updates)} WHERE id=?", values)
            conn.commit()
            
            return True
```

4. **Test**:
   ```bash
   # Local
   python -c "from smart_blocks_db import update_smart_block; update_smart_block(1, title='Test')"
   
   # Vercel
   vercel env pull .env.local
   python -c "from smart_blocks_db import update_smart_block; update_smart_block(1, title='Test Vercel')"
   ```

---

### Option 2: Use PostgreSQL (Supabase/Neon) - ADVANCED

Better for long-term, more data, and analytics.

#### Setup Steps:

1. **Create PostgreSQL Database**:
   - **Supabase**: https://supabase.com → New Project
   - **Neon**: https://neon.tech → Create Project
   - **Railway**: https://railway.app → New Service → PostgreSQL

2. **Get Connection String**:
   - Format: `postgresql://username:password@host:port/database?sslmode=require`

3. **Set Vercel Environment Variable**:
   ```bash
   vercel env add DATABASE_URL
   # Paste your PostgreSQL connection string
   ```

4. **Run Migrations on Vercel**:
   ```bash
   vercel env pull .env.local
   python memory.py  # This runs init_db() automatically
   ```

5. **Deploy**:
   ```bash
   git add .
   git commit -m "Add PostgreSQL for Vercel"
   git push
   ```

---

### Option 3: Enhanced SQLite with Automatic Retry - FALLBACK

If you want to keep SQLite but improve reliability:

Create `vercel_db_fix.py`:

```python
import os
import sqlite3
import time
from contextlib import contextmanager

@contextmanager
def get_resilient_db():
    """Get database connection with automatic retry for Vercel."""
    is_vercel = bool(os.getenv("VERCEL"))
    db_path = "/tmp/partnerai_data.db" if is_vercel else "partnerai.db"
    
    # Retry logic
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
            
            yield conn
            return
        except sqlite3.DatabaseError as e:
            if attempt < max_retries - 1:
                print(f"DB error (retry {attempt+1}): {e}")
                time.sleep(retry_delay)
            else:
                raise

def update_smart_block_resilient(block_id, title=None, content=None, metadata=None):
    """Update smart block with retry logic."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_resilient_db() as conn:
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
        
        updates.append("updated_at=?")
        values.append(timestamp)
        values.append(block_id)
        
        cursor.execute(f"UPDATE smart_blocks SET {', '.join(updates)} WHERE id=?", values)
        conn.commit()
```

Update `smart_blocks_db.py`:
```python
from vercel_db_fix import get_resilient_db

def update_smart_block(block_id, title=None, content=None, metadata=None):
    """Update an existing block with Vercel resilience."""
    from datetime import datetime
    import json
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_resilient_db() as conn:
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
        
        updates.append("updated_at=?")
        values.append(timestamp)
        values.append(block_id)
        
        if updates:
            cursor.execute(f"UPDATE smart_blocks SET {', '.join(updates)} WHERE id=?", values)
            conn.commit()
```

---

## Recommended Path Forward

### For MVP/Testing:
**Use Vercel KV (Option 1)** - Takes 5 minutes, works instantly

### For Production:
**Use PostgreSQL (Option 2)** - More reliable, better performance, scalable

### For Local Development:
SQLite works fine (no changes needed)

---

## Implementation Priority

1. **This week**: Deploy Vercel KV fix (fast)
2. **Next sprint**: Migrate to PostgreSQL (robust)
3. **Ongoing**: Monitor Vercel metrics for performance

---

## Testing Checklist

After implementation:

- [ ] Can create workspace block locally
- [ ] Can create workspace block on Vercel
- [ ] Block persists after page refresh (local)
- [ ] Block persists after deployment (Vercel)
- [ ] Multiple blocks save correctly
- [ ] Concurrent saves don't corrupt data
- [ ] Deleted blocks are removed
- [ ] Updated blocks reflect changes

---

## Troubleshooting

### Problem: "Connection refused" on Vercel
**Solution**: Check that DATABASE_URL or KV_URL is set in Vercel environment

### Problem: "Database is locked" locally
**Solution**: Close other processes, or restart Flask

### Problem: "Data lost after redeployment"
**Solution**: This is expected with SQLite. Use KV or PostgreSQL.

### Problem: "Slow saves on Vercel"
**Solution**: Use PostgreSQL instead of SQLite

---

## Code Locations to Update

1. **smart_blocks_db.py** - `update_smart_block()` function (line 67)
2. **web/app.py** - `/api/blocks/<id>` PUT endpoint (line ~3630)
3. **memory.py** - Already has PostgreSQL support, no changes needed

---

## Environment Variables Needed

### For Vercel KV:
```
KV_URL=rediss://...
KV_REST_API_URL=https://...
KV_REST_API_TOKEN=...
```

### For PostgreSQL:
```
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
```

### For Local Development:
```
# No env vars needed - uses local partnerai.db
```

---

**Next Step**: Choose between KV (fast) or PostgreSQL (robust) and implement!
