"""Extraction service that wraps the existing CLI functionality."""

import subprocess
import tempfile
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil
import os

from ..models.config import APIConfig
from ..models.responses import ProcessingManifest, DiagramInfo, DebugImageInfo


class ExtractionService:
    """Service for processing images using the existing CLI."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.cli_path = Path(__file__).parent.parent.parent / "extract_diagrams.py"
        
    def process_image(
        self, 
        image_data: bytes, 
        debug: bool = False, 
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Process an image using the existing CLI and return structured results.
        
        Args:
            image_data: Raw PNG image bytes
            debug: Whether to generate debug images
            verbose: Whether to enable verbose logging
            
        Returns:
            Dictionary containing processing results and session information
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        # Create session directory
        session_dir = Path(self.config.temp_dir) / "sessions" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save uploaded image
            input_path = session_dir / "input.png"
            input_path.write_bytes(image_data)
            
            # Create output directory within session
            output_dir = session_dir / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Build CLI command
            cmd = [
                "python", str(self.cli_path),
                str(input_path),
                str(output_dir)
            ]
            
            if debug:
                cmd.append("--debug")
            if verbose:
                cmd.append("--verbose")
            
            # Execute CLI
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=self.config.processing_timeout_seconds,
                cwd=str(self.cli_path.parent)
            )
            
            if result.returncode != 0:
                raise Exception(f"CLI processing failed: {result.stderr}")
            
            # Read manifest
            manifest_path = output_dir / "manifest.json"
            if not manifest_path.exists():
                raise Exception("Manifest file not created by CLI")
                
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            # Move files to session storage and build response
            processing_time = time.time() - start_time
            
            return self._build_response(
                session_id=session_id,
                session_dir=session_dir,
                output_dir=output_dir,
                manifest_data=manifest_data,
                processing_time=processing_time,
                debug=debug
            )
            
        except subprocess.TimeoutExpired:
            # Clean up on timeout
            shutil.rmtree(session_dir, ignore_errors=True)
            raise Exception(f"Processing timed out after {self.config.processing_timeout_seconds} seconds")
        except Exception as e:
            # Clean up on error
            shutil.rmtree(session_dir, ignore_errors=True)
            raise e
    
    def _build_response(
        self,
        session_id: str,
        session_dir: Path,
        output_dir: Path,
        manifest_data: Dict[str, Any],
        processing_time: float,
        debug: bool
    ) -> Dict[str, Any]:
        """Build the API response from CLI output."""
        
        # Move files from output_dir to session root for serving
        final_files = []
        
        # Move manifest
        manifest_src = output_dir / "manifest.json"
        manifest_dst = session_dir / "manifest.json"
        shutil.move(str(manifest_src), str(manifest_dst))
        final_files.append("manifest.json")
        
        # Move diagram files
        diagram_files = []
        for diagram in manifest_data.get("diagrams", []):
            if diagram.get("extracted", False):
                filename = diagram["file"]
                src_path = output_dir / filename
                dst_path = session_dir / filename
                
                if src_path.exists():
                    shutil.move(str(src_path), str(dst_path))
                    final_files.append(filename)
                    
                    # Build diagram info for response
                    diagram_files.append(DiagramInfo(
                        id=diagram["id"],
                        filename=filename,
                        bbox=diagram["bbox"],
                        confidence=diagram["confidence"],
                        url=f"/api/v1/files/{session_id}/{filename}"
                    ))
        
        # Move debug files if requested
        debug_files = []
        if debug:
            debug_patterns = [
                "*.png"  # All debug PNG files
            ]
            
            for pattern in debug_patterns:
                for debug_file in output_dir.glob(pattern):
                    if debug_file.name not in [d["file"] for d in manifest_data.get("diagrams", [])]:
                        dst_path = session_dir / debug_file.name
                        shutil.move(str(debug_file), str(dst_path))
                        final_files.append(debug_file.name)
                        
                        debug_files.append(DebugImageInfo(
                            name=debug_file.name,
                            url=f"/api/v1/files/{session_id}/{debug_file.name}"
                        ))
        
        # Clean up empty output directory
        shutil.rmtree(output_dir, ignore_errors=True)
        
        # Build manifest response
        manifest_response = ProcessingManifest(
            original_file=manifest_data["original_file"],
            diagrams=manifest_data.get("diagrams", []),
            processing_info=manifest_data.get("processing_info", {})
        )
        
        # Build final response
        response = {
            "success": True,
            "processing_time": round(processing_time, 2),
            "session_id": session_id,
            "manifest": manifest_response,
            "diagrams": diagram_files
        }
        
        if debug_files:
            response["debug_images"] = debug_files
            
        return response
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        session_dir = Path(self.config.temp_dir) / "sessions" / session_id
        
        if not session_dir.exists():
            return None
            
        files = []
        total_size = 0
        
        for file_path in session_dir.iterdir():
            if file_path.is_file():
                size = file_path.stat().st_size
                files.append(file_path.name)
                total_size += size
        
        # Get creation time from directory
        created_at = session_dir.stat().st_ctime
        expires_at = created_at + (self.config.session_ttl_hours * 3600)
        
        return {
            "session_id": session_id,
            "created_at": created_at,
            "expires_at": expires_at,
            "file_count": len(files),
            "total_size_bytes": total_size,
            "files": sorted(files)
        }
    
    def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """Clean up a session and return cleanup stats."""
        session_dir = Path(self.config.temp_dir) / "sessions" / session_id
        
        if not session_dir.exists():
            return {
                "success": False,
                "files_deleted": 0,
                "bytes_freed": 0,
                "error": "Session not found"
            }
        
        # Calculate stats before deletion
        files_deleted = 0
        bytes_freed = 0
        
        for file_path in session_dir.rglob("*"):
            if file_path.is_file():
                files_deleted += 1
                bytes_freed += file_path.stat().st_size
        
        # Remove the entire session directory
        shutil.rmtree(session_dir, ignore_errors=True)
        
        return {
            "success": True,
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed
        }
