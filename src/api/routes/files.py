"""File serving and session management endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse

from ..models.responses import SessionInfo, CleanupResponse
from ..models.config import APIConfig
from ..services.extraction import ExtractionService
from ..services.file_manager import FileManager


router = APIRouter(prefix="/api/v1")


def get_config() -> APIConfig:
    """Get API configuration."""
    return APIConfig.from_env()


def get_extraction_service(config: APIConfig = Depends(get_config)) -> ExtractionService:
    """Get extraction service instance."""
    return ExtractionService(config)


def get_file_manager(config: APIConfig = Depends(get_config)) -> FileManager:
    """Get file manager instance."""
    return FileManager(config)


@router.get("/files/{session_id}/{filename}")
async def download_file(
    session_id: str,
    filename: str,
    keep: bool = Query(False, description="Keep file after download instead of auto-deleting"),
    file_manager: FileManager = Depends(get_file_manager)
):
    """
    Download a file from a session.
    
    By default, files are automatically deleted after successful download.
    Use ?keep=true to preserve files for multiple downloads.
    """
    
    file_path = file_manager.get_file_path(session_id, filename)
    
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "FILE_NOT_FOUND",
                "message": "File not found",
                "details": f"Session {session_id} or file {filename} does not exist"
            }
        )
    
    # Determine media type based on file extension
    media_type = "application/octet-stream"
    if filename.lower().endswith('.png'):
        media_type = "image/png"
    elif filename.lower().endswith('.json'):
        media_type = "application/json"
    
    # Create response with auto-delete behavior
    response = FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )
    
    # Add header to indicate auto-delete behavior
    if not keep:
        response.headers["X-Auto-Deleted"] = "true"
        # Note: We'll delete the file after the response is sent
        # This is handled by a background task in the main app
    
    return response


@router.delete("/files/{session_id}", response_model=CleanupResponse)
async def cleanup_session(
    session_id: str,
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    Clean up all files in a session.
    
    This removes all files associated with the session and frees up storage space.
    """
    
    result = extraction_service.cleanup_session(session_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found",
                "details": result.get("error", "Unknown error")
            }
        )
    
    return CleanupResponse(**result)


@router.get("/sessions/{session_id}/info", response_model=SessionInfo)
async def get_session_info(
    session_id: str,
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    Get information about a session.
    
    Returns metadata about the session including file count, total size, and expiration.
    """
    
    session_info = extraction_service.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found",
                "details": f"Session {session_id} does not exist or has expired"
            }
        )
    
    # Convert timestamps to datetime objects for Pydantic
    from datetime import datetime
    session_info["created_at"] = datetime.fromtimestamp(session_info["created_at"])
    session_info["expires_at"] = datetime.fromtimestamp(session_info["expires_at"])
    
    return SessionInfo(**session_info)
