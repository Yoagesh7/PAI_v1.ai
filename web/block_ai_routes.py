"""
Block AI API Routes
Notion-like AI integration for block editing
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
import logging
import json
from datetime import datetime
from functools import wraps
import os
import requests

logger = logging.getLogger(__name__)

# Create blueprint
block_ai_bp = Blueprint('block_ai', __name__, url_prefix='/api/block-ai')

# Import AI engines
try:
    from block_ai_engine import BlockAIEngine, TableAIEngine, NotificationEngine
except ImportError:
    logger.warning('block_ai_engine not available')
    BlockAIEngine = None
    TableAIEngine = None
    NotificationEngine = None


def require_auth(f):
    """Require user authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import session
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════
# BLOCK AI ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@block_ai_bp.route('/process', methods=['POST'])
@require_auth
def process_block():
    """
    Process AI request for block content.
    POST /api/block-ai/process
    {
        "block_id": "123",
        "content": "...",
        "mode": "improve" | "summarize" | "expand" | "actions" | "tags" | "custom",
        "custom_prompt": "..." (optional, for custom mode),
        "block_type": "text" | "table" | "list",
        "context": {...}
    }
    """
    if not BlockAIEngine:
        return jsonify({'error': 'AI system unavailable'}), 503
    
    from flask import session
    user_id = session['user_id']
    
    data = request.json or {}
    block_id = data.get('block_id')
    content = data.get('content', '')
    mode = data.get('mode', 'improve')
    custom_prompt = data.get('custom_prompt')
    block_type = data.get('block_type', 'text')
    context = data.get('context')
    
    if not block_id or not content:
        return jsonify({'error': 'block_id and content are required'}), 400
    
    try:
        # Call AI engine (async in production)
        import asyncio
        result = asyncio.run(BlockAIEngine.process_block_request(
            user_id=user_id,
            block_id=block_id,
            content=content,
            mode=mode,
            custom_prompt=custom_prompt,
            block_type=block_type,
            context=context
        ))
        
        return jsonify(result), 200 if result.get('success') else 400
    
    except Exception as e:
        logger.error(f'Block AI error: {e}')
        return jsonify({'error': str(e), 'mode': mode}), 500


@block_ai_bp.route('/stream', methods=['POST'])
@require_auth
def stream_block_ai():
    """
    Stream AI response for real-time display.
    POST /api/block-ai/stream
    {
        "block_id": "123",
        "content": "...",
        "mode": "improve",
        "custom_prompt": "..." (optional)
    }
    """
    if not BlockAIEngine:
        return jsonify({'error': 'AI system unavailable'}), 503
    
    from flask import session
    user_id = session['user_id']
    
    data = request.json or {}
    block_id = data.get('block_id')
    content = data.get('content', '')
    mode = data.get('mode', 'improve')
    custom_prompt = data.get('custom_prompt')
    
    if not block_id or not content:
        return jsonify({'error': 'block_id and content are required'}), 400
    
    async def generate():
        try:
            async for chunk in BlockAIEngine.stream_ai_response(
                user_id=user_id,
                block_id=block_id,
                content=content,
                mode=mode,
                custom_prompt=custom_prompt
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            logger.error(f'Stream error: {e}')
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream'
        }
    )


@block_ai_bp.route('/modes', methods=['GET'])
@require_auth
def get_ai_modes():
    """Get available AI modes for blocks."""
    if not BlockAIEngine:
        return jsonify({'error': 'AI system unavailable'}), 503
    
    modes = []
    for key, value in BlockAIEngine.MODES.items():
        modes.append({
            'id': key,
            'name': key.replace('_', ' ').title(),
            'prompt': value['prompt'],
            'icon': value['icon']
        })
    
    return jsonify({'modes': modes})


# ═══════════════════════════════════════════════════════════════
# TABLE AI ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@block_ai_bp.route('/table/analyze', methods=['POST'])
@require_auth
def analyze_table():
    """
    Analyze table with AI.
    POST /api/block-ai/table/analyze
    {
        "block_id": "123",
        "table_data": [[...], ...],
        "headers": ["col1", "col2", ...]
    }
    """
    if not TableAIEngine:
        return jsonify({'error': 'AI system unavailable'}), 503
    
    from flask import session
    user_id = session['user_id']
    
    data = request.json or {}
    block_id = data.get('block_id')
    table_data = data.get('table_data', [])
    headers = data.get('headers', [])
    
    if not block_id:
        return jsonify({'error': 'block_id is required'}), 400
    
    try:
        import asyncio
        result = asyncio.run(TableAIEngine.analyze_table(
            user_id=user_id,
            table_data=table_data,
            headers=headers
        ))
        
        return jsonify(result), 200 if result.get('success') else 400
    
    except Exception as e:
        logger.error(f'Table analysis error: {e}')
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# NOTIFICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@block_ai_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """Get user notifications."""
    if not NotificationEngine:
        return jsonify({'error': 'Notification system unavailable'}), 503
    
    from flask import session
    user_id = session['user_id']
    
    try:
        # Query notifications from DB
        notifications = []  # Implement in memory.py
        return jsonify({'notifications': notifications})
    
    except Exception as e:
        logger.error(f'Notification fetch error: {e}')
        return jsonify({'error': str(e)}), 500


@block_ai_bp.route('/notifications', methods=['POST'])
@require_auth
def create_notification():
    """
    Create a notification.
    POST /api/block-ai/notifications
    {
        "block_id": "123",
        "type": "due_date" | "mention" | "completion" | "shared" | "comment" | "reminder",
        "message": "...",
        "due_date": "2026-05-30T10:00:00Z",
        "metadata": {...}
    }
    """
    if not NotificationEngine:
        return jsonify({'error': 'Notification system unavailable'}), 503
    
    from flask import session
    user_id = session['user_id']
    
    data = request.json or {}
    block_id = data.get('block_id')
    notification_type = data.get('type')
    message = data.get('message')
    due_date = data.get('due_date')
    metadata = data.get('metadata')
    
    if not all([block_id, notification_type, message]):
        return jsonify({'error': 'block_id, type, and message are required'}), 400
    
    try:
        result = NotificationEngine.create_notification(
            user_id=user_id,
            block_id=block_id,
            notification_type=notification_type,
            message=message,
            due_date=due_date,
            metadata=metadata
        )
        
        return jsonify(result), 201 if result.get('success') else 400
    
    except Exception as e:
        logger.error(f'Notification creation error: {e}')
        return jsonify({'error': str(e)}), 500


@block_ai_bp.route('/due-dates', methods=['GET'])
@require_auth
def check_due_dates():
    """Get upcoming due dates for user."""
    if not NotificationEngine:
        return jsonify({'error': 'Notification system unavailable'}), 503
    
    from flask import session
    user_id = session['user_id']
    
    try:
        due_dates = NotificationEngine.check_due_dates(user_id)
        return jsonify({'due_dates': due_dates})
    
    except Exception as e:
        logger.error(f'Due date check error: {e}')
        return jsonify({'error': str(e)}), 500


# Export blueprint
__all__ = ['block_ai_bp']


@block_ai_bp.route('/nvidia/proxy', methods=['POST'])
@require_auth
def nvidia_proxy():
    """
    Proxy to NVIDIA Integrate API. Server-side only — the API key must be set in NV_API_KEY env var.
    POST /api/block-ai/nvidia/proxy
    Body: forwarded JSON payload for NVIDIA Integrate (model, messages, etc.)
    Returns NVIDIA response JSON (non-stream) or streams SSE when `stream: true`.
    """
    key = os.getenv('NV_API_KEY')
    if not key:
        return jsonify({'error': 'NV_API_KEY not configured on server'}), 503

    payload = request.json or {}
    stream = bool(payload.get('stream', False))
    invoke_url = 'https://integrate.api.nvidia.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {key}',
        'Accept': 'text/event-stream' if stream else 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        resp = requests.post(invoke_url, headers=headers, json=payload, stream=stream, timeout=60)
        # If streaming, proxy the lines back as-is
        if stream:
            def generate():
                try:
                    for line in resp.iter_lines():
                        if line:
                            yield line.decode('utf-8') + "\n"
                except Exception as e:
                    logger.error(f'NVIDIA proxy stream error: {e}')
                    yield json.dumps({'error': str(e)}) + "\n"
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        # Non-streaming: forward JSON
        try:
            return jsonify(resp.json()), resp.status_code
        except Exception:
            return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type', 'application/octet-stream'))
    except Exception as e:
        logger.error(f'NVIDIA proxy error: {e}')
        return jsonify({'error': str(e)}), 500
