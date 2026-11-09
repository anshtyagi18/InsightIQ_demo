"""
FastAPI router for AI provider and model management.
Handles configuration of different AI providers including OpenRouter, Google, A4F, etc.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# from ..auth import User, get_current_user, require_permission, Permission
from ..core.adk_config import adk_config, get_main_model, get_fallback_models
from ..services.litellm_service import litellm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])

# Provider and Model Configuration Models
class Provider(BaseModel):
    """Provider configuration model."""
    id: str = Field(..., description="Provider unique identifier")
    name: str = Field(..., description="Provider display name")
    base_url: str = Field(..., description="Provider API base URL")
    api_key_env: str = Field(..., description="Environment variable name for API key")
    description: Optional[str] = Field(None, description="Provider description")
    enabled: bool = Field(True, description="Whether provider is enabled")
    supports_streaming: bool = Field(False, description="Whether provider supports streaming")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limit configuration")

class Model(BaseModel):
    """Model configuration model."""
    id: str = Field(..., description="Model unique identifier")
    name: str = Field(..., description="Model display name")
    provider_id: str = Field(..., description="Provider ID this model belongs to")
    litellm_model: str = Field(..., description="LiteLLM model identifier")
    context_length: int = Field(4096, description="Maximum context length")
    input_cost_per_token: float = Field(0.0, description="Input cost per token in USD")
    output_cost_per_token: float = Field(0.0, description="Output cost per token in USD")
    supports_functions: bool = Field(False, description="Whether model supports function calling")
    description: Optional[str] = Field(None, description="Model description")
    enabled: bool = Field(True, description="Whether model is enabled")

class ProviderUpdate(BaseModel):
    """Provider update request model."""
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

class ModelUpdate(BaseModel):
    """Model update request model."""
    name: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_token: Optional[float] = None
    output_cost_per_token: Optional[float] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

class ProviderSelection(BaseModel):
    """Current provider selection model."""
    main_provider: str = Field(..., description="Main provider ID")
    main_model: str = Field(..., description="Main model ID")
    fallback_provider: Optional[str] = Field(None, description="Fallback provider ID")
    fallback_model: Optional[str] = Field(None, description="Fallback model ID")
    research_provider: Optional[str] = Field(None, description="Research provider ID")
    research_model: Optional[str] = Field(None, description="Research model ID")

class ApiKeyUpdate(BaseModel):
    """API key update request model."""
    api_key: str = Field(..., description="The API key value")
    validate_key: bool = Field(default=False, description="Whether to validate the API key")

# Default provider configurations
DEFAULT_PROVIDERS = {
    "google": {
        "id": "google",
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "api_key_env": "GEMINI_API_KEY",
        "description": "Google's state-of-the-art Gemini models",
        "enabled": True,
        "supports_streaming": True,
        "rate_limit": {"requests_per_minute": 60}
    }
}

DEFAULT_MODELS = {
    "gemini-2.5-flash": {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider_id": "google",
        "litellm_model": "gemini/gemini-2.5-flash",
        "context_length": 1048576,
        "input_cost_per_token": 0.0000001875,
        "output_cost_per_token": 0.00000075,
        "supports_functions": True,
        "description": "Google's fast, high-performance Gemini 2.5 Flash model"
    },
    "gemini-2.5-pro": {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider_id": "google",
        "litellm_model": "gemini/gemini-2.5-pro",
        "context_length": 2097152,
        "input_cost_per_token": 0.00000125,
        "output_cost_per_token": 0.000005,
        "supports_functions": True,
        "description": "Google's advanced reasoning Gemini 2.5 Pro model"
    },
    "gemini-1.5-flash": {
        "id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "provider_id": "google",
        "litellm_model": "gemini/gemini-1.5-flash",
        "context_length": 1048576,
        "input_cost_per_token": 0.000000075,
        "output_cost_per_token": 0.0000003,
        "supports_functions": True,
        "description": "Google's fast and cost-efficient Gemini 1.5 Flash model"
    },
    "gemini-1.5-pro": {
        "id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "provider_id": "google",
        "litellm_model": "gemini/gemini-1.5-pro",
        "context_length": 2097152,
        "input_cost_per_token": 0.00000125,
        "output_cost_per_token": 0.000005,
        "supports_functions": True,
        "description": "Google's multimodal reasoning Gemini 1.5 Pro model"
    }
}

def get_config_file_path() -> Path:
    """Get the path to the provider configuration file."""
    p = Path("provider_config.json")
    if not p.exists():
        p = Path("backend/provider_config.json")
    return p

def load_provider_config() -> Dict[str, Any]:
    """Load provider configuration from file."""
    config_file = get_config_file_path()
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load provider config: {e}")
    
    # Return default configuration
    return {
        "providers": DEFAULT_PROVIDERS,
        "models": DEFAULT_MODELS,
        "selection": {
            "main_provider": "google",
            "main_model": "gemini-2.5-flash",
            "fallback_provider": "google",
            "fallback_model": "gemini-2.5-pro",
            "research_provider": "google",
            "research_model": "gemini-2.5-pro"
        }
    }

def save_provider_config(config: Dict[str, Any]) -> None:
    """Save provider configuration to file."""
    config_file = get_config_file_path()
    
    # Add timestamp
    config["last_updated"] = datetime.utcnow().isoformat()
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save provider config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@router.get("/")
async def list_providers():
    """Get all available providers."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        
        # Add API key status for each provider
        for provider_id, provider in providers.items():
            api_key_env = provider.get("api_key_env")
            provider["api_key_configured"] = bool(os.getenv(api_key_env)) if api_key_env else False
        
        return JSONResponse(content={
            "status": "success",
            "providers": providers
        })
        
    except Exception as e:
        logger.error(f"Failed to list providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")

@router.get("/models")
async def list_models(provider_id: Optional[str] = None):
    """Get all available models, optionally filtered by provider."""
    try:
        config = load_provider_config()
        models = config.get("models", {})
        
        if provider_id:
            models = {
                model_id: model for model_id, model in models.items()
                if model.get("provider_id") == provider_id
            }
        
        return JSONResponse(content={
            "status": "success",
            "models": models
        })
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.get("/selection")
async def get_current_selection():
    """Get current provider and model selection."""
    try:
        config = load_provider_config()
        selection = config.get("selection", {})
        
        return JSONResponse(content={
            "status": "success",
            "selection": selection
        })
        
    except Exception as e:
        logger.error(f"Failed to get current selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get current selection: {str(e)}")

@router.put("/selection")
async def update_selection(selection: ProviderSelection):
    """Update current provider and model selection."""
    try:
        config = load_provider_config()
        
        # Validate providers and models exist
        providers = config.get("providers", {})
        models = config.get("models", {})
        
        if selection.main_provider not in providers:
            raise HTTPException(status_code=400, detail=f"Provider {selection.main_provider} not found")
        if selection.main_model not in models:
            raise HTTPException(status_code=400, detail=f"Model {selection.main_model} not found")
        
        # Update selection
        config["selection"] = selection.dict()
        save_provider_config(config)
        
        # Reload ADK configuration to use new selection
        try:
            adk_config._load_provider_selection()
            logger.info(f"ADK configuration reloaded with new selection: {selection.main_model}")
        except Exception as e:
            logger.warning(f"Failed to reload ADK configuration: {e}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Provider selection updated successfully",
            "selection": selection.dict()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update selection: {str(e)}")

@router.post("/providers")
async def add_provider(provider: Provider):
    """Add a new provider."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        
        if provider.id in providers:
            raise HTTPException(status_code=400, detail=f"Provider {provider.id} already exists")
        
        providers[provider.id] = provider.dict()
        config["providers"] = providers
        save_provider_config(config)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Provider {provider.id} added successfully",
            "provider": provider.dict()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add provider: {str(e)}")

@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, update: ProviderUpdate):
    """Update an existing provider."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        
        if provider_id not in providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        # Update only provided fields
        provider = providers[provider_id]
        update_data = update.dict(exclude_unset=True)
        provider.update(update_data)
        
        save_provider_config(config)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Provider {provider_id} updated successfully",
            "provider": provider
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update provider: {str(e)}")

@router.post("/models")
async def add_model(model: Model):
    """Add a new model."""
    try:
        config = load_provider_config()
        models = config.get("models", {})
        providers = config.get("providers", {})
        
        if model.id in models:
            raise HTTPException(status_code=400, detail=f"Model {model.id} already exists")
        
        if model.provider_id not in providers:
            raise HTTPException(status_code=400, detail=f"Provider {model.provider_id} not found")
        
        models[model.id] = model.dict()
        config["models"] = models
        save_provider_config(config)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Model {model.id} added successfully",
            "model": model.dict()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add model: {str(e)}")

@router.put("/models/{model_id}")
async def update_model(model_id: str, update: ModelUpdate):
    """Update an existing model."""
    try:
        config = load_provider_config()
        models = config.get("models", {})
        
        if model_id not in models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Update only provided fields
        model = models[model_id]
        update_data = update.dict(exclude_unset=True)
        model.update(update_data)
        
        save_provider_config(config)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Model {model_id} updated successfully",
            "model": model
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update model: {str(e)}")

@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """Delete a provider and all its models."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        models = config.get("models", {})
        
        if provider_id not in providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        # Remove provider
        del providers[provider_id]
        
        # Remove all models for this provider
        models_to_remove = [
            model_id for model_id, model in models.items()
            if model.get("provider_id") == provider_id
        ]
        
        for model_id in models_to_remove:
            del models[model_id]
        
        config["providers"] = providers
        config["models"] = models
        save_provider_config(config)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Provider {provider_id} and {len(models_to_remove)} models deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete provider: {str(e)}")

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """Delete a model."""
    try:
        config = load_provider_config()
        models = config.get("models", {})
        
        if model_id not in models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        del models[model_id]
        config["models"] = models
        save_provider_config(config)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Model {model_id} deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

@router.post("/test/{provider_id}")
async def test_provider(provider_id: str):
    """Test connection to a specific provider."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        
        if provider_id not in providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        provider = providers[provider_id]
        api_key_env = provider.get("api_key_env")
        api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not api_key:
            return JSONResponse(content={
                "status": "error",
                "message": f"API key not configured for {provider_id}",
                "provider": provider_id
            })
        
        # For now, just return success if API key is configured
        # TODO: Implement actual API testing
        return JSONResponse(content={
            "status": "success",
            "message": f"Provider {provider_id} is configured and ready",
            "provider": provider_id,
            "api_key_configured": True
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test provider: {str(e)}")

@router.get("/status")
async def get_provider_status():
    """Get overall provider status and statistics."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        models = config.get("models", {})
        selection = config.get("selection", {})
        
        # Count enabled providers and models
        enabled_providers = sum(1 for p in providers.values() if p.get("enabled", True))
        enabled_models = sum(1 for m in models.values() if m.get("enabled", True))
        
        # Check API key configuration
        configured_providers = 0
        for provider in providers.values():
            api_key_env = provider.get("api_key_env")
            if api_key_env and os.getenv(api_key_env):
                configured_providers += 1
        
        # Get current AI configuration
        try:
            adk_model_config = adk_config.get_model_config()
            ai_config = {
                "main_model": adk_model_config.get("model"),
                "fallback_models": adk_model_config.get("fallback_models"),
                "provider": adk_model_config.get("provider")
            }
        except Exception as e:
            logger.warning(f"Could not get AI configuration: {e}")
            ai_config = {"error": "Could not load AI configuration"}
        
        return JSONResponse(content={
            "status": "success",
            "statistics": {
                "total_providers": len(providers),
                "enabled_providers": enabled_providers,
                "configured_providers": configured_providers,
                "total_models": len(models),
                "enabled_models": enabled_models
            },
            "current_selection": selection,
            "active_ai_config": ai_config,
            "health": {
                "configuration_file": get_config_file_path().exists(),
                "main_provider_configured": bool(
                    selection.get("main_provider") and 
                    selection.get("main_provider") in providers and
                    os.getenv(providers[selection.get("main_provider", {})].get("api_key_env", ""))
                )
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get provider status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")

@router.get("/ai-config")
async def get_ai_configuration():
    """Get current AI configuration that agents are using."""
    try:
        # Force reload of provider selection
        adk_config._load_provider_selection()
        
        model_config = adk_config.get_model_config()
        
        return JSONResponse(content={
            "status": "success",
            "ai_configuration": {
                "main_model": model_config.get("model"),
                "fallback_models": model_config.get("fallback_models", []),
                "provider": model_config.get("provider"),
                "base_url": model_config.get("base_url"),
                "litellm_enabled": adk_config.use_litellm,
                "selected_main_model": getattr(adk_config, 'selected_main_model', 'Not set'),
                "selected_fallback_models": getattr(adk_config, 'selected_fallback_models', [])
            },
            "utility_functions": {
                "get_main_model": get_main_model(),
                "get_fallback_models": get_fallback_models()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get AI configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI configuration: {str(e)}")

@router.put("/{provider_id}/api-key")
async def update_provider_api_key(provider_id: str, update: ApiKeyUpdate):
    """Update API key for a specific provider."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        
        if provider_id not in providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        provider = providers[provider_id]
        api_key_env = provider.get("api_key_env")
        
        if not api_key_env:
            raise HTTPException(status_code=400, detail=f"Provider {provider_id} does not have an API key environment variable configured")
        
        # Update the environment variable
        os.environ[api_key_env] = update.api_key
        
        # Update provider configuration to mark as configured
        provider["api_key_configured"] = True
        save_provider_config(config)
        
        # Optional: Validate the API key if requested
        validation_result = None
        if update.validate_key:
            try:
                # Basic validation - attempt to use the key
                validation_result = await validate_api_key(provider_id, update.api_key)
            except Exception as e:
                logger.warning(f"API key validation failed for {provider_id}: {e}")
                validation_result = {
                    "valid": False,
                    "error": str(e)
                }
        
        return JSONResponse(content={
            "status": "success",
            "message": f"API key updated successfully for {provider_id}",
            "provider": provider_id,
            "api_key_configured": True,
            "validation": validation_result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update API key for {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")

async def validate_api_key(provider_id: str, api_key: str) -> Dict[str, Any]:
    """Validate an API key for a specific provider."""
    try:
        if provider_id == "openrouter":
            # Test OpenRouter API key
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://insightiq.app",
                        "X-Title": "InsightIQ"
                    },
                    timeout=10.0
                )
                return {
                    "valid": response.status_code == 200,
                    "status_code": response.status_code,
                    "message": "API key is valid" if response.status_code == 200 else "API key validation failed"
                }
        
        elif provider_id == "google":
            # Test Google API key
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                    timeout=10.0
                )
                return {
                    "valid": response.status_code == 200,
                    "status_code": response.status_code,
                    "message": "API key is valid" if response.status_code == 200 else "API key validation failed"
                }
        
        elif provider_id == "a4f":
            # Test A4F API key
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.a4f.co/v1/models",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    timeout=10.0
                )
                return {
                    "valid": response.status_code == 200,
                    "status_code": response.status_code,
                    "message": "API key is valid" if response.status_code == 200 else "API key validation failed"
                }
        
        else:
            return {
                "valid": True,
                "message": f"Validation not implemented for {provider_id}"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "message": f"Validation failed: {str(e)}"
        }

@router.get("/{provider_id}/api-key/status")
async def get_api_key_status(provider_id: str):
    """Get API key status for a specific provider."""
    try:
        config = load_provider_config()
        providers = config.get("providers", {})
        
        if provider_id not in providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        provider = providers[provider_id]
        api_key_env = provider.get("api_key_env")
        
        if not api_key_env:
            return JSONResponse(content={
                "status": "success",
                "provider": provider_id,
                "api_key_configured": False,
                "api_key_env": None,
                "message": "Provider does not require API key"
            })
        
        api_key_configured = bool(os.getenv(api_key_env))
        
        return JSONResponse(content={
            "status": "success",
            "provider": provider_id,
            "api_key_configured": api_key_configured,
            "api_key_env": api_key_env,
            "message": "API key is configured" if api_key_configured else "API key is not configured"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API key status for {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get API key status: {str(e)}") 