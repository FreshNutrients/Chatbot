"""
Configuration module for the FreshNutrients AI Chat API.

This module handles all environment variables and application settings
using Pydantic's BaseSettings for validation and type safety.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "FreshNutrients AI Chat API"
    API_VERSION: str = "1.0.0"
    
    # Azure SQL Database Configuration
    AZURE_SQL_SERVER: str = ""
    AZURE_SQL_DATABASE: str = ""
    AZURE_SQL_USERNAME: str = ""
    AZURE_SQL_PASSWORD: str = ""
    
    # Azure SQL Private Endpoint (Production)
    AZURE_SQL_PRIVATE_ENDPOINT: str = ""  # e.g., "myserver-private.database.windows.net"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_MODEL: str = "gpt-35-turbo"
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"  # Allow all origins for local testing
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security
    API_SECRET_KEY: str = "your-secret-key-here"
    ENABLE_API_AUTH: bool = False  # Temporarily disabled for testing
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_HTTPS_REDIRECT: bool = False  # Set to True in production
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per hour
    RATE_LIMIT_WINDOW: int = 3600   # window in seconds
    
    # Request Validation
    MAX_MESSAGE_LENGTH: int = 1000
    MAX_JSON_SIZE_KB: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def is_azure_sql_configured(self) -> bool:
        """Check if Azure SQL configuration is available."""
        return all([
            self.AZURE_SQL_SERVER,
            self.AZURE_SQL_DATABASE,
            self.AZURE_SQL_USERNAME,
            self.AZURE_SQL_PASSWORD
        ])
    
    @property
    def is_azure_openai_configured(self) -> bool:
        """Check if Azure OpenAI configuration is available."""
        return all([
            self.AZURE_OPENAI_ENDPOINT,
            self.AZURE_OPENAI_KEY,
            self.AZURE_OPENAI_MODEL
        ])


# Create global settings instance
settings = Settings()
