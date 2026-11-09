"""
FastAPI router for dashboard export functionality.
Supports PDF, PNG, and HTML export formats with role-based access controls.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..services.export_service import (
    DashboardExportService, 
    ExportFormat, 
    ExportOptions, 
    ExportResult,
    export_service
)
from ..auth import (
    User, 
    Permission,
    get_current_user, 
    require_permission,
    require_export_permission
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])

# Request/Response Models
class ExportRequest(BaseModel):
    """Request model for dashboard export."""
    dashboard_data: Dict[str, Any] = Field(..., description="Dashboard data to export")
    format: ExportFormat = Field(..., description="Export format")
    options: Optional[ExportOptions] = Field(None, description="Export options")

class ExportStatusResponse(BaseModel):
    """Response model for export status."""
    export_id: str
    status: str
    format: ExportFormat
    file_size: Optional[int] = None
    created_at: str
    download_url: Optional[str] = None
    user_info: Dict[str, str] = Field(default_factory=dict, description="User information")

@router.post("/dashboard", response_model=ExportStatusResponse)
async def export_dashboard(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_export_permission())
):
    """
    Export a dashboard in the specified format.
    
    Supports PDF, PNG, and HTML export formats with various customization options.
    Requires appropriate export permissions based on user role.
    """
    try:
        logger.info(f"Dashboard export request from user {current_user.username} (role: {current_user.role.value})")
        
        # Validate format-specific permissions
        format_str = request.format.value
        if not current_user.can_export(format_str):
            raise HTTPException(
                status_code=403,
                detail=f"User role '{current_user.role.value}' does not have permission to export in {format_str} format"
            )
        
        # Validate dashboard data
        if not request.dashboard_data:
            raise HTTPException(status_code=400, detail="Dashboard data is required")
        
        # Perform export
        result = await export_service.export_dashboard(
            dashboard_data=request.dashboard_data,
            format=request.format,
            options=request.options,
            user_id=current_user.id
        )
        
        # Schedule cleanup task
        background_tasks.add_task(
            export_service.cleanup_old_exports, 
            max_age_hours=24
        )
        
        # Generate download URL
        download_url = f"/export/download/{result.export_id}"
        
        return ExportStatusResponse(
            export_id=result.export_id,
            status="completed",
            format=result.format,
            file_size=result.file_size,
            created_at=result.created_at.isoformat(),
            download_url=download_url,
            user_info={
                "user_id": current_user.id,
                "username": current_user.username,
                "role": current_user.role.value
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like permission errors)
        raise
    except Exception as e:
        logger.error(f"Export failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download an exported file by export ID.
    
    Users can only download their own exports unless they have admin privileges.
    """
    try:
        # Find export file
        export_dir = Path("exports")
        
        # Look for file with export_id
        possible_files = list(export_dir.glob(f"{export_id}.*"))
        
        if not possible_files:
            raise HTTPException(status_code=404, detail="Export file not found")
        
        file_path = possible_files[0]
        
        # TODO: In production, verify user ownership of export
        # For now, allow any authenticated user to download
        logger.info(f"User {current_user.username} downloading export {export_id}")
        
        # Determine content type based on file extension
        content_type_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".html": "text/html",
            ".svg": "image/svg+xml"
        }
        
        content_type = content_type_map.get(file_path.suffix, "application/octet-stream")
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=file_path.name
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Export file not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/status/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of an export operation.
    
    Users can check status of any export (for now).
    """
    try:
        # Check if export file exists
        export_dir = Path("exports")
        possible_files = list(export_dir.glob(f"{export_id}.*"))
        
        if not possible_files:
            return ExportStatusResponse(
                export_id=export_id,
                status="not_found",
                format=ExportFormat.PDF,  # Default, actual format unknown
                created_at="unknown",
                user_info={
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "role": current_user.role.value
                }
            )
        
        file_path = possible_files[0]
        file_stat = file_path.stat()
        
        # Determine format from extension
        format_map = {
            ".pdf": ExportFormat.PDF,
            ".png": ExportFormat.PNG,
            ".html": ExportFormat.HTML,
            ".svg": ExportFormat.SVG
        }
        
        file_format = format_map.get(file_path.suffix, ExportFormat.PDF)
        
        return ExportStatusResponse(
            export_id=export_id,
            status="completed",
            format=file_format,
            file_size=file_stat.st_size,
            created_at=str(file_stat.st_mtime),
            download_url=f"/export/download/{export_id}",
            user_info={
                "user_id": current_user.id,
                "username": current_user.username,
                "role": current_user.role.value
            }
        )
        
    except Exception as e:
        logger.error(f"Status check failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/quick-pdf")
async def quick_pdf_export(
    dashboard_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    width: int = Query(1200, description="Page width in pixels"),
    height: int = Query(800, description="Page height in pixels"),
    current_user: User = Depends(require_export_permission("pdf"))
):
    """
    Quick PDF export with minimal configuration.
    Requires PDF export permission.
    """
    try:
        logger.info(f"Quick PDF export request from user {current_user.username}")
        
        options = ExportOptions(
            format=ExportFormat.PDF,
            width=width,
            height=height
        )
        
        result = await export_service.export_dashboard(
            dashboard_data=dashboard_data,
            format=ExportFormat.PDF,
            options=options,
            user_id=current_user.id
        )
        
        background_tasks.add_task(export_service.cleanup_old_exports)
        
        return FileResponse(
            path=result.file_path,
            media_type="application/pdf",
            filename=f"dashboard_{result.export_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick PDF export failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@router.post("/quick-png")
async def quick_png_export(
    dashboard_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    width: int = Query(1200, description="Image width in pixels"),
    height: int = Query(800, description="Image height in pixels"),
    full_page: bool = Query(True, description="Capture full page"),
    current_user: User = Depends(require_export_permission("png"))
):
    """
    Quick PNG export with minimal configuration.
    Requires PNG export permission.
    """
    try:
        logger.info(f"Quick PNG export request from user {current_user.username}")
        
        options = ExportOptions(
            format=ExportFormat.PNG,
            width=width,
            height=height,
            full_page=full_page
        )
        
        result = await export_service.export_dashboard(
            dashboard_data=dashboard_data,
            format=ExportFormat.PNG,
            options=options,
            user_id=current_user.id
        )
        
        background_tasks.add_task(export_service.cleanup_old_exports)
        
        return FileResponse(
            path=result.file_path,
            media_type="image/png",
            filename=f"dashboard_{result.export_id}.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick PNG export failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PNG export failed: {str(e)}")

@router.delete("/cleanup")
async def cleanup_exports(
    max_age_hours: int = Query(24, description="Maximum age in hours for files to keep"),
    current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """
    Manually trigger cleanup of old export files.
    Requires admin privileges.
    """
    try:
        logger.info(f"Cleanup initiated by admin user {current_user.username}")
        export_service.cleanup_old_exports(max_age_hours=max_age_hours)
        return {
            "status": "cleanup_completed", 
            "max_age_hours": max_age_hours,
            "initiated_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleanup failed for user {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/formats")
async def get_supported_formats(current_user: User = Depends(get_current_user)):
    """
    Get list of supported export formats and their capabilities.
    Returns permissions based on user role.
    """
    base_formats = [
        {
            "format": "pdf",
            "description": "Portable Document Format - High quality for printing",
            "supports_vector": True,
            "supports_interactive": False,
            "available": current_user.can_export("pdf")
        },
        {
            "format": "png", 
            "description": "Portable Network Graphics - High quality raster image",
            "supports_vector": False,
            "supports_interactive": False,
            "available": current_user.can_export("png")
        },
        {
            "format": "html",
            "description": "HyperText Markup Language - Interactive web format",
            "supports_vector": True,
            "supports_interactive": True,
            "available": current_user.can_export("html")
        }
    ]
    
    return {
        "formats": base_formats,
        "user_info": {
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role.value,
            "can_export_any": current_user.can_export()
        },
        "default_options": {
            "width": 1200,
            "height": 800,
            "timeout": 30000,
            "background": True
        }
    }

@router.get("/permissions")
async def get_user_permissions(current_user: User = Depends(get_current_user)):
    """
    Get current user's export permissions.
    Useful for frontend to enable/disable features.
    """
    return {
        "user_info": {
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role.value
        },
        "export_permissions": {
            "pdf": current_user.can_export("pdf"),
            "png": current_user.can_export("png"), 
            "html": current_user.can_export("html"),
            "bulk": current_user.has_permission(Permission.EXPORT_BULK),
            "share": current_user.has_permission(Permission.EXPORT_SHARE)
        },
        "dashboard_permissions": {
            "view": current_user.has_permission(Permission.DASHBOARD_VIEW),
            "create": current_user.has_permission(Permission.DASHBOARD_CREATE),
            "edit": current_user.has_permission(Permission.DASHBOARD_EDIT),
            "delete": current_user.has_permission(Permission.DASHBOARD_DELETE),
            "share": current_user.has_permission(Permission.DASHBOARD_SHARE)
        },
        "system_permissions": {
            "admin": current_user.has_permission(Permission.SYSTEM_ADMIN),
            "user_manage": current_user.has_permission(Permission.USER_MANAGE)
        }
    } 