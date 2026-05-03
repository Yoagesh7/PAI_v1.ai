import os
import sys
import traceback

# Add parent directory to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)

# Attempt to load the Flask app with detailed error handling
try:
	print(f"🔄 Loading Flask app from web.app module...", flush=True)
	from web.app import app
	print(f"✅ Flask app loaded successfully", flush=True)
	print(f"📋 Registered routes: {len(app.url_map._rules)}", flush=True)
	
	# List some routes for debugging
	for rule in list(app.url_map._rules)[:10]:
		print(f"   - {rule.rule} {rule.methods}", flush=True)
	
except ImportError as e:
	print(f"❌ ImportError loading Flask app: {e}", flush=True)
	traceback.print_exc()
	raise
except Exception as e:
	print(f"❌ Error loading Flask app: {e}", flush=True)
	traceback.print_exc()
	raise

# Export app as WSGI application for Vercel
__all__ = ['app']
