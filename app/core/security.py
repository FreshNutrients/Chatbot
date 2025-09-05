"""
Security and authentication module for FreshNutrients AI Chat API.

This module handles:
- API key authentication
- Request validation
- Rate limiting
- Security headers
- Request sanitization
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import hashlib
import json
from typing import Dict, Optional
from collections import defaultdict, deque
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600   # 1 hour in seconds

# Valid API keys (in production, store in Azure Key Vault)
VALID_API_KEYS = {
    settings.API_SECRET_KEY,  # Primary key
    "fn-chat-api-key-2025",   # Secondary key for rotation
}


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for HTTPS enforcement and security headers."""
    
    async def dispatch(self, request: Request, call_next):
        # HTTPS enforcement (in production)
        if settings.ENVIRONMENT == "production" and request.url.scheme != "https":
            return Response(
                content="HTTPS required", 
                status_code=426,
                headers={"Upgrade": "TLS/1.2"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent API abuse."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        api_key = self._extract_api_key(request)
        client_id = f"{client_ip}:{api_key}" if api_key else client_ip
        
        # Check rate limit
        current_time = time.time()
        client_requests = rate_limit_storage[client_id]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] < current_time - RATE_LIMIT_WINDOW:
            client_requests.popleft()
        
        # Check if limit exceeded
        if len(client_requests) >= RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {RATE_LIMIT_REQUESTS} requests per hour allowed",
                    "retry_after": RATE_LIMIT_WINDOW
                }),
                status_code=429,
                headers={"Content-Type": "application/json"}
            )
        
        # Add current request
        client_requests.append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, RATE_LIMIT_REQUESTS - len(client_requests))
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + RATE_LIMIT_WINDOW))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers (from load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify API key authentication.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: Validated API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    api_key = credentials.credentials
    
    if not api_key or api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}..." if api_key else "No API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Valid API key authenticated: {api_key[:10]}...")
    return api_key


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
        
    Raises:
        HTTPException: If input is invalid
    """
    if not text or not isinstance(text, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input: text must be a non-empty string"
        )
    
    # Length validation
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input too long: maximum {max_length} characters allowed"
        )
    
    # Remove potentially dangerous characters
    dangerous_patterns = [
        "<script", "</script>", "javascript:", "data:",
        "vbscript:", "onload=", "onerror=", "onclick="
    ]
    
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input: potentially dangerous content detected"
            )
    
    # Basic sanitization
    sanitized = text.strip()
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    return sanitized


def hash_api_key(api_key: str) -> str:
    """
    Create a hash of API key for logging (privacy protection).
    
    Args:
        api_key: API key to hash
        
    Returns:
        str: Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()[:12]


class RequestValidator:
    """Request validation utilities."""
    
    @staticmethod
    def validate_conversation_id(conversation_id: str) -> bool:
        """Validate conversation ID format."""
        if not conversation_id:
            return False
        
        # Allow UUID format or alphanumeric with hyphens
        import re
        pattern = r'^[a-zA-Z0-9\-_]{1,50}$'
        return bool(re.match(pattern, conversation_id))
    
    @staticmethod
    def validate_json_size(json_data: dict, max_size_kb: int = 50) -> bool:
        """Validate JSON payload size."""
        json_str = json.dumps(json_data)
        size_kb = len(json_str.encode('utf-8')) / 1024
        return size_kb <= max_size_kb


# Security utilities for other modules
def get_secure_headers() -> Dict[str, str]:
    """Get security headers for responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache"
    }
