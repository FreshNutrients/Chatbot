"""
Pydantic models for request and response validation.

This module defines all the data models used for API requests and responses,
ensuring type safety and automatic validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    llm_configured: bool = Field(..., description="LLM service configuration status")
    circuit_breaker_open: bool = Field(default=False, description="Azure OpenAI circuit breaker status")
    last_azure_failure: Optional[datetime] = Field(default=None, description="Last Azure OpenAI failure timestamp")