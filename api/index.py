import os
import sys

# Add parent directory to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)

print("🔄 Loading Flask app from web.app module...", flush=True)
from web.app import app

# Explicit exports for Vercel Python runtime
application = app
handler = app

print("✅ Flask app loaded successfully", flush=True)
print(f"📋 Registered routes: {len(app.url_map._rules)}", flush=True)

# List some routes for debugging
for rule in list(app.url_map._rules)[:10]:
	print(f"   - {rule.rule} {rule.methods}", flush=True)

__all__ = ['app', 'application', 'handler']
