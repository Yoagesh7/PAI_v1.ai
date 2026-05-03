"""
Smart Blocks Core Logic
Handles block validation, AI suggestions, and relationship algorithms
"""
import json
from datetime import datetime
from smart_blocks_db import (
    create_smart_block, get_user_blocks, update_smart_block,
    delete_smart_block, link_blocks, get_block_relationships, search_blocks
)


# Valid block types
BLOCK_TYPES = {
    'idea': {
        'name': 'Idea Block',
        'icon': '💡',
        'description': 'Startup ideas, content ideas, brainstorming',
        'template': {'tags': [], 'priority': 'medium'}
    },
    'task': {
        'name': 'Task Block',
        'icon': '✅',
        'description': 'Daily/weekly tasks, actionable items',
        'template': {'due_date': None, 'priority': 'medium', 'estimated_time': None}
    },
    'learning': {
        'name': 'Learning Block',
        'icon': '📘',
        'description': 'What you learned today, insights',
        'template': {'source': None, 'key_points': []}
    },
    'habit': {
        'name': 'Habit Block',
        'icon': '🔁',
        'description': 'Habits and streaks tracking',
        'template': {'frequency': 'daily', 'target_time': None, 'current_streak': 0}
    },
    'reflection': {
        'name': 'Reflection Block',
        'icon': '📊',
        'description': 'Weekly self-review, progress analysis',
        'template': {'week': None, 'wins': [], 'improvements': []}
    }
}

# Valid relationship types
RELATIONSHIP_TYPES = ['related', 'depends_on', 'part_of', 'leads_to', 'inspired_by']


def validate_block_type(block_type):
    """Validate block type."""
    return block_type in BLOCK_TYPES


def get_block_template(block_type):
    """Get default template/metadata for a block type."""
    if block_type in BLOCK_TYPES:
        return BLOCK_TYPES[block_type]['template'].copy()
    return {}


def create_block(user_id, block_type, title, content, metadata=None):
    """
    Create a new smart block with validation.
    
    Args:
        user_id: User ID
        block_type: One of BLOCK_TYPES
        title: Block title
        content: Block content
        metadata: Optional dict with block-specific data
    
    Returns:
        block_id on success, None on failure
    """
    if not validate_block_type(block_type):
        return None
    
    # Merge with template
    template = get_block_template(block_type)
    if metadata:
        template.update(metadata)
    
    return create_smart_block(user_id, block_type, title, content, template)


def suggest_related_blocks(user_id, block_content, block_type, limit=5):
    """
    Use simple keyword matching to suggest related blocks.
    In production, this could use embeddings/AI.
    
    Returns:
        List of suggested block IDs
    """
    # Extract keywords (simple approach - split and take important words)
    words = block_content.lower().split()
    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
    keywords = [w.strip('.,!?;:') for w in words if len(w) > 3 and w not in stop_words][:5]
    
    # Search for blocks with these keywords
    related = []
    for keyword in keywords:
        results = search_blocks(user_id, keyword)
        related.extend(results)
    
    # Deduplicate and limit
    seen = set()
    unique_related = []
    for block in related:
        if block['id'] not in seen:
            seen.add(block['id'])
            unique_related.append(block)
        if len(unique_related) >= limit:
            break
    
    return unique_related


def get_block_with_context(block_id):
    """
    Get a block along with its relationships and metadata.
    
    Returns:
        {
            'block': block_data,
            'relationships': [related_blocks],
            'suggested': [suggested_blocks]
        }
    """
    # This is a placeholder - would need to enhance with actual data fetching
    relationships = get_block_relationships(block_id)
    
    return {
        'relationships': relationships,
        'relationship_count': len(relationships)
    }


def auto_link_blocks(user_id, new_block_id, new_block_content, new_block_type):
    """
    Automatically suggest and create relationships when a new block is created.
    Uses keyword matching + AI suggestions.
    """
    suggested = suggest_related_blocks(user_id, new_block_content, new_block_type, limit=3)
    
    # For now, return suggestions without auto-linking
    # In production, could use confidence scoring
    return suggested


def analyze_block_network(user_id):
    """
    Analyze the user's block network to find patterns.
    
    Returns:
        {
            'total_blocks': int,
            'blocks_by_type': dict,
            'most_connected': block_id,
            'isolated_blocks': [block_ids],
            'recent_activity': [blocks]
        }
    """
    all_blocks = get_user_blocks(user_id, limit=1000)
    
    # Count by type
    blocks_by_type = {}
    for block in all_blocks:
        btype = block['type']
        blocks_by_type[btype] = blocks_by_type.get(btype, 0) + 1
    
    # Get recent (last 7 days)
    from datetime import datetime, timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent = [b for b in all_blocks if b['created_at'] >= week_ago]
    
    return {
        'total_blocks': len(all_blocks),
        'blocks_by_type': blocks_by_type,
        'recent_activity': recent[:10],
        'recent_count': len(recent)
    }
