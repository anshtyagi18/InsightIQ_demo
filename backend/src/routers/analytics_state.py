"""
Analytics State router for frontend state management integration.
Provides endpoints for storing and retrieving analytics sessions, file uploads, and user data.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.database import database, get_analysis_session, store_analysis_session
from ..services.database_service import DatabaseAnalyticsService
from ..auth.service import get_current_user
from ..auth.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics-state"])

# Initialize database service
db_service = DatabaseAnalyticsService()

# Request/Response Models
class AnalyticsSessionRequest(BaseModel):
    sessionId: str = Field(..., description="Analytics session ID")
    analysisType: str = Field(..., description="Type of analysis")
    fileInfo: Dict[str, Any] = Field(..., description="File information")
    dashboardConfig: Dict[str, Any] = Field(..., description="Dashboard configuration")
    aiInsights: List[Dict[str, Any]] = Field(default_factory=list, description="AI insights")
    performanceMetrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")

class AnalyticsSessionResponse(BaseModel):
    id: str
    sessionId: str
    analysisType: str
    fileInfo: Dict[str, Any]
    dashboardConfig: Optional[Dict[str, Any]] = None
    aiInsights: Optional[List[Dict[str, Any]]] = None
    performanceSummary: Optional[Dict[str, Any]] = None
    createdAt: str
    updatedAt: str

class FileUploadResponse(BaseModel):
    id: str
    fileHash: str
    filename: str
    fileSize: int
    mimeType: str
    uploadPath: str
    processed: bool
    metadata: Dict[str, Any]
    createdAt: str

class UserSessionResponse(BaseModel):
    recentSessions: List[AnalyticsSessionResponse]
    recentUploads: List[FileUploadResponse]
    preferences: Dict[str, Any]

# Analytics Session Endpoints
@router.post("/sessions", response_model=Dict[str, Any])
async def store_analytics_session(
    request: AnalyticsSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Store analytics session in database."""
    try:
        logger.info(f"Storing analytics session: {request.sessionId}")
        
        # Add user info to file info
        enhanced_file_info = {
            **request.fileInfo,
            "user_id": current_user.id,
            "user_email": current_user.email
        }
        
        success = await db_service.store_analysis_session(
            session_id=request.sessionId,
            analysis_type=request.analysisType,
            file_info=enhanced_file_info,
            dashboard_config=request.dashboardConfig,
            ai_insights=request.aiInsights,
            performance_metrics=request.performanceMetrics,
            user_id=current_user.id
        )
        
        if success:
            return {
                "success": True,
                "message": "Analytics session stored successfully",
                "sessionId": request.sessionId
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store analytics session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing analytics session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=AnalyticsSessionResponse)
async def get_analytics_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get analytics session from database."""
    try:
        logger.info(f"Retrieving analytics session: {session_id}")
        
        session_data = await db_service.get_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Analytics session not found")
        
        # Convert to response model
        return AnalyticsSessionResponse(
            id=session_data.get("id", session_id),
            sessionId=session_id,
            analysisType=session_data.get("analysis_type", "unknown"),
            fileInfo=session_data.get("file_info", {}),
            dashboardConfig=session_data.get("dashboard_config"),
            aiInsights=session_data.get("ai_insights"),
            performanceSummary=session_data.get("performance_summary"),
            createdAt=session_data.get("created_at", datetime.utcnow().isoformat()),
            updatedAt=session_data.get("updated_at", datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analytics session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")

@router.get("/sessions/recent", response_model=List[AnalyticsSessionResponse])
async def get_recent_sessions(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's recent analytics sessions."""
    try:
        logger.info(f"Retrieving recent sessions for user: {current_user.id}")
        
        sessions = await db_service.get_user_sessions(user_id=current_user.id, limit=limit)
        
        # Convert to response models
        response_sessions = []
        for session in sessions:
            response_sessions.append(AnalyticsSessionResponse(
                id=session.get("id", session["session_id"]),
                sessionId=session["session_id"],
                analysisType=session["analysis_type"],
                fileInfo=session["file_info"],
                dashboardConfig=None,  # Not included in recent sessions for performance
                aiInsights=None,
                performanceSummary=None,
                createdAt=session["created_at"],
                updatedAt=session.get("updated_at", session["created_at"])
            ))
        
        return response_sessions
        
    except Exception as e:
        logger.error(f"Error retrieving recent sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent sessions: {str(e)}")

# File Upload Endpoints
@router.post("/files/store")
async def store_file_upload(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Store file upload information."""
    try:
        session_id = request.get("sessionId")
        file_info = request.get("fileInfo", {})
        preview_data = request.get("previewData")
        
        logger.info(f"Storing file upload for session: {session_id}")
        
        # Add user info
        enhanced_file_info = {
            **file_info,
            "user_id": current_user.id,
            "user_email": current_user.email
        }
        
        success = await db_service.store_file_upload(
            session_id=session_id,
            file_info=enhanced_file_info,
            preview_data=preview_data,
            user_id=current_user.id
        )
        
        if success:
            return {
                "success": True,
                "message": "File upload stored successfully",
                "sessionId": session_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store file upload")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store file upload: {str(e)}")

@router.get("/files/info/{session_id}", response_model=FileUploadResponse)
async def get_file_upload(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get file upload information."""
    try:
        logger.info(f"Retrieving file upload for session: {session_id}")
        
        file_data = await db_service.get_file_upload(session_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File upload not found")
        
        return FileUploadResponse(
            id=file_data.get("id", file_data["file_hash"]),
            fileHash=file_data["file_hash"],
            filename=file_data["filename"],
            fileSize=file_data["file_size"],
            mimeType=file_data["mime_type"],
            uploadPath=file_data["upload_path"],
            processed=file_data.get("processed", False),
            metadata=file_data.get("metadata", {}),
            createdAt=file_data.get("created_at", datetime.utcnow().isoformat())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file upload: {str(e)}")

@router.get("/files/recent", response_model=List[FileUploadResponse])
async def get_recent_uploads(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get user's recent file uploads."""
    try:
        logger.info(f"Retrieving recent uploads for user: {current_user.id}")
        
        # Query recent uploads
        query = """
            SELECT file_hash, filename, file_size, mime_type, upload_path, 
                   metadata_info, created_at, processed
            FROM file_uploads 
            ORDER BY created_at DESC 
            LIMIT :limit
        """
        
        results = await database.fetch_all(query, {
            "limit": limit * 2
        })
        
        uploads = []
        for result in results:
            metadata = result["metadata_info"]
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            elif metadata is None:
                metadata = {}
            
            uploads.append(FileUploadResponse(
                id=result["file_hash"],
                fileHash=result["file_hash"],
                filename=result["filename"],
                fileSize=result["file_size"],
                mimeType=result["mime_type"],
                uploadPath=result["upload_path"],
                processed=result.get("processed", False),
                metadata=metadata,
                createdAt=result["created_at"].isoformat() if result["created_at"] else datetime.utcnow().isoformat()
            ))
        
        return uploads
        
    except Exception as e:
        logger.error(f"Error retrieving recent uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent uploads: {str(e)}")

# User Session Endpoint
@router.get("/user-session", response_model=UserSessionResponse)
async def get_user_session_data(
    current_user: User = Depends(get_current_user)
):
    """Get user's session data including recent sessions and uploads."""
    try:
        logger.info(f"Retrieving user session data for: {current_user.id}")
        
        # Get recent sessions and uploads in parallel
        import asyncio
        
        recent_sessions_task = get_recent_sessions(limit=10, current_user=current_user)
        recent_uploads_task = get_recent_uploads(limit=5, current_user=current_user)
        
        recent_sessions, recent_uploads = await asyncio.gather(
            recent_sessions_task,
            recent_uploads_task,
            return_exceptions=True
        )
        
        # Handle any exceptions
        if isinstance(recent_sessions, Exception):
            logger.warning(f"Failed to get recent sessions: {recent_sessions}")
            recent_sessions = []
        
        if isinstance(recent_uploads, Exception):
            logger.warning(f"Failed to get recent uploads: {recent_uploads}")
            recent_uploads = []
        
        # Default user preferences
        preferences = {
            "defaultChartType": "bar",
            "theme": "light",
            "autoRefresh": False
        }
        
        return UserSessionResponse(
            recentSessions=recent_sessions,
            recentUploads=recent_uploads,
            preferences=preferences
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user session data: {e}")
        # Return empty data rather than failing
        return UserSessionResponse(
            recentSessions=[],
            recentUploads=[],
            preferences={
                "defaultChartType": "bar",
                "theme": "light",
                "autoRefresh": False
            }
        )

# Comparison Results Endpoints
@router.post("/comparison/store")
async def store_comparison_result(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Store comparison result."""
    try:
        session_id = request.get("sessionId")
        comparison_data = request.get("comparisonData", {})
        insights = request.get("insights", {})
        
        logger.info(f"Storing comparison result for session: {session_id}")
        
        success = await db_service.store_comparison_result(
            comparison_id=session_id,
            analysis_result=comparison_data,
            metadata={
                "user_id": current_user.id,
                "insights": insights
            }
        )
        
        if success:
            return {
                "success": True,
                "message": "Comparison result stored successfully",
                "sessionId": session_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store comparison result")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing comparison result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store comparison result: {str(e)}")

@router.get("/comparison/result/{session_id}")
async def get_comparison_result(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get comparison result."""
    try:
        logger.info(f"Retrieving comparison result for session: {session_id}")
        
        result = await db_service.get_comparison_result(session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Comparison result not found")
        
        return {
            "id": result.get("id", session_id),
            "sessionId": session_id,
            "estimatedFileHash": result.get("estimated_file_hash", ""),
            "actualFileHash": result.get("actual_file_hash", ""),
            "comparisonData": result.get("comparison_data", {}),
            "insights": result.get("insights", {}),
            "createdAt": result.get("created_at", datetime.utcnow().isoformat())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving comparison result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve comparison result: {str(e)}")

@router.get("/health")
async def analytics_state_health():
    """Health check for analytics state service."""
    return {
        "status": "healthy",
        "service": "analytics-state",
        "features": [
            "session_storage",
            "file_tracking",
            "comparison_results",
            "user_preferences"
        ]
    } 