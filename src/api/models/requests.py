"""Request models for the API."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractionConfig(BaseModel):
    """Configuration for extraction processing."""
    debug: bool = Field(default=False, description="Generate debug images")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    # Add other configuration options as needed from the CLI
    

class ExtractionRequest(BaseModel):
    """Request model for extraction (for documentation purposes)."""
    # Note: FastAPI handles multipart form data separately
    # This is mainly for OpenAPI documentation
    config: Optional[ExtractionConfig] = None
