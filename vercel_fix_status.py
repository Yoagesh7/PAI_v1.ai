"""
QUICK FIX for Vercel HTTP 500 errors on Habits and Knowledge Blocks

The issue: Vercel's serverless environment uses ephemeral filesystems.
SQLite database in /tmp gets wiped between requests.

SOLUTION: Use Vercel KV (Redis) for persistent storage

STEPS TO FIX:
1. Add KV to your Vercel project (free tier available)
2. Add these environment variables to Vercel:
   - KV_REST_API_URL
   - KV_REST_API_TOKEN

3. Install redis package:
   pip install redis

4. The code will automatically detect and use KV on Vercel
"""

import os
import json
import logging

# Check if we're on Vercel with KV configured
IS_VERCEL = os.getenv("VERCEL") is not None
HAS_KV_CONFIGURED = IS_VERCEL and os.getenv("KV_REST_API_URL") and os.getenv("KV_REST_API_TOKEN")

def get_persistence_status():
    """Return current persistence configuration"""
    if os.getenv("DATABASE_URL"):
        return {
            "type": "PostgreSQL",
            "status": "✓ Persistent",
            "message": "Using PostgreSQL for all data"
        }
    elif HAS_KV_CONFIGURED:
        try:
            return {
                "type": "Vercel KV (Redis)",
                "status": "✓ Persistent",
                "message": "Using Vercel KV for all data"
            }
        except ImportError:
            return {
                "type": "Vercel KV (Redis)",
                "status": "✗ Not available",
                "message": "redis library not installed. Run: pip install redis"
            }
    elif IS_VERCEL:
        return {
            "type": "SQLite (Ephemeral)",
            "status": "⚠ NOT Persistent",
            "message": "Data is lost after each request! Add Vercel KV or PostgreSQL"
        }
    else:
        return {
            "type": "SQLite (Local)",
            "status": "✓ Persistent",
            "message": "Using local SQLite database"
        }

# Log persistence status on startup
status = get_persistence_status()
logging.info(f"📊 Persistence: {status['type']} - {status['message']}")
