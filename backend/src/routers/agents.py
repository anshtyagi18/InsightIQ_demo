"""
Google ADK Agents Router

FastAPI router for integrating Google ADK agents with the Analytics Hub API.
Provides endpoints for agent-based data processing and analytics.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging
import json
import pandas as pd
import io
from datetime import datetime

from ..agents.orchestrator import AnalyticsOrchestrator
from ..agents.data_cleaner import DataCleanerAgent
from ..agents.enhanced_langgraph_orchestrator import EnhancedLangGraphOrchestrator
from ..core.adk_config import adk_config
from src.services.litellm_service import litellm_service
from src.core.adk_config import get_main_model, get_fallback_models, get_provider, get_litellm_config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agents", tags=["agents"])

# Global agent instances (initialized on first use)
_orchestrator = None
_data_cleaner = None
_enhanced_orchestrator = None


# Pydantic models for request/response
class FileAnalysisRequest(BaseModel):
    """Request model for file analysis."""
    file_info: Dict[str, Any] = Field(..., description="File information including type, size, columns, and preview data")


class FileAnalysisResponse(BaseModel):
    """Response model for file analysis."""
    status: str
    file_analysis: Dict[str, Any]
    processing_pipeline: List[str]
    complexity_score: int
    estimated_processing_time: int


class DataProcessingRequest(BaseModel):
    """Request model for data processing."""
    data: Dict[str, Any] = Field(..., description="Dataset to process")
    pipeline: List[str] = Field(..., description="Processing pipeline steps")


class DataProcessingResponse(BaseModel):
    """Response model for data processing."""
    status: str
    pipeline_executed: List[str]
    step_results: Dict[str, Any]
    processed_data: Dict[str, Any]
    recommendations: List[str]


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""
    status: str
    agents_available: List[str]
    configuration: Dict[str, Any]
    last_updated: str


def get_orchestrator() -> AnalyticsOrchestrator:
    """Get or create the analytics orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = AnalyticsOrchestrator()
            logger.info("Analytics Orchestrator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Analytics Orchestrator: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize analytics orchestrator")
    return _orchestrator


def get_data_cleaner() -> DataCleanerAgent:
    """Get or create the data cleaner agent."""
    global _data_cleaner
    if _data_cleaner is None:
        try:
            _data_cleaner = DataCleanerAgent()
            logger.info("Data Cleaner Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Data Cleaner Agent: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize data cleaner agent")
    return _data_cleaner


def get_enhanced_orchestrator() -> EnhancedLangGraphOrchestrator:
    """Get or create the enhanced LangGraph orchestrator."""
    global _enhanced_orchestrator
    if _enhanced_orchestrator is None:
        try:
            _enhanced_orchestrator = EnhancedLangGraphOrchestrator(
                model="openrouter/anthropic/claude-3-haiku",
                enable_state_persistence=True
            )
            logger.info("Enhanced LangGraph Orchestrator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced LangGraph Orchestrator: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize enhanced orchestrator")
    return _enhanced_orchestrator


def parse_uploaded_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Parse uploaded file and extract metadata for agent processing."""
    try:
        file_extension = filename.lower().split('.')[-1]
        
        # Determine file type and parse accordingly
        if file_extension in ['csv']:
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(file_content))
        elif file_extension == 'json':
            data = json.loads(file_content.decode('utf-8'))
            df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Extract file information for agent analysis
        file_info = {
            'type': file_extension,
            'size': len(file_content),
            'columns': df.columns.tolist(),
            'preview_rows': df.head(5).to_dict('records'),
            'total_rows': len(df),
            'filename': filename
        }
        
        return file_info
        
    except Exception as e:
        logger.error(f"Error parsing file {filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get the current status of all agents and their configuration."""
    try:
        # Check agent availability
        agents_available = []
        
        try:
            get_orchestrator()
            agents_available.append("analytics_orchestrator")
        except:
            pass
            
        try:
            get_data_cleaner()
            agents_available.append("data_cleaner")
        except:
            pass
        
        # Get configuration info
        config_validation = adk_config.validate_config()
        
        # Get appropriate API key status based on provider
        provider = config_validation.get("provider", "google")
        if provider == "openrouter":
            has_api_key = config_validation.get("has_openrouter_key", False)
            vertex_ai_enabled = False
        else:
            has_api_key = config_validation.get("has_api_key", False)
            vertex_ai_enabled = config_validation.get("vertex_ai_enabled", False)
        
        return AgentStatusResponse(
            status="operational" if agents_available else "offline",
            agents_available=agents_available,
            configuration={
                "model": adk_config.default_model,
                "provider": provider,
                "project_id": adk_config.project_id if provider == "google" else None,
                "has_api_key": has_api_key,
                "vertex_ai_enabled": vertex_ai_enabled,
                "is_production_ready": config_validation.get("is_production_ready", False)
            },
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")


@router.post("/analyze-file", response_model=FileAnalysisResponse)
async def analyze_file(request: FileAnalysisRequest):
    """Analyze uploaded file to determine processing requirements using the Analytics Orchestrator."""
    try:
        orchestrator = get_orchestrator()
        
        # Use the orchestrator's file analysis function
        from ..agents.orchestrator import analyze_file_requirements
        
        analysis_result = analyze_file_requirements(request.file_info)
        
        if analysis_result["status"] != "success":
            raise HTTPException(status_code=400, detail=analysis_result.get("message", "Analysis failed"))
        
        return FileAnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")


@router.post("/analyze-upload")
async def analyze_upload(file: UploadFile = File(...)):
    """Analyze an uploaded file directly and return processing recommendations."""
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse the file
        file_info = parse_uploaded_file(file_content, file.filename)
        
        # Analyze with orchestrator
        orchestrator = get_orchestrator()
        from ..agents.orchestrator import analyze_file_requirements
        
        analysis_result = analyze_file_requirements(file_info)
        
        if analysis_result["status"] != "success":
            raise HTTPException(status_code=400, detail=analysis_result.get("message", "Analysis failed"))
        
        # Add file info to response
        analysis_result["uploaded_file"] = {
            "filename": file.filename,
            "size_mb": round(len(file_content) / (1024 * 1024), 2),
            "columns": file_info["columns"],
            "sample_rows": file_info["total_rows"]
        }
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload analysis failed: {str(e)}")


@router.post("/process-data", response_model=DataProcessingResponse)
async def process_data(request: DataProcessingRequest, background_tasks: BackgroundTasks):
    """Process data using the specified pipeline and multiple agents."""
    try:
        orchestrator = get_orchestrator()
        
        # Use the orchestrator's data processing function
        from ..agents.orchestrator import orchestrate_data_processing
        
        processing_result = orchestrate_data_processing(request.data, request.pipeline)
        
        if processing_result["status"] != "success":
            raise HTTPException(status_code=400, detail=processing_result.get("message", "Processing failed"))
        
        return DataProcessingResponse(**processing_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise HTTPException(status_code=500, detail=f"Data processing failed: {str(e)}")


@router.post("/clean-data")
async def clean_data(request: Dict[str, Any]):
    """Clean data using the Data Cleaner Agent."""
    try:
        data_cleaner = get_data_cleaner()
        
        # Use data cleaner functions directly
        from ..agents.data_cleaner import detect_missing_values, detect_duplicates, validate_data_types
        
        cleaning_results = {
            "status": "success",
            "cleaning_steps": {},
            "recommendations": [],
            "quality_score": 0
        }
        
        # Run missing value analysis
        missing_result = detect_missing_values(request)
        if missing_result["status"] == "success":
            cleaning_results["cleaning_steps"]["missing_values"] = missing_result
            cleaning_results["recommendations"].extend(missing_result.get("recommendations", []))
        
        # Run duplicate analysis
        duplicate_result = detect_duplicates(request)
        if duplicate_result["status"] == "success":
            cleaning_results["cleaning_steps"]["duplicates"] = duplicate_result
            cleaning_results["recommendations"].extend(duplicate_result.get("recommendations", []))
        
        # Run data type validation
        validation_result = validate_data_types(request)
        if validation_result["status"] == "success":
            cleaning_results["cleaning_steps"]["data_types"] = validation_result
            cleaning_results["recommendations"].extend(validation_result.get("recommendations", []))
        
        # Calculate overall quality score (simple heuristic)
        quality_factors = []
        if missing_result.get("missing_percentage", 0) < 10:
            quality_factors.append(8)
        elif missing_result.get("missing_percentage", 0) < 25:
            quality_factors.append(6)
        else:
            quality_factors.append(4)
            
        if duplicate_result.get("duplicate_percentage", 0) < 5:
            quality_factors.append(9)
        elif duplicate_result.get("duplicate_percentage", 0) < 15:
            quality_factors.append(7)
        else:
            quality_factors.append(5)
            
        cleaning_results["quality_score"] = sum(quality_factors) / len(quality_factors) if quality_factors else 5
        
        return cleaning_results
        
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        raise HTTPException(status_code=500, detail=f"Data cleaning failed: {str(e)}")


@router.post("/generate-dashboard-plan")
async def generate_dashboard_plan(analysis_results: Dict[str, Any]):
    """Generate a dashboard plan based on analysis results."""
    try:
        orchestrator = get_orchestrator()
        
        # Use the orchestrator's dashboard planning function
        from ..agents.orchestrator import generate_dashboard_plan
        
        dashboard_result = generate_dashboard_plan(analysis_results)
        
        if dashboard_result["status"] != "success":
            raise HTTPException(status_code=400, detail=dashboard_result.get("message", "Dashboard planning failed"))
        
        return dashboard_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard plan: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard planning failed: {str(e)}")


# Health check endpoint for agents
@router.get("/health")
async def health_check():
    """Health check endpoint for the agents service."""
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "configuration": adk_config.is_configured(),
                "agents_importable": True,
                "api_endpoints": "operational"
            }
        }
        
        # Test agent initialization
        try:
            get_orchestrator()
            health_status["checks"]["orchestrator"] = True
        except:
            health_status["checks"]["orchestrator"] = False
            health_status["status"] = "degraded"
        
        try:
            get_data_cleaner()
            health_status["checks"]["data_cleaner"] = True
        except:
            health_status["checks"]["data_cleaner"] = False
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/models/status")
async def get_model_status():
    """Get current model configuration and status."""
    try:
        config = adk_config.get_model_config()
        validation = adk_config.validate_config()
        
        # Get LiteLLM service stats if available
        model_stats = {}
        if litellm_service.is_available():
            model_stats = litellm_service.get_model_stats()
        
        response = {
            "provider": get_provider(),
            "main_model": get_main_model(),
            "fallback_models": get_fallback_models(),
            "configuration": {
                "litellm_enabled": config.get("provider") == "litellm",
                "openrouter_configured": bool(adk_config.openrouter_api_key),
                "google_configured": bool(adk_config.google_api_key),
                "is_production_ready": validation.get("is_production_ready", False)
            },
            "validation": validation,
            "performance_stats": model_stats,
            "features": {
                "enhanced_analytics": True,
                "a2a_integration": True,
                "context7_integration": True,
                "response_caching": True,
                "model_fallback": True
            }
        }
        
        logger.info("Model status retrieved successfully")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get model status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/models/test")
async def test_model_connection():
    """Test connection to the configured AI models."""
    try:
        test_prompt = "Respond with 'OK' if you can process this request."
        
        if litellm_service.is_available():
            # Test LiteLLM service
            response = await litellm_service.generate_response(
                prompt=test_prompt,
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                "status": "success",
                "provider": get_provider(),
                "model_used": response.model_used,
                "response_time": response.response_time,
                "tokens_used": response.tokens_used,
                "cached": response.cached,
                "fallback_used": response.fallback_used,
                "test_response": response.content,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "unavailable",
                "provider": get_provider(),
                "message": "LiteLLM service not available. Check configuration.",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Model connection test failed: {str(e)}")
        return {
            "status": "error",
            "provider": get_provider(),
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/models/cache/clear")
async def clear_model_cache():
    """Clear the model response cache."""
    try:
        if litellm_service.is_available():
            litellm_service.clear_cache()
            return {
                "status": "success",
                "message": "Model cache cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "unavailable",
                "message": "LiteLLM service not available",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/models/config")
async def get_litellm_config():
    """Get LiteLLM configuration for external use."""
    try:
        config = get_litellm_config()
        
        if not config:
            return {
                "status": "unavailable",
                "message": "LiteLLM not configured",
                "provider": get_provider()
            }
        
        # Remove sensitive information
        safe_config = {
            "model_list": [
                {
                    "model_name": model["model_name"],
                    "model_type": model["litellm_params"]["model"],
                    "provider": "openrouter" if "openrouter" in model["litellm_params"]["model"] else "unknown"
                }
                for model in config.get("model_list", [])
            ],
            "general_settings": config.get("general_settings", {}),
            "litellm_settings": config.get("litellm_settings", {}),
            "provider": get_provider(),
            "main_model": get_main_model(),
            "fallback_models": get_fallback_models()
        }
        
        return safe_config
        
    except Exception as e:
        logger.error(f"Failed to get LiteLLM config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get LiteLLM config: {str(e)}")


# Enhanced LangGraph Orchestrator Endpoints
@router.get("/enhanced-orchestrator/status")
async def get_enhanced_orchestrator_status():
    """Get status of the Enhanced LangGraph Orchestrator."""
    try:
        orchestrator = get_enhanced_orchestrator()
        
        return {
            "status": "operational",
            "model": orchestrator.model,
            "state_persistence": orchestrator.enable_state_persistence,
            "openrouter_available": orchestrator.openrouter_config.is_available,
            "components": {
                "data_filter_agent": orchestrator.data_filter_agent is not None,
                "state_manager": orchestrator.state_manager is not None,
                "workflow": orchestrator.workflow is not None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhanced orchestrator status: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced orchestrator status failed: {str(e)}")


@router.post("/enhanced-orchestrator/process")
async def process_with_enhanced_orchestrator(
    original_data: Dict[str, Any],
    file_info: Optional[Dict[str, Any]] = None,
    user_requirements: Optional[Dict[str, Any]] = None
):
    """Process data using the Enhanced LangGraph Orchestrator."""
    try:
        orchestrator = get_enhanced_orchestrator()
        
        # Set default values if not provided
        if file_info is None:
            file_info = {
                "file_size": 1000,
                "num_rows": len(original_data.get("data", [])),
                "num_columns": len(original_data.get("columns", [])),
                "has_nulls": False,
                "has_duplicates": False,
                "data_types": ["string", "number"]
            }
        
        if user_requirements is None:
            user_requirements = {
                "chart_types": ["bar", "line"],
                "filters": []
            }
        
        # Execute the enhanced workflow
        result = await orchestrator.execute_enhanced_workflow(
            original_data=original_data,
            file_info=file_info,
            user_requirements=user_requirements
        )
        
        return {
            "status": "success",
            "workflow_id": result.get("workflow_id"),
            "processing_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enhanced orchestrator processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/enhanced-orchestrator/test")
async def test_enhanced_orchestrator():
    """Test the Enhanced LangGraph Orchestrator with sample data."""
    try:
        orchestrator = get_enhanced_orchestrator()
        
        # Sample test data
        sample_data = {
            "columns": ["id", "name", "age", "salary", "department"],
            "data": [
                [1, "John Doe", 30, 75000, "Engineering"],
                [2, "Jane Smith", 28, 65000, "Marketing"],
                [3, "Bob Johnson", 35, 85000, "Engineering"]
            ]
        }
        
        sample_file_info = {
            "file_size": 1000,
            "num_rows": 3,
            "num_columns": 5,
            "has_nulls": False,
            "has_duplicates": False,
            "data_types": ["int", "string", "int", "int", "string"]
        }
        
        # Test data filtering
        filter_agent = orchestrator.data_filter_agent
        filtering_result = filter_agent._fallback_filtering(sample_data)
        
        # Test complexity calculation
        complexity = orchestrator._calculate_data_complexity(sample_file_info)
        
        return {
            "status": "success",
            "test_results": {
                "orchestrator_initialized": True,
                "data_filtering": {
                    "relevant_columns": filtering_result.relevant_columns,
                    "irrelevant_columns": filtering_result.irrelevant_columns,
                    "metadata_columns": filtering_result.metadata_columns,
                    "confidence_score": filtering_result.confidence_score
                },
                "complexity_score": complexity,
                "openrouter_available": orchestrator.openrouter_config.is_available,
                "workflow_ready": orchestrator.workflow is not None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enhanced orchestrator test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/enhanced-orchestrator/analyze-upload")
async def analyze_upload_enhanced(file: UploadFile = File(...)):
    """Analyze uploaded file using the Enhanced LangGraph Orchestrator."""
    try:
        orchestrator = get_enhanced_orchestrator()
        
        # Read and parse the file
        content = await file.read()
        file_info = parse_uploaded_file(content, file.filename)
        
        # Convert file data to the format expected by the orchestrator
        if file_info["type"] in ["csv", "xlsx", "xls"]:
            # Parse the actual data
            if file_info["type"] == "csv":
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
            
            original_data = {
                "columns": df.columns.tolist(),
                "data": df.values.tolist()
            }
        else:
            original_data = {
                "columns": file_info["columns"],
                "data": file_info["preview_rows"]
            }
        
        # Enhanced file info
        enhanced_file_info = {
            "file_size": file_info["size"],
            "num_rows": file_info["total_rows"],
            "num_columns": len(file_info["columns"]),
            "has_nulls": df.isnull().any().any() if "df" in locals() else False,
            "has_duplicates": df.duplicated().any() if "df" in locals() else False,
            "data_types": [str(dtype) for dtype in df.dtypes] if "df" in locals() else ["unknown"]
        }
        
        # Use the orchestrator for analysis
        filter_agent = orchestrator.data_filter_agent
        filtering_result = filter_agent._fallback_filtering(original_data)
        complexity = orchestrator._calculate_data_complexity(enhanced_file_info)
        
        return {
            "status": "success",
            "file_analysis": {
                "filename": file.filename,
                "file_info": enhanced_file_info,
                "data_filtering": {
                    "relevant_columns": filtering_result.relevant_columns,
                    "irrelevant_columns": filtering_result.irrelevant_columns,
                    "metadata_columns": filtering_result.metadata_columns,
                    "confidence_score": filtering_result.confidence_score,
                    "reasoning": filtering_result.reasoning
                },
                "complexity_score": complexity,
                "recommendations": [
                    "Use relevant columns for analytics calculations",
                    "Consider removing irrelevant columns to improve performance",
                    "Metadata columns can be used for filtering and grouping"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enhanced orchestrator upload analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload analysis failed: {str(e)}") 