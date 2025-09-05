"""
Performance monitoring and analytics module.

This module provides:
- Performance metrics collection
- Error tracking and logging
- Usage analytics
- System health monitoring
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import psutil
import asyncio

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    user_agent: Optional[str] = None
    api_key_hash: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SystemHealth:
    """System health metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    response_time_avg: float
    error_rate: float


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.error_count = defaultdict(int)
        self.endpoint_stats = defaultdict(list)
        self.start_time = datetime.now()
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        user_agent: Optional[str] = None,
        api_key_hash: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Record a request metric."""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            user_agent=user_agent,
            api_key_hash=api_key_hash,
            error_message=error_message
        )
        
        self.metrics.append(metric)
        self.endpoint_stats[endpoint].append(response_time)
        
        # Track errors
        if status_code >= 400:
            self.error_count[f"{status_code}_{endpoint}"] += 1
        
        # Log performance issues
        if response_time > 5.0:  # Slow response
            logger.warning(f"Slow response: {endpoint} took {response_time:.2f}s")
        
        if status_code >= 500:  # Server error
            logger.error(f"Server error: {endpoint} returned {status_code}: {error_message}")
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health metrics."""
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate average response time (last 100 requests)
        recent_metrics = list(self.metrics)[-100:]
        if recent_metrics:
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            error_rate = sum(1 for m in recent_metrics if m.status_code >= 400) / len(recent_metrics)
        else:
            avg_response_time = 0.0
            error_rate = 0.0
        
        return SystemHealth(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            active_connections=len(recent_metrics),
            response_time_avg=avg_response_time,
            error_rate=error_rate
        )
    
    def get_endpoint_stats(self, endpoint: str, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for a specific endpoint."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        endpoint_metrics = [
            m for m in self.metrics 
            if m.endpoint == endpoint and m.timestamp > cutoff_time
        ]
        
        if not endpoint_metrics:
            return {"error": "No data found for endpoint"}
        
        response_times = [m.response_time for m in endpoint_metrics]
        status_codes = [m.status_code for m in endpoint_metrics]
        
        return {
            "endpoint": endpoint,
            "total_requests": len(endpoint_metrics),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "error_rate": sum(1 for code in status_codes if code >= 400) / len(status_codes),
            "status_code_distribution": dict(defaultdict(int, 
                {str(code): status_codes.count(code) for code in set(status_codes)}
            ))
        }
    
    def get_usage_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage analytics for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"error": "No data found for time period"}
        
        # Endpoint usage
        endpoint_usage = defaultdict(int)
        for metric in recent_metrics:
            endpoint_usage[metric.endpoint] += 1
        
        # Hourly distribution
        hourly_usage = defaultdict(int)
        for metric in recent_metrics:
            hour = metric.timestamp.hour
            hourly_usage[hour] += 1
        
        # Top errors
        error_metrics = [m for m in recent_metrics if m.status_code >= 400]
        error_summary = defaultdict(int)
        for error in error_metrics:
            key = f"{error.status_code}_{error.endpoint}"
            error_summary[key] += 1
        
        return {
            "time_period_hours": hours,
            "total_requests": len(recent_metrics),
            "unique_endpoints": len(endpoint_usage),
            "endpoint_usage": dict(endpoint_usage),
            "hourly_distribution": dict(hourly_usage),
            "error_summary": dict(error_summary),
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }


class ErrorTracker:
    """Error tracking and alerting system."""
    
    def __init__(self):
        self.errors: deque = deque(maxlen=1000)  # Keep last 1000 errors
        self.error_patterns = defaultdict(int)
    
    def track_error(
        self,
        error_type: str,
        error_message: str,
        endpoint: str,
        user_context: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ):
        """Track an error occurrence."""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "endpoint": endpoint,
            "user_context": user_context or {},
            "stack_trace": stack_trace
        }
        
        self.errors.append(error_data)
        self.error_patterns[error_type] += 1
        
        # Log error
        logger.error(f"Error tracked: {error_type} in {endpoint}: {error_message}")
        
        # Alert on critical errors
        if error_type in ["database_connection", "llm_service_down", "auth_failure"]:
            self._send_alert(error_data)
    
    def _send_alert(self, error_data: Dict[str, Any]):
        """Send alert for critical errors (placeholder for production alerting)."""
        # In production, this would send to Slack, email, or monitoring service
        logger.critical(f"CRITICAL ERROR ALERT: {error_data}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.errors 
            if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]
        
        error_types = defaultdict(int)
        endpoints = defaultdict(int)
        
        for error in recent_errors:
            error_types[error["error_type"]] += 1
            endpoints[error["endpoint"]] += 1
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_errors),
            "error_types": dict(error_types),
            "affected_endpoints": dict(endpoints),
            "recent_errors": recent_errors[-10:]  # Last 10 errors
        }


# Global instances
performance_monitor = PerformanceMonitor()
error_tracker = ErrorTracker()


class MonitoringMiddleware:
    """Middleware for automatic performance monitoring."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Extract request info
        method = scope["method"]
        path = scope["path"]
        
        # Process request
        try:
            await self.app(scope, receive, send)
            status_code = 200  # Default success
        except Exception as e:
            status_code = 500
            error_tracker.track_error(
                error_type="middleware_error",
                error_message=str(e),
                endpoint=path,
                stack_trace=str(e)
            )
            raise
        finally:
            # Record metrics
            response_time = time.time() - start_time
            performance_monitor.record_request(
                endpoint=path,
                method=method,
                response_time=response_time,
                status_code=status_code
            )


# Utility functions for other modules
def track_llm_performance(response_time: float, token_count: int, model: str):
    """Track LLM service performance."""
    logger.info(f"LLM Performance: {response_time:.2f}s, {token_count} tokens, model: {model}")
    
    # Track expensive requests
    if response_time > 10.0 or token_count > 2000:
        logger.warning(f"Expensive LLM request: {response_time:.2f}s, {token_count} tokens")


def track_database_performance(query_type: str, response_time: float, row_count: int):
    """Track database query performance."""
    logger.debug(f"DB Performance: {query_type} took {response_time:.2f}s, returned {row_count} rows")
    
    # Track slow queries
    if response_time > 2.0:
        logger.warning(f"Slow database query: {query_type} took {response_time:.2f}s")


async def health_check_background_task():
    """Background task for periodic health checks."""
    while True:
        try:
            health = performance_monitor.get_system_health()
            
            # Log health metrics
            logger.info(f"System Health: CPU={health.cpu_percent}%, "
                       f"Memory={health.memory_percent}%, "
                       f"Avg Response={health.response_time_avg:.2f}s, "
                       f"Error Rate={health.error_rate:.2%}")
            
            # Alert on high resource usage
            if health.cpu_percent > 80 or health.memory_percent > 85:
                error_tracker.track_error(
                    error_type="high_resource_usage",
                    error_message=f"CPU: {health.cpu_percent}%, Memory: {health.memory_percent}%",
                    endpoint="system_health"
                )
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await asyncio.sleep(60)  # Retry in 1 minute
