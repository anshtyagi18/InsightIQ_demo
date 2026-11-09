"""
Database Service Layer for Analytics Hub
Replaces in-memory caches with persistent database operations.
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
# Note: Using databases library for async queries, not SQLAlchemy ORM

from src.core.database import (
    database, cache_manager, 
    analysis_sessions, file_uploads, user_sessions, comparison_results,
    store_analysis_session, get_analysis_session, store_file_info, get_file_info,
    store_comparison_result, get_comparison_result
)

logger = logging.getLogger(__name__)

class DatabaseAnalyticsService:
    """Service layer for managing analytics data in the database."""
    
    async def store_analysis_session(
        self, 
        session_id: str,
        analysis_type: str,
        file_info: Dict[str, Any],
        dashboard_config: Dict[str, Any],
        ai_insights: List[Dict[str, Any]],
        performance_metrics: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """Store analysis session results in database."""
        try:
            # Use the existing function from database module
            result = await store_analysis_session(
                session_id=session_id,
                analysis_type=analysis_type,
                file_info=file_info,
                dashboard_config=dashboard_config,
                ai_insights=ai_insights,
                performance_summary=performance_metrics
            )
            
            # Cache the result in Redis for fast access
            cache_key = f"analysis:{session_id}"
            cache_data = {
                "dashboard_config": dashboard_config,
                "ai_insights": ai_insights,
                "performance_metrics": performance_metrics
            }
            await cache_manager.set(cache_key, json.dumps(cache_data), expire=3600)
            
            logger.info(f"Stored analysis session: {session_id}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to store analysis session {session_id}: {e}")
            return False
    
    async def get_analysis_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis session from database or cache."""
        try:
            # Try cache first
            cache_key = f"analysis:{session_id}"
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Retrieved analysis from cache: {session_id}")
                return json.loads(cached_result)
            
            # Use the existing function from database module
            result = await get_analysis_session(session_id)
            if result:
                # Cache for next time
                await cache_manager.set(cache_key, json.dumps(result), expire=3600)
                logger.info(f"Retrieved analysis from database: {session_id}")
                return result
                
            logger.warning(f"Analysis session not found: {session_id}")
            return None
                
        except Exception as e:
            logger.error(f"Failed to get analysis session {session_id}: {e}")
            return None
    
    async def store_file_upload(
        self, 
        session_id: str,
        file_info: Dict[str, Any],
        preview_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Store file upload information."""
        try:
            # Generate file hash
            file_content = json.dumps(file_info, sort_keys=True)
            file_hash = hashlib.md5(file_content.encode()).hexdigest()
            
            # Check if file already exists
            existing_file = await get_file_info(file_hash)
            if existing_file:
                logger.info(f"File already exists with hash: {file_hash}")
                return True
            
            # Use the existing function from database module
            result = await store_file_info(
                file_hash=file_hash,
                filename=file_info.get('filename', 'unknown'),
                file_size=file_info.get('size_bytes', 0),
                mime_type=file_info.get('content_type', 'unknown'),
                upload_path=file_info.get('file_path', ''),
                metadata_info={
                    'session_id': session_id,
                    'user_id': user_id,
                    'stored_filename': file_info.get('stored_filename', file_info.get('filename')),
                    'preview_data': preview_data,
                    'column_info': file_info.get('columns'),
                    'processing_status': 'uploaded'
                }
            )
            
            logger.info(f"Stored file upload: {file_info.get('filename')}")
            return bool(result)
                
        except Exception as e:
            logger.error(f"Failed to store file upload: {e}")
            return False
    
    async def get_file_upload(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve file upload information by session_id."""
        try:
            # Query for file uploads by session_id in metadata
            query = """
                SELECT file_hash, filename, file_size, mime_type, upload_path, metadata_info, created_at
                FROM file_uploads 
                WHERE metadata_info->>'session_id' = :session_id
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            result = await database.fetch_one(query, values={"session_id": session_id})
            
            if result:
                # Handle JSON metadata - could be string or dict
                metadata_info = result["metadata_info"]
                if isinstance(metadata_info, str):
                    try:
                        metadata_info = json.loads(metadata_info)
                    except:
                        metadata_info = {}
                elif metadata_info is None:
                    metadata_info = {}
                
                file_data = {
                    "filename": result["filename"],
                    "file_hash": result["file_hash"],
                    "file_size": result["file_size"],
                    "mime_type": result["mime_type"],
                    "upload_path": result["upload_path"],
                    "metadata": metadata_info,
                    "created_at": result["created_at"].isoformat() if result["created_at"] else None,
                    # Add required fields for compatibility
                    "file_type": metadata_info.get("file_type", "unknown"),
                    "sheet": metadata_info.get("sheet", ""),
                    "row_count": metadata_info.get("row_count", 0),
                    "column_count": metadata_info.get("column_count", 0),
                    "columns": metadata_info.get("columns", []),
                    "uploaded_at": result["created_at"] if result["created_at"] else None,
                    # Note: dataframe not stored in database, will need to be recreated from file
                    "dataframe": None
                }
                
                logger.info(f"Retrieved file upload: {session_id}")
                return file_data
                
            logger.warning(f"File upload not found: {session_id}")
            return None
                
        except Exception as e:
            logger.error(f"Failed to get file upload {session_id}: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent analysis sessions for a user."""
        try:
            # Using raw SQL query with databases library
            query = f"""
                SELECT session_id, analysis_type, file_info, created_at
                FROM analysis_sessions 
                WHERE file_info->>'user_id' = :user_id
                ORDER BY created_at DESC 
                LIMIT :limit
            """
            
            result = await database.fetch_all(
                query, values={"user_id": user_id, "limit": limit}
            )
            
            return [
                {
                    "session_id": row["session_id"],
                    "analysis_type": row["analysis_type"],
                    "filename": row["file_info"].get("filename", "unknown") if row["file_info"] else "unknown",
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                }
                for row in result
            ]
                
        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []
    
    async def find_similar_analysis(self, file_hash: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find similar analysis sessions based on file hash."""
        try:
            # Using raw SQL query with databases library
            base_query = """
                SELECT session_id, dashboard_config, ai_insights, created_at
                FROM analysis_sessions 
                WHERE file_info->>'file_hash' = :file_hash
            """
            
            if user_id:
                base_query += " AND file_info->>'user_id' != :user_id"
                values = {"file_hash": file_hash, "user_id": user_id}
            else:
                values = {"file_hash": file_hash}
            
            base_query += " ORDER BY created_at DESC LIMIT 5"
            
            result = await database.fetch_all(base_query, values=values)
            
            return [
                {
                    "session_id": row["session_id"],
                    "dashboard_config": row["dashboard_config"],
                    "ai_insights": row["ai_insights"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                }
                for row in result
            ]
                
        except Exception as e:
            logger.error(f"Failed to find similar analysis for hash {file_hash}: {e}")
            return []
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old analysis sessions."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Using raw SQL query with databases library
            query = """
                DELETE FROM analysis_sessions 
                WHERE created_at < :cutoff_date
            """
            
            result = await database.execute(query, values={"cutoff_date": cutoff_date})
            deleted_count = result or 0
            
            logger.info(f"Cleaned up {deleted_count} old analysis sessions")
            return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0

    async def store_comparison_result(
        self,
        comparison_id: str,
        analysis_result: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store comparison analysis results."""
        try:
            # Extract file hashes from metadata if available
            estimated_file_hash = metadata.get('estimated_file_id', '') if metadata else ''
            actual_file_hash = metadata.get('actual_file_id', '') if metadata else ''
            
            result = await store_comparison_result(
                session_id=comparison_id,
                estimated_file_hash=estimated_file_hash,
                actual_file_hash=actual_file_hash,
                comparison_data=analysis_result,
                insights=metadata
            )
            
            # Cache the result
            cache_key = f"comparison:{comparison_id}"
            cache_data = {
                "result": analysis_result,
                "metadata": metadata
            }
            await cache_manager.set(cache_key, json.dumps(cache_data), expire=3600)
            
            logger.info(f"Stored comparison result: {comparison_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store comparison result {comparison_id}: {e}")
            return False

    async def get_comparison_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve comparison analysis results."""
        try:
            # Try cache first
            cache_key = f"comparison:{session_id}"
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Retrieved comparison from cache: {session_id}")
                return json.loads(cached_result)
            
            # Query database
            result = await get_comparison_result(session_id)
            if result:
                # Convert any UUID objects to strings for JSON serialization
                serializable_result = {}
                for key, value in result.items():
                    if hasattr(value, 'hex'):  # UUID object
                        serializable_result[key] = str(value)
                    elif isinstance(value, datetime):
                        serializable_result[key] = value.isoformat()
                    else:
                        serializable_result[key] = value
                
                # Cache for next time
                await cache_manager.set(cache_key, json.dumps(serializable_result), expire=3600)
                logger.info(f"Retrieved comparison from database: {session_id}")
                return serializable_result
                
            logger.warning(f"Comparison result not found: {session_id}")
            return None
                
        except Exception as e:
            logger.error(f"Failed to get comparison result {session_id}: {e}")
            return None


# Global instance
database_service = DatabaseAnalyticsService() 