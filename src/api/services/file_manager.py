"""File management service for session-based file handling."""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import shutil

from ..models.config import APIConfig


class FileManager:
    """Manages session-based file storage and cleanup."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.sessions_dir = Path(config.temp_dir) / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def get_file_path(self, session_id: str, filename: str) -> Optional[Path]:
        """Get the full path to a file in a session."""
        session_dir = self.sessions_dir / session_id
        file_path = session_dir / filename
        
        if not session_dir.exists() or not file_path.exists():
            return None
            
        return file_path
    
    def delete_file_after_download(self, session_id: str, filename: str) -> bool:
        """Delete a file after successful download (auto-cleanup behavior)."""
        file_path = self.get_file_path(session_id, filename)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                return True
            except OSError:
                return False
        return False
    
    def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """Clean up expired sessions based on TTL."""
        current_time = time.time()
        ttl_seconds = self.config.session_ttl_hours * 3600
        
        cleaned_sessions = 0
        files_deleted = 0
        bytes_freed = 0
        
        for session_dir in self.sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            # Check if session has expired
            created_time = session_dir.stat().st_ctime
            if current_time - created_time > ttl_seconds:
                # Calculate stats before deletion
                session_files = 0
                session_bytes = 0
                
                for file_path in session_dir.rglob("*"):
                    if file_path.is_file():
                        session_files += 1
                        session_bytes += file_path.stat().st_size
                
                # Remove session
                shutil.rmtree(session_dir, ignore_errors=True)
                
                cleaned_sessions += 1
                files_deleted += session_files
                bytes_freed += session_bytes
        
        return {
            "cleaned_sessions": cleaned_sessions,
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get current storage statistics."""
        total_sessions = 0
        total_files = 0
        total_bytes = 0
        
        for session_dir in self.sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            total_sessions += 1
            
            for file_path in session_dir.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    total_bytes += file_path.stat().st_size
        
        return {
            "total_sessions": total_sessions,
            "total_files": total_files,
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2)
        }
    
    def enforce_storage_limits(self) -> Dict[str, Any]:
        """Enforce storage limits by removing oldest sessions if needed."""
        stats = self.get_storage_stats()
        
        if stats["total_sessions"] <= self.config.max_concurrent_sessions:
            return {"action": "none", "reason": "within_limits"}
        
        # Get sessions sorted by creation time (oldest first)
        sessions = []
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                sessions.append((session_dir.stat().st_ctime, session_dir))
        
        sessions.sort(key=lambda x: x[0])  # Sort by creation time
        
        # Remove oldest sessions until we're within limits
        removed_sessions = 0
        removed_files = 0
        removed_bytes = 0
        
        sessions_to_remove = len(sessions) - self.config.max_concurrent_sessions
        
        for i in range(sessions_to_remove):
            _, session_dir = sessions[i]
            
            # Calculate stats before deletion
            session_files = 0
            session_bytes = 0
            
            for file_path in session_dir.rglob("*"):
                if file_path.is_file():
                    session_files += 1
                    session_bytes += file_path.stat().st_size
            
            # Remove session
            shutil.rmtree(session_dir, ignore_errors=True)
            
            removed_sessions += 1
            removed_files += session_files
            removed_bytes += session_bytes
        
        return {
            "action": "cleanup",
            "removed_sessions": removed_sessions,
            "removed_files": removed_files,
            "removed_bytes": removed_bytes,
            "reason": "storage_limit_exceeded"
        }
