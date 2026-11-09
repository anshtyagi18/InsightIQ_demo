"""
UI State router for managing user interface preferences and state.
Replaces localStorage functionality with database-backed storage.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ..core.database import (
    store_ui_state, get_ui_state, get_all_ui_state, 
    store_dashboard_state, get_dashboard_state, delete_ui_state
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ui-state", tags=["ui-state"])
security = HTTPBearer(auto_error=False)

# Request/Response Models
class UIStateRequest(BaseModel):
    state_type: str = Field(..., description="Type of state (theme, preferences, dashboard, etc.)")
    state_key: str = Field(..., description="Specific key within the state type")
    state_value: Any = Field(..., description="The state value to store")

class DashboardStateRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard identifier")
    layout_config: Dict[str, Any] = Field(..., description="Layout configuration")
    theme_config: Optional[Dict[str, Any]] = Field(None, description="Theme configuration")
    filters_config: Optional[Dict[str, Any]] = Field(None, description="Filters configuration")

class UIStateResponse(BaseModel):
    success: bool
    state_value: Optional[Any] = None
    message: Optional[str] = None

# Helper function to get user from token
async def get_current_user_id(authorization: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Extract user ID from authorization token."""
    if not authorization:
        # Allow anonymous users with a guest user ID
        return "guest_user"
    
    # For now, use a simple user ID extraction
    # In production, this should validate the JWT and extract user ID
    token = authorization.credentials
    
    # Mock user ID for development - replace with real JWT validation
    user_id = f"user_{hash(token) % 1000000}"
    return user_id

# UI State endpoints
@router.post("/store", response_model=UIStateResponse)
async def store_state(
    request: UIStateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Store UI state in database (replaces localStorage.setItem)."""
    try:
        logger.info(f"📝 Storing UI state: {request.state_type}.{request.state_key} for user {user_id}")
        
        success = await store_ui_state(
            user_id=user_id,
            state_type=request.state_type,
            state_key=request.state_key,
            state_value=request.state_value
        )
        
        if success:
            return UIStateResponse(success=True, message="State stored successfully")
        else:
            raise HTTPException(status_code=500, detail="Failed to store state")
            
    except Exception as e:
        logger.error(f"❌ Error storing UI state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get/{state_type}/{state_key}", response_model=UIStateResponse)
async def get_state(
    state_type: str,
    state_key: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get UI state from database (replaces localStorage.getItem)."""
    try:
        logger.info(f"🔍 Getting UI state: {state_type}.{state_key} for user {user_id}")
        
        state_value = await get_ui_state(
            user_id=user_id,
            state_type=state_type,
            state_key=state_key
        )
        
        return UIStateResponse(
            success=True,
            state_value=state_value,
            message="State retrieved successfully" if state_value is not None else "State not found"
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting UI state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-all/{state_type}")
async def get_all_state(
    state_type: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get all UI state for a specific type (e.g., all preferences)."""
    try:
        logger.info(f"🔍 Getting all UI state for type: {state_type}, user {user_id}")
        
        state_data = await get_all_ui_state(
            user_id=user_id,
            state_type=state_type
        )
        
        return {
            "success": True,
            "state_data": state_data,
            "message": "State data retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting all UI state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{state_type}/{state_key}")
async def delete_state(
    state_type: str,
    state_key: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete UI state from database (replaces localStorage.removeItem)."""
    try:
        logger.info(f"🗑️ Deleting UI state: {state_type}.{state_key} for user {user_id}")
        
        success = await delete_ui_state(
            user_id=user_id,
            state_type=state_type,
            state_key=state_key
        )
        
        if success:
            return {"success": True, "message": "State deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete state")
            
    except Exception as e:
        logger.error(f"❌ Error deleting UI state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard State endpoints
@router.post("/dashboard/store")
async def store_dashboard(
    request: DashboardStateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Store dashboard state in database."""
    try:
        logger.info(f"📊 Storing dashboard state: {request.dashboard_id} for user {user_id}")
        
        success = await store_dashboard_state(
            user_id=user_id,
            dashboard_id=request.dashboard_id,
            layout_config=request.layout_config,
            theme_config=request.theme_config,
            filters_config=request.filters_config
        )
        
        if success:
            return {"success": True, "message": "Dashboard state stored successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to store dashboard state")
            
    except Exception as e:
        logger.error(f"❌ Error storing dashboard state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/get/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get dashboard state from database."""
    try:
        logger.info(f"🔍 Getting dashboard state: {dashboard_id} for user {user_id}")
        
        dashboard_state = await get_dashboard_state(
            user_id=user_id,
            dashboard_id=dashboard_id
        )
        
        return {
            "success": True,
            "dashboard_state": dashboard_state,
            "message": "Dashboard state retrieved successfully" if dashboard_state else "Dashboard state not found"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch operations for performance
@router.post("/batch-store")
async def batch_store_state(
    states: list[UIStateRequest],
    user_id: str = Depends(get_current_user_id)
):
    """Store multiple UI states in one request for better performance."""
    try:
        logger.info(f"📦 Batch storing {len(states)} UI states for user {user_id}")
        
        results = []
        for state in states:
            success = await store_ui_state(
                user_id=user_id,
                state_type=state.state_type,
                state_key=state.state_key,
                state_value=state.state_value
            )
            results.append({
                "state_type": state.state_type,
                "state_key": state.state_key,
                "success": success
            })
        
        return {
            "success": True,
            "results": results,
            "message": f"Batch stored {len(states)} states"
        }
        
    except Exception as e:
        logger.error(f"❌ Error batch storing UI states: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ui_state_health():
    """Health check endpoint for UI state service."""
    return {
        "status": "healthy",
        "service": "ui-state-management",
        "features": [
            "Database-backed UI state storage",
            "Theme preferences persistence",
            "Dashboard configuration storage",
            "User preference management",
            "Performance-optimized localStorage replacement"
        ]
    } 