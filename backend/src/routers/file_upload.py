"""
File upload router for Analytics Hub API.
Handles file uploads with validation and processing.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
import os
import io
import uuid
import logging
import json
from datetime import datetime
from ..services.file_parser import FileParserService, SmartJSONEncoder
from ..services.storage_service import StorageService
from .websocket import (
    update_file_processing_progress, 
    send_processing_error, 
    send_processing_completion
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/files",
    tags=["File Upload"],
    responses={404: {"description": "Not found"}},
)

# Configuration constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}
ALLOWED_CONTENT_TYPES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json'
}

# Initialize storage service
# TODO: Make this configurable via environment variables
storage_service = StorageService(storage_type="local", base_path="uploads")

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    include_preview: bool = Query(True, description="Include file content preview in response"),
    preview_rows: int = Query(5, ge=1, le=50, description="Number of rows to include in preview"),
    store_file: bool = Query(True, description="Store file permanently (false for preview only)"),
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Upload a file for analysis with real-time progress updates.
    
    Accepts CSV, Excel (xlsx, xls), and JSON files up to 10MB.
    Returns file metadata, upload status, storage info, and optional content preview.
    """
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        # Stage 1: File validation
        await update_file_processing_progress(session_id, "validation", 10, "Validating file format and size...")
        
        # Basic file validation
        if not file.filename:
            await send_processing_error(session_id, "No file provided", "NO_FILE")
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            await send_processing_error(session_id, f"File type not allowed. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}", "INVALID_FORMAT")
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check content type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            await send_processing_error(session_id, f"Content type not allowed. Received: {file.content_type}", "INVALID_CONTENT_TYPE")
            raise HTTPException(
                status_code=400,
                detail=f"Content type not allowed. Received: {file.content_type}"
            )
        
        await update_file_processing_progress(session_id, "validation", 25, "Reading file content...")
        
        # Read file content to check size and for preview
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            await send_processing_error(session_id, f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB", "FILE_TOO_LARGE")
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            await send_processing_error(session_id, "Empty file not allowed", "EMPTY_FILE")
            raise HTTPException(status_code=400, detail="Empty file not allowed")
        
        await update_file_processing_progress(session_id, "validation", 40, "File validation completed successfully")
        
        # Generate response with file metadata
        upload_time = datetime.utcnow().isoformat() + "Z"
        
        response_data = {
            "status": "success",
            "message": "File processed successfully",
            "session_id": session_id,
            "file_info": {
                "filename": file.filename,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "content_type": file.content_type,
                "extension": file_extension,
                "upload_time": upload_time
            }
        }
        
        # Stage 2: File storage
        if store_file:
            await update_file_processing_progress(session_id, "storage", 50, "Storing file...")
            
            try:
                storage_info = await storage_service.store_file(
                    content=content,
                    original_filename=file.filename,
                    content_type=file.content_type,
                    metadata={
                        "upload_time": upload_time,
                        "client_ip": "unknown",  # TODO: Get actual client IP
                        "file_size": file_size,
                        "session_id": session_id
                    }
                )
                response_data["storage"] = storage_info
                response_data["message"] = "File uploaded and stored successfully"
                await update_file_processing_progress(session_id, "storage", 70, "File stored successfully")
                
            except HTTPException as e:
                await send_processing_error(session_id, f"Storage failed: {e.detail}", "STORAGE_ERROR")
                response_data["storage_error"] = e.detail
                response_data["message"] = "File processed but storage failed"
            except Exception as e:
                await send_processing_error(session_id, f"Unexpected storage error: {str(e)}", "STORAGE_EXCEPTION")
                response_data["storage_error"] = f"Unexpected storage error: {str(e)}"
                response_data["message"] = "File processed but storage failed"
        
        # Stage 3: Preview generation
        if include_preview:
            await update_file_processing_progress(session_id, "preview", 80, "Generating file preview...")
            
            try:
                preview = FileParserService.get_file_preview(
                    content=content,
                    filename=file.filename,
                    content_type=file.content_type,
                    preview_rows=preview_rows
                )
                response_data["preview"] = preview
                await update_file_processing_progress(session_id, "preview", 95, "Preview generated successfully")
                
            except HTTPException as e:
                await send_processing_error(session_id, f"Preview generation failed: {e.detail}", "PREVIEW_ERROR")
                response_data["preview_error"] = e.detail
                if "storage" not in response_data:
                    response_data["message"] = "File processed, but preview generation failed"
            except Exception as e:
                await send_processing_error(session_id, f"Unexpected error generating preview: {str(e)}", "PREVIEW_EXCEPTION")
                response_data["preview_error"] = f"Unexpected error generating preview: {str(e)}"
                if "storage" not in response_data:
                    response_data["message"] = "File processed, but preview generation failed"
        
        # Stage 4: Completion
        await update_file_processing_progress(session_id, "completed", 100, "File processing completed successfully")
        await send_processing_completion(session_id, response_data)
        
        # Use custom JSON encoder to handle NaN values
        try:
            json_content = json.dumps(response_data, cls=SmartJSONEncoder, ensure_ascii=False)
            
            return JSONResponse(
                status_code=200,
                content=json.loads(json_content),  # Parse back to dict for JSONResponse
                headers={"X-Session-ID": session_id}
            )
        except (ValueError, TypeError) as e:
            logger.error(f"JSON serialization error for session {session_id}: {str(e)}", exc_info=True)
            logger.error(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else type(response_data)}")
            
            # Try to send basic response without problematic data
            safe_response = {
                "status": "success",
                "message": "File uploaded successfully (preview data serialization failed)",
                "session_id": session_id
            }
            
            # Try to include safe parts of the response
            if "storage" in response_data:
                try:
                    safe_response["storage"] = json.loads(json.dumps(response_data["storage"], cls=SmartJSONEncoder))
                except:
                    pass
            
            try:
                await send_processing_error(session_id, f"JSON serialization error: {str(e)}", "SERIALIZATION_ERROR")
            except Exception as websocket_error:
                logger.warning(f"Failed to send serialization error via WebSocket: {websocket_error}")
            
            return JSONResponse(
                status_code=200,
                content=safe_response,
                headers={"X-Session-ID": session_id}
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already handled above)
        raise
    except Exception as e:
        # Handle unexpected errors with detailed logging
        logger.error(f"Unexpected error in file upload for session {session_id}: {str(e)}", exc_info=True)
        try:
            await send_processing_error(session_id, f"Unexpected error: {str(e)}", "UNEXPECTED_ERROR")
        except Exception as websocket_error:
            logger.warning(f"Failed to send error via WebSocket: {websocket_error}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/preview")
async def preview_file(
    file: UploadFile = File(...),
    preview_rows: int = Query(10, ge=1, le=100, description="Number of rows to include in preview")
):
    """
    Preview file content without uploading/storing it.
    
    Useful for quick file inspection before actual upload.
    Returns only the file preview and metadata.
    """
    
    # Basic file validation (same as upload)
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Content type not allowed. Received: {file.content_type}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file not allowed"
        )
    
    # Generate preview
    preview = FileParserService.get_file_preview(
        content=content,
        filename=file.filename,
        content_type=file.content_type,
        preview_rows=preview_rows
    )
    
    return {
        "status": "success",
        "message": "File preview generated successfully",
        "file_info": {
            "filename": file.filename,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "content_type": file.content_type,
            "extension": file_extension
        },
        "preview": preview
    }

@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Download a stored file.
    
    Args:
        file_path: Relative path to the file (e.g., "2024/01/15/filename.csv")
    """
    
    try:
        # Get file content
        file_content = await storage_service.get_file(file_path)
        
        # Get file metadata for proper headers
        try:
            metadata = await storage_service.get_file_metadata(file_path)
            content_type = metadata.get("content_type", "application/octet-stream")
            original_filename = metadata.get("original_filename", "download")
        except:
            # Fallback if metadata not available
            content_type = "application/octet-stream"
            original_filename = os.path.basename(file_path)
        
        # Create streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{original_filename}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get("/info/{file_path:path}")
async def get_file_info(file_path: str):
    """
    Get metadata for a stored file.
    
    Args:
        file_path: Relative path to the file
    """
    
    try:
        metadata = await storage_service.get_file_metadata(file_path)
        return {
            "status": "success",
            "file_info": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file info: {str(e)}"
        )

@router.get("/formats")
async def get_supported_formats():
    """
    Get list of supported file formats and size limits.
    """
    storage_info = storage_service.get_config_info()
    
    return {
        "supported_extensions": list(ALLOWED_EXTENSIONS),
        "supported_content_types": list(ALLOWED_CONTENT_TYPES),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "max_file_size_bytes": MAX_FILE_SIZE,
        "preview_options": {
            "default_preview_rows": 5,
            "max_preview_rows": 50,
            "supported_preview_formats": ["CSV", "Excel", "JSON"]
        },
        "storage": storage_info
    }


@router.post("/clean")
async def clean_file_data(
    file: Optional[UploadFile] = File(None),
    options: Optional[str] = Query(None, description="JSON string of cleaning options")
):
    """
    Cleans messy Excel/CSV data using the ExcelCleaningPipeline.
    Returns the comprehensive cleaning audit report, before/after preview, and cleaned records.
    Keeps the original uploaded file unchanged.
    """
    try:
        from backend.src.services.excel_cleaning_pipeline import ExcelCleaningPipeline

        parsed_options = {}
        if options:
            try:
                parsed_options = json.loads(options)
            except Exception:
                pass

        pipeline = ExcelCleaningPipeline(parsed_options)

        if file:
            content = await file.read()
            filename = file.filename or "dataset.xlsx"
            result = pipeline.process_file(content, filename=filename)
        else:
            raise HTTPException(status_code=400, detail="No file provided for cleaning")

        json_content = json.dumps(result, cls=SmartJSONEncoder, ensure_ascii=False)
        return JSONResponse(status_code=200, content=json.loads(json_content))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleaning error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Data cleaning failed: {str(e)}")


@router.post("/export-cleaned")
async def export_cleaned_excel(
    file: UploadFile = File(...),
    options: Optional[str] = Query(None)
):
    """
    Runs cleaning pipeline on file and exports a pristine, analytics-ready .xlsx file.
    Original file remains unchanged.
    """
    try:
        from backend.src.services.excel_cleaning_pipeline import ExcelCleaningPipeline
        import pandas as pd

        parsed_options = {}
        if options:
            try:
                parsed_options = json.loads(options)
            except Exception:
                pass

        content = await file.read()
        pipeline = ExcelCleaningPipeline(parsed_options)
        result = pipeline.process_file(content, filename=file.filename or "dataset.xlsx")

        if result.get("status") != "success":
            raise HTTPException(status_code=422, detail="Failed to clean dataset for export")

        cleaned_df = pd.DataFrame(result["cleaned_data"])
        output_stream = io.BytesIO()
        with pd.ExcelWriter(output_stream, engine='openpyxl') as writer:
            cleaned_df.to_excel(writer, index=False, sheet_name='Cleaned_Data')
        
        output_stream.seek(0)
        clean_filename = f"cleaned_{file.filename or 'dataset.xlsx'}"
        if not clean_filename.endswith('.xlsx'):
            clean_filename = os.path.splitext(clean_filename)[0] + '.xlsx'

        return StreamingResponse(
            output_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=\"{clean_filename}\""
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
