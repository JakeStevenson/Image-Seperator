"""Health check endpoint."""

from fastapi import APIRouter
from ..models.responses import HealthResponse
from .. import __version__

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__
    )
