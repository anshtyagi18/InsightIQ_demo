"""
Application configuration module for InsightIQ.
Handles environment variables and application settings with simplified local architecture.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # App Information
    APP_NAME: str = os.getenv("APP_NAME", "InsightIQ")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # Database configuration (SQLite default)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./insightiq.db")
    
    # AI configuration (Gemini API)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # Local Storage configuration
    STORAGE_TYPE: str = "local"
    STORAGE_BASE_PATH: str = os.getenv("STORAGE_BASE_PATH", "uploads")
    
    # File upload limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    ALLOWED_FILE_EXTENSIONS: str = os.getenv("ALLOWED_FILE_EXTENSIONS", ".csv,.xlsx,.xls,.json")
    
    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # CORS settings
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def allowed_extensions_set(self) -> set:
        """Get allowed extensions as a set."""
        return {ext.strip() for ext in self.ALLOWED_FILE_EXTENSIONS.split(",")}
    
    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    def get_storage_config(self) -> dict:
        """Get storage configuration dictionary."""
        return {
            "storage_type": "local",
            "base_path": self.STORAGE_BASE_PATH
        }

# Global settings instance
settings = Settings()

# Content type mappings for supported file extensions
CONTENT_TYPE_MAPPING = {
    '.csv': 'text/csv',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.json': 'application/json'
}

def get_content_types() -> set:
    """Get allowed content types based on configured extensions."""
    return {CONTENT_TYPE_MAPPING.get(ext) for ext in settings.allowed_extensions_set 
            if ext in CONTENT_TYPE_MAPPING}
