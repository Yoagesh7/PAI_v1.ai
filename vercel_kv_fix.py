"""
Vercel KV (Redis) Adapter for persistent data storage on Vercel
This module provides a drop-in replacement for SQLite when running on Vercel
"""
import os
import json
import logging
from datetime import datetime
from contextlib import contextmanager

# Try to import redis library
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logging.warning("redis library not installed. KV operations will fail. Run: pip install redis")


class VercelKVAdapter:
    """Adapter to use Vercel KV (Redis) as a persistent database"""
    
    def __init__(self):
        self.redis_url = os.getenv("KV_REST_API_URL")
        self.redis_token = os.getenv("KV_REST_API_TOKEN")
        self.client = None
        
        if self.redis_url and self.redis_token and HAS_REDIS:
            try:
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    ssl_certfile=None,
                    ssl_keyfile=None,
                    ssl_ca_certs=None
                )
                # Test connection
                self.client.ping()
                logging.info("✓ Vercel KV connected successfully")
            except Exception as e:
                logging.warning(f"✗ Failed to connect to Vercel KV: {e}")
                self.client = None
        
    def is_available(self):
        """Check if KV is available and connected"""
        return self.client is not None
    
    def set(self, key, value, ttl=None):
        """Set a value in KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        if isinstance(value, dict):
            value = json.dumps(value)
        
        if ttl:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)
    
    def get(self, key):
        """Get a value from KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    def delete(self, key):
        """Delete a value from KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        self.client.delete(key)
    
    def hset(self, key, mapping):
        """Set a hash in KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        if isinstance(mapping, dict):
            mapping = {k: json.dumps(v) if isinstance(v, dict) else v for k, v in mapping.items()}
        
        self.client.hset(key, mapping=mapping)
    
    def hget(self, key, field):
        """Get a hash field from KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        value = self.client.hget(key, field)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    
    def hgetall(self, key):
        """Get all hash fields from KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        values = self.client.hgetall(key)
        result = {}
        for k, v in values.items():
            try:
                result[k] = json.loads(v)
            except:
                result[k] = v
        return result
    
    def lpush(self, key, *values):
        """Push values to a list in KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        json_values = [json.dumps(v) if isinstance(v, dict) else v for v in values]
        self.client.lpush(key, *json_values)
    
    def lrange(self, key, start, end):
        """Get range from list in KV"""
        if not self.is_available():
            raise RuntimeError("Vercel KV not available")
        
        values = self.client.lrange(key, start, end)
        result = []
        for v in values:
            try:
                result.append(json.loads(v))
            except:
                result.append(v)
        return result


# Global KV instance
_kv_instance = None

def get_kv():
    """Get the global KV adapter instance"""
    global _kv_instance
    if _kv_instance is None:
        _kv_instance = VercelKVAdapter()
    return _kv_instance
