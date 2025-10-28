"""Response models for the API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


class DiagramInfo(BaseModel):
    """Information about an extracted diagram."""
    id: int
    filename: str
    bbox: List[int]  # [x, y, w, h]
    confidence: float
    url: str


class DebugImageInfo(BaseModel):
    """Information about a debug image."""
    name: str
    url: str


class ProcessingManifest(BaseModel):
    """Processing manifest information."""
    original_file: str
    diagrams: List[Dict[str, Any]]
    processing_info: Dict[str, Any]


class ExtractionResponse(BaseModel):
    """Response from the extraction endpoint."""
    success: bool
    processing_time: float
    session_id: str
    manifest: ProcessingManifest
    diagrams: List[DiagramInfo]
    debug_images: Optional[List[DebugImageInfo]] = None


class AsyncJobResponse(BaseModel):
    """Response from async job submission."""
    job_id: str
    status: str
    estimated_time: float


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress: float
    result: Optional[ExtractionResponse] = None
    error: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information response."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    file_count: int
    total_size_bytes: int
    files: List[str]


class CleanupResponse(BaseModel):
    """File cleanup response."""
    success: bool
    files_deleted: int
    bytes_freed: int


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: Dict[str, Any]
    timestamp: datetime
