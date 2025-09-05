"""
Admin and monitoring endpoints for FreshNutrients AI Chat API.

This module provides:
- System health monitoring
- Performance metrics
- Usage analytics
- Error tracking
- Administrative functions
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ..core.security import verify_api_key
from ..utils.monitoring import performance_monitor, error_tracker
from ..config import settings

logger = logging.getLogger(__name__)

# Create admin router
router = APIRouter(prefix="/admin", tags=["monitoring"])


@router.get("/health", response_model=Dict[str, Any])
async def system_health(
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
):
    """
    Get comprehensive system health metrics.
    
    Requires API authentication.
    """
    try:
        health = performance_monitor.get_system_health()
        
        return {
            "status": "healthy" if health.cpu_percent < 80 and health.memory_percent < 85 else "warning",
            "timestamp": health.timestamp.isoformat(),
            "metrics": {
                "cpu_percent": health.cpu_percent,
                "memory_percent": health.memory_percent,
                "disk_percent": health.disk_percent,
                "active_connections": health.active_connections,
                "average_response_time": health.response_time_avg,
                "error_rate": health.error_rate
            },
            "uptime_hours": (datetime.now() - performance_monitor.start_time).total_seconds() / 3600
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/metrics/{endpoint}")
async def endpoint_metrics(
    endpoint: str,
    hours: int = 24,
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
):
    """
    Get performance metrics for a specific endpoint.
    
    Args:
        endpoint: The endpoint path to analyze
        hours: Time window in hours (default: 24)
    """
    try:
        stats = performance_monitor.get_endpoint_stats(endpoint, hours)
        return {
            "endpoint": endpoint,
            "time_window_hours": hours,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get metrics for {endpoint}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve endpoint metrics"
        )


@router.get("/analytics")
async def usage_analytics(
    hours: int = 24,
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
):
    """
    Get usage analytics and patterns.
    
    Args:
        hours: Time window in hours (default: 24)
    """
    try:
        analytics = performance_monitor.get_usage_analytics(hours)
        return {
            "analytics": analytics,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage analytics"
        )


@router.get("/errors")
async def error_summary(
    hours: int = 24,
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
):
    """
    Get error summary and tracking information.
    
    Args:
        hours: Time window in hours (default: 24)
    """
    try:
        errors = error_tracker.get_error_summary(hours)
        return {
            "error_summary": errors,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error summary"
        )


@router.get("/config")
async def system_config(
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
):
    """
    Get current system configuration (safe subset).
    
    Returns non-sensitive configuration for debugging.
    """
    try:
        config = {
            "environment": settings.ENVIRONMENT,
            "api_version": settings.API_VERSION,
            "rate_limiting": {
                "enabled": settings.ENABLE_RATE_LIMITING,
                "requests_per_hour": settings.RATE_LIMIT_REQUESTS if hasattr(settings, 'RATE_LIMIT_REQUESTS') else "default",
                "window_seconds": settings.RATE_LIMIT_WINDOW if hasattr(settings, 'RATE_LIMIT_WINDOW') else "default"
            },
            "security": {
                "api_auth_enabled": settings.ENABLE_API_AUTH,
                "https_redirect": settings.ENABLE_HTTPS_REDIRECT if hasattr(settings, 'ENABLE_HTTPS_REDIRECT') else False
            },
            "validation": {
                "max_message_length": settings.MAX_MESSAGE_LENGTH if hasattr(settings, 'MAX_MESSAGE_LENGTH') else "default",
                "max_json_size_kb": settings.MAX_JSON_SIZE_KB if hasattr(settings, 'MAX_JSON_SIZE_KB') else "default"
            },
            "database_configured": settings.is_azure_sql_configured,
            "llm_configured": settings.is_azure_openai_configured
        }
        
        return {
            "configuration": config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system configuration"
        )


@router.post("/clear-metrics")
async def clear_metrics(
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
):
    """
    Clear performance metrics (admin function).
    
    Use with caution - this will reset all collected metrics.
    """
    try:
        performance_monitor.metrics.clear()
        performance_monitor.error_count.clear()
        performance_monitor.endpoint_stats.clear()
        
        logger.info("Performance metrics cleared by admin")
        
        return {
            "status": "success",
            "message": "Performance metrics cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear metrics"
        )
