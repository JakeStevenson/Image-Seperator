"""Extraction endpoints for processing images."""

import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models.responses import ExtractionResponse, ErrorResponse
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


@router.post("/extract", response_model=ExtractionResponse)
async def extract_diagrams(
    file: UploadFile = File(..., description="PNG image file to process"),
    debug: bool = Form(False, description="Generate debug images"),
    config: Optional[str] = Form(None, description="JSON configuration (optional)"),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    file_manager: FileManager = Depends(get_file_manager)
):
    """
    Extract diagrams from a PNG image synchronously.
    
    This endpoint processes the uploaded image and returns the results immediately.
    Files are stored in a temporary session and can be downloaded via the files endpoint.
    """
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_FORMAT",
                "message": "File must be an image",
                "details": f"Received content type: {file.content_type}"
            }
        )
    
    if not file.filename or not file.filename.lower().endswith('.png'):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_FORMAT", 
                "message": "File must be a PNG image",
                "details": f"Received filename: {file.filename}"
            }
        )
    
    # Check file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    config_obj = get_config()
    if file_size_mb > config_obj.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File size exceeds limit of {config_obj.max_file_size_mb}MB",
                "details": f"Received file size: {file_size_mb:.2f}MB"
            }
        )
    
    # Parse optional config
    processing_config = {}
    if config:
        try:
            processing_config = json.loads(config)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_CONFIG",
                    "message": "Configuration must be valid JSON",
                    "details": "Failed to parse config parameter"
                }
            )
    
    # Enforce storage limits before processing
    file_manager.enforce_storage_limits()
    
    try:
        # Process the image
        result = extraction_service.process_image(
            image_data=file_content,
            debug=debug,
            verbose=processing_config.get("verbose", False)
        )
        
        return ExtractionResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "PROCESSING_ERROR",
                "message": "Failed to process image",
                "details": str(e)
            }
        )
