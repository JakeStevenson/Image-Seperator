"""Configuration models for the API."""

from typing import Optional
from pydantic import BaseModel, Field
import os


class APIConfig(BaseModel):
    """API configuration settings."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    
    # File management
    temp_dir: str = Field(default="/tmp/diagram_api", description="Temporary file directory")
    session_ttl_hours: int = Field(default=1, description="Session TTL in hours")
    max_concurrent_sessions: int = Field(default=100, description="Maximum concurrent sessions")
    max_session_size_mb: int = Field(default=500, description="Maximum session size in MB")
    
    # Processing limits
    max_file_size_mb: int = Field(default=50, description="Maximum upload file size in MB")
    processing_timeout_seconds: int = Field(default=300, description="Processing timeout in seconds")
    
    
    # Security
    cors_origins: list = Field(default=["*"], description="CORS allowed origins")
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            temp_dir=os.getenv("TEMP_DIR", "/tmp/diagram_api"),
            session_ttl_hours=int(os.getenv("SESSION_TTL_HOURS", "1")),
            max_concurrent_sessions=int(os.getenv("MAX_CONCURRENT_SESSIONS", "100")),
            max_session_size_mb=int(os.getenv("MAX_SESSION_SIZE_MB", "500")),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
            processing_timeout_seconds=int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "300")),
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        )
