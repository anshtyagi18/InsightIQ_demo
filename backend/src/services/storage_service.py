"""
Storage service for file management.
Implements local asynchronous file storage for InsightIQ.
"""

import os
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import aiofiles
from fastapi import HTTPException

class StorageService:
    """Service for managing local file storage."""
    
    def __init__(self, storage_type: str = "local", base_path: str = "uploads"):
        """
        Initialize storage service.
        
        Args:
            storage_type: Type of storage (defaults to "local")
            base_path: Base path for local storage
        """
        self.storage_type = "local"
        self.base_path = base_path
        self._ensure_local_directories()
    
    def _ensure_local_directories(self):
        """Ensure local storage directories exist."""
        upload_dir = Path(self.base_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories by date for organization
        today = datetime.now().strftime("%Y/%m/%d")
        daily_dir = upload_dir / today
        daily_dir.mkdir(parents=True, exist_ok=True)
    
    async def store_file(
        self, 
        content: bytes, 
        original_filename: str, 
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store file and return storage information.
        
        Args:
            content: File content as bytes
            original_filename: Original filename
            content_type: MIME type
            metadata: Additional metadata to store
            
        Returns:
            Dictionary with storage information
        """
        # Generate unique filename
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        file_hash = hashlib.sha256(content).hexdigest()[:16]
        
        # Create filename with timestamp and hash for uniqueness
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stored_filename = f"{timestamp}_{file_hash}_{unique_id}{file_extension}"
        
        return await self._store_local(
            content, stored_filename, original_filename, content_type, metadata
        )
    
    async def _store_local(
        self, 
        content: bytes, 
        stored_filename: str, 
        original_filename: str, 
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store file locally."""
        today = datetime.now().strftime("%Y/%m/%d")
        file_path = Path(self.base_path) / today / stored_filename
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            storage_info = {
                "storage_type": "local",
                "file_path": str(file_path),
                "relative_path": f"{today}/{stored_filename}",
                "stored_filename": stored_filename,
                "original_filename": original_filename,
                "content_type": content_type,
                "size_bytes": len(content),
                "file_hash": hashlib.sha256(content).hexdigest(),
                "upload_time": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            }
            
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta.json')
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(storage_info, indent=2))
            
            storage_info["access_url"] = f"/api/v1/files/download/{today}/{stored_filename}"
            return storage_info
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store file locally: {str(e)}"
            )
    
    async def get_file(self, file_path: str) -> bytes:
        """Retrieve file content."""
        full_path = Path(self.base_path) / file_path
        
        if not full_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        try:
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {str(e)}"
            )
    
    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata."""
        metadata_path = Path(self.base_path) / (file_path + '.meta.json')
        
        if not metadata_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File metadata not found"
            )
        
        try:
            async with aiofiles.open(metadata_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read metadata: {str(e)}"
            )
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get storage configuration information."""
        return {
            "storage_type": "local",
            "base_path": self.base_path,
            "features": {
                "local_storage": True,
                "file_download": True,
                "metadata_storage": True
            }
        }
