"""
Server startup script for the FreshNutrients AI Chat API.

Run this script to start the development server:
    python server.py

For production deployment, use:
    gunicorn app.main:app -k uvicorn.workers.UvicornWorker
"""

import uvicorn
from app.config import settings
from app.utils.logging import setup_logging

if __name__ == "__main__":
    # Set up logging
    setup_logging()
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
