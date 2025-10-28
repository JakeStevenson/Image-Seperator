"""Main FastAPI application for the diagram extraction API."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .models.config import APIConfig
from .models.responses import ErrorResponse
from .routes import health, extract, files
from .services.file_manager import FileManager


# Global config instance
config = APIConfig.from_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"Starting Diagram Extraction API v{app.version}")
    print(f"Configuration: {config.dict()}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("API shutdown complete")


async def periodic_cleanup():
    """Periodic cleanup of expired sessions."""
    file_manager = FileManager(config)
    
    while True:
        try:
            await asyncio.sleep(900)  # Run every 15 minutes
            result = file_manager.cleanup_expired_sessions()
            if result["cleaned_sessions"] > 0:
                print(f"Cleanup: removed {result['cleaned_sessions']} expired sessions, "
                      f"freed {result['bytes_freed']} bytes")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Cleanup error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Diagram Extraction API",
    description="HTTP API for extracting diagrams from handwritten notes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    
    # If detail is already a dict (from our endpoints), use it directly
    if isinstance(exc.detail, dict):
        error_detail = exc.detail
    else:
        # Convert string details to structured format
        error_detail = {
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "details": None
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=error_detail,
            timestamp=datetime.now()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    print(f"Unexpected error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if config.host == "0.0.0.0" else None  # Only show details in dev
            },
            timestamp=datetime.now()
        ).dict()
    )


# Include routers
app.include_router(health.router)
app.include_router(extract.router)
app.include_router(files.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Diagram Extraction API",
        "version": "1.0.0",
        "description": "HTTP API for extracting diagrams from handwritten notes",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level="info"
    )
