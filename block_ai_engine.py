"""
Block AI Engine - Full Notion-like AI Integration
Handles AI prompts for blocks, content, and tables
"""
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing AI modules
try:
    from nvidia_llm import rag_system, call_ai
except ImportError:
    rag_system = None
    call_ai = None


class BlockAIEngine:
    """Main AI engine for block editing operations"""
    
    # AI Modes for blocks
    MODES = {
        'improve': {
            'prompt': 'Improve the clarity, grammar, and impact of this content while keeping it concise.',
            'icon': '✍️'
        },
        'summarize': {
            'prompt': 'Create a brief, bullet-point summary of this content.',
            'icon': '📋'
        },
        'expand': {
            'prompt': 'Expand this content with more details, examples, and explanation.',
            'icon': '🔭'
        },
        'actions': {
            'prompt': 'Extract action items and next steps from this content in a numbered list.',
            'icon': '⚡'
        },
        'tags': {
            'prompt': 'Suggest 5-7 relevant tags for this content. Return as comma-separated list.',
            'icon': '🏷️'
        },
        'tone_professional': {
            'prompt': 'Rewrite this in a professional, formal tone.',
            'icon': '💼'
        },
        'tone_casual': {
            'prompt': 'Rewrite this in a casual, conversational tone.',
            'icon': '💬'
        },
        'tone_creative': {
            'prompt': 'Rewrite this in a creative, engaging tone.',
            'icon': '✨'
        },
        'translate': {
            'prompt': 'Translate this content to the user-specified language.',
            'icon': '🌐'
        },
        'custom': {
            'prompt': 'Use user-provided prompt',
            'icon': '🤖'
        }
    }
    
    TABLE_MODES = {
        'analyze': {
            'prompt': 'Analyze this table and provide key insights in bullet points.',
            'icon': '📊'
        },
        'summarize': {
            'prompt': 'Summarize the data in this table with key statistics.',
            'icon': '📈'
        },
        'generate': {
            'prompt': 'Generate new rows for this table based on the pattern.',
            'icon': '➕'
        },
        'clean': {
            'prompt': 'Clean and standardize this table data, fixing inconsistencies.',
            'icon': '🧹'
        }
    }
    
    @staticmethod
    async def process_block_request(
        user_id: str,
        block_id: str,
        content: str,
        mode: str,
        custom_prompt: Optional[str] = None,
        block_type: str = 'text',
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process AI request for block content.
        
        Args:
            user_id: User ID
            block_id: Block ID
            content: Current block content
            mode: AI mode (improve, summarize, expand, etc.)
            custom_prompt: Custom prompt for 'custom' mode
            block_type: Type of block (text, table, list)
            context: Additional context (title, tags, etc.)
        
        Returns:
            {
                'success': bool,
                'result': str,
                'mode': str,
                'timestamp': str,
                'tokens_used': int,
                'error': str (if failed)
            }
        """
        try:
            if not content or not content.strip():
                return {
                    'success': False,
                    'error': 'Content is empty',
                    'mode': mode
                }
            
            # Get the prompt
            if mode == 'custom':
                if not custom_prompt:
                    return {'success': False, 'error': 'Custom prompt is required', 'mode': mode}
                prompt_text = custom_prompt
            elif mode in BlockAIEngine.MODES:
                prompt_text = BlockAIEngine.MODES[mode]['prompt']
            elif mode in BlockAIEngine.TABLE_MODES:
                prompt_text = BlockAIEngine.TABLE_MODES[mode]['prompt']
            else:
                return {
                    'success': False,
                    'error': f'Unknown mode: {mode}',
                    'mode': mode
                }
            
            # Build full prompt with context
            full_prompt = BlockAIEngine._build_full_prompt(
                content, prompt_text, block_type, context
            )
            
            # Call AI
            if call_ai:
                response = await call_ai(full_prompt)
                result = response if isinstance(response, str) else str(response)
            else:
                logger.warning('AI system not available')
                result = f"[AI unavailable] {prompt_text}"
            
            return {
                'success': True,
                'result': result,
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'tokens_used': len(result.split())  # Rough estimate
            }
        
        except Exception as e:
            logger.error(f'Block AI error: {e}')
            return {
                'success': False,
                'error': str(e),
                'mode': mode
            }
    
    @staticmethod
    def _build_full_prompt(content: str, mode_prompt: str, block_type: str, context: Optional[Dict]) -> str:
        """Build full prompt with context."""
        parts = [mode_prompt]
        
        if context:
            if context.get('title'):
                parts.append(f"\nBlock Title: {context['title']}")
            if context.get('tags'):
                parts.append(f"Tags: {', '.join(context['tags'])}")
        
        parts.append(f"\n{block_type.upper()} CONTENT:\n{content}")
        
        if block_type == 'table':
            parts.append("\n\nProvide output in a clear, structured format.")
        else:
            parts.append("\n\nKeep the tone consistent with the original content.")
        
        return "\n".join(parts)
    
    @staticmethod
    async def stream_ai_response(
        user_id: str,
        block_id: str,
        content: str,
        mode: str,
        custom_prompt: Optional[str] = None
    ):
        """
        Stream AI response for real-time feedback.
        Yields chunks of the response.
        """
        try:
            if mode == 'custom':
                prompt_text = custom_prompt or ''
            else:
                prompt_text = BlockAIEngine.MODES.get(mode, {}).get('prompt', '')
            
            full_prompt = BlockAIEngine._build_full_prompt(content, prompt_text, 'text', None)
            
            # This would stream from the AI API if available
            # For now, return full response
            if call_ai:
                response = await call_ai(full_prompt)
                yield response
            else:
                yield "[AI unavailable]"
        
        except Exception as e:
            logger.error(f'Stream error: {e}')
            yield f"Error: {str(e)}"


class TableAIEngine:
    """AI engine specifically for table operations"""
    
    @staticmethod
    async def analyze_table(user_id: str, table_data: List[List], headers: List[str]) -> Dict:
        """Analyze table and extract insights."""
        try:
            csv_format = TableAIEngine._to_csv(table_data, headers)
            prompt = f"""Analyze this data table and provide:
1. Key patterns or trends
2. Anomalies or outliers
3. Summary statistics
4. Recommendations

TABLE:
{csv_format}"""
            
            if call_ai:
                response = await call_ai(prompt)
            else:
                response = "[Analysis unavailable]"
            
            return {
                'success': True,
                'analysis': response,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f'Table analysis error: {e}')
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _to_csv(table_data: List[List], headers: List[str]) -> str:
        """Convert table to CSV format."""
        lines = [','.join(headers)]
        for row in table_data:
            lines.append(','.join(str(cell) for cell in row))
        return '\n'.join(lines)


class NotificationEngine:
    """Handle notifications, due dates, and reminders"""
    
    NOTIFICATION_TYPES = ['due_date', 'mention', 'completion', 'shared', 'comment', 'reminder']
    
    @staticmethod
    def create_notification(
        user_id: str,
        block_id: str,
        notification_type: str,
        message: str,
        due_date: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a notification."""
        try:
            from memory import get_db
            db = get_db()
            
            notification = {
                'user_id': user_id,
                'block_id': block_id,
                'type': notification_type,
                'message': message,
                'due_date': due_date,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat(),
                'read': False
            }
            
            # Store in DB (implement in memory.py)
            # For now, return the structure
            logger.info(f'Notification created: {notification}')
            return {'success': True, 'notification': notification}
        
        except Exception as e:
            logger.error(f'Notification error: {e}')
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def check_due_dates(user_id: str) -> List[Dict]:
        """Get upcoming due dates for user."""
        try:
            from memory import get_db
            db = get_db()
            
            # Query blocks with due dates
            # Return sorted by due date
            return []
        except Exception as e:
            logger.error(f'Due date check error: {e}')
            return []


# Export classes for API use
__all__ = ['BlockAIEngine', 'TableAIEngine', 'NotificationEngine']
