"""
Utility helper functions for the FreshNutrients AI Chat API.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime


def generate_conversation_id() -> str:
    """
    Generate a unique conversation ID.
    
    Returns:
        UUID string for conversation tracking
    """
    return str(uuid.uuid4())


def validate_conversation_id(conversation_id: str) -> bool:
    """
    Validate conversation ID format.
    
    Args:
        conversation_id: Conversation ID to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    try:
        uuid.UUID(conversation_id)
        return True
    except ValueError:
        return False


def format_response_metadata(
    model_used: str,
    response_time: float,
    category: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Format response metadata for API responses.
    
    Args:
        model_used: LLM model used for response
        response_time: Response generation time in seconds
        category: Response category (optional)
        **kwargs: Additional metadata fields
        
    Returns:
        Formatted metadata dictionary
    """
    metadata = {
        "model_used": model_used,
        "response_time": round(response_time, 2),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if category:
        metadata["category"] = category
    
    metadata.update(kwargs)
    return metadata


def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input text.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    # Basic sanitization - can be expanded
    return text.strip()[:1000]  # Limit length and trim whitespace
