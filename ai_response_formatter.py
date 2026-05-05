"""
AI Response Formatter
Enhances AI chat responses with bullet points, emojis, and better formatting
"""
import re

def format_ai_response(text: str) -> str:
    """
    Enhance AI response with:
    - Bullet points for list-like content
    - Relevant emojis
    - Better formatting and readability
    """
    
    # If text is too short, return as-is
    if not text or len(text.strip()) < 10:
        return text
    
    # Split into sentences/lines for processing
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Check if line should be a bullet point (numbered or unnumbered list)
        # Pattern: "1. Item", "- Item", "• Item", or lines that look like list items
        if re.match(r'^[\d]+[\.\)]\s+', line):
            # Already numbered, ensure proper format
            formatted_lines.append(f"• {line}")
        elif re.match(r'^[-–•]\s+', line):
            # Already has bullet, keep it
            formatted_lines.append(f"• {line.lstrip('-–•').strip()}")
        elif re.match(r'^(and|or|then|because|so|also)\s+', line, re.IGNORECASE):
            # Conjunction at start - likely part of previous point, don't bullet
            formatted_lines.append(line)
        elif re.match(r'(step|next|tip|advice|strategy|approach)[\s:]', line, re.IGNORECASE):
            # Looks like a step/strategy line
            formatted_lines.append(f"→ {line}")
        else:
            # Regular line
            formatted_lines.append(line)
    
    # Rejoin
    text = '\n'.join(formatted_lines)
    
    # Add emojis strategically (if not already present)
    emoji_replacements = [
        (r'\b(success|great|good|excellent|perfect|awesome|amazing)\b', r'\1 ✨', re.IGNORECASE),
        (r'\b(important|critical|key|must)\b', r'⚡ \1', re.IGNORECASE),
        (r'\b(warning|watch out|be careful|avoid)\b', r'⚠️ \1', re.IGNORECASE),
        (r'\b(question|ask|wondering)\b', r'❓ \1', re.IGNORECASE),
        (r'\b(step|next|then|start|begin)\b', r'→ \1', re.IGNORECASE),
        (r'\b(finish|complete|done|accomplished)\b', r'✓ \1', re.IGNORECASE),
        (r'\b(tip|trick|hack|insight)\b', r'💡 \1', re.IGNORECASE),
        (r'\b(goal|target|aim|vision)\b', r'🎯 \1', re.IGNORECASE),
        (r'\b(challenge|difficult|hard|struggle)\b', r'💪 \1', re.IGNORECASE),
        (r'\b(habit|routine|daily|practice)\b', r'🔄 \1', re.IGNORECASE),
        (r'\b(motivation|motivate|inspire|empower)\b', r'🚀 \1', re.IGNORECASE),
        (r'\b(time|schedule|deadline|soon)\b', r'⏰ \1', re.IGNORECASE),
    ]
    
    for pattern, replacement, flags in emoji_replacements:
        # Only replace if emoji not already nearby (prevent double emoji)
        text = re.sub(
            f'(?<![✨⚡⚠️❓→✓💡🎯💪🔄🚀⏰])\b{pattern[2:-2]}(?![✨⚡⚠️❓→✓💡🎯💪🔄🚀⏰])',
            replacement,
            text,
            flags=flags
        )
    
    # Ensure OPTIONS formatting is preserved (for interactive buttons)
    if '[OPTIONS:' in text:
        # Don't modify the OPTIONS line
        pass
    
    return text


def extract_options(text: str) -> tuple:
    """
    Extract options from text
    Returns: (text_without_options, options_list)
    
    Example:
        "Should I start now? [OPTIONS: Yes | No | Maybe]"
        -> ("Should I start now?", ["Yes", "No", "Maybe"])
    """
    match = re.search(r'\[OPTIONS:\s*([^\]]+)\]', text)
    if match:
        options_str = match.group(1)
        options = [opt.strip() for opt in options_str.split('|')]
        text_clean = text[:match.start()].rstrip() + '\n' + text[match.end():].lstrip()
        return text_clean, options
    return text, []


def add_emoji_to_greeting(response: str, is_first_response: bool = False) -> str:
    """Add greeting emoji if it's a first or welcoming response."""
    if is_first_response and not response.startswith(('👋', '🙌', '😊', '✨')):
        response = f"👋 {response}"
    return response


def format_list_items(items: list, style: str = 'bullet') -> str:
    """
    Format a list of items with style
    
    Args:
        items: List of strings
        style: 'bullet', 'number', 'arrow'
    """
    if style == 'number':
        return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(items))
    elif style == 'arrow':
        return '\n'.join(f"→ {item}" for item in items)
    else:  # bullet (default)
        return '\n'.join(f"• {item}" for item in items)


def format_habit_message(habit_count: int, completed: int) -> str:
    """Format a habit completion message with emojis."""
    emoji = '🔥' if completed == habit_count else ('✓' if completed > 0 else '⭕')
    percentage = int((completed / habit_count * 100)) if habit_count > 0 else 0
    return f"{emoji} {completed}/{habit_count} habits completed ({percentage}%)"


def format_task_message(task_count: int, completed: int) -> str:
    """Format a task completion message with emojis."""
    emoji = '🎉' if completed == task_count else ('✓' if completed > 0 else '📋')
    percentage = int((completed / task_count * 100)) if task_count > 0 else 0
    return f"{emoji} {completed}/{task_count} tasks completed ({percentage}%)"


def format_motivation(streak: int) -> str:
    """Generate motivational text with emojis based on streak."""
    if streak >= 30:
        return f"🔥🔥🔥 {streak}-day streak! You're unstoppable!"
    elif streak >= 14:
        return f"🔥 {streak}-day streak! Keep it rolling!"
    elif streak >= 7:
        return f"✨ {streak}-day streak! Great momentum!"
    elif streak >= 3:
        return f"💪 {streak}-day streak! You're on your way!"
    else:
        return "🌱 Start your streak today!"
