"""
Logging configuration utilities.

This module provides centralized logging configuration
for the FreshNutrients AI Chat API.
"""

import logging
import sys
from typing import Optional
from ..config import settings


def setup_logging(level: Optional[str] = None) -> None:
    """
    Set up application logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = level or settings.LOG_LEVEL
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
