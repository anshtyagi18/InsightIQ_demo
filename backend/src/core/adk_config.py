"""
AI Configuration Module for InsightIQ
Manages configuration for Google Gemini models and AI analytics engines.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ADKConfig:
    """Configuration class for Google Gemini AI integration."""
    
    @property
    def gemini_api_key(self) -> Optional[str]:
        """Dynamic API key reading from environment variables."""
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    @property
    def google_api_key(self) -> Optional[str]:
        """Alias for gemini_api_key."""
        return self.gemini_api_key
    
    def __init__(self):
        """Initialize AI model configuration."""
        self.default_model = "gemini-3.8-flash"
        self.main_model = "gemini-3.8-flash"
        self.thinking_model = "gemini-2.5-pro"
        self.fallback_models = ["gemini-2.5-flash", "gemini-2.5-pro"]
        
        self.selected_main_model = self.main_model
        self.selected_fallback_models = self.fallback_models
        
        # Load provider configuration from provider_config.json if available
        self._load_provider_selection()
        
        # Default agent parameters
        self.agent_defaults = {
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9,
            "top_k": 40,
            "stream": False,
            "provider": "google"
        }
    
    def _load_provider_selection(self):
        """Load provider selection from configuration file."""
        try:
            config_file = Path("provider_config.json")
            if not config_file.exists():
                config_file = Path("backend/provider_config.json")
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    selection = config.get("selection", {})
                    models = config.get("models", {})
                    
                    main_model_id = selection.get("main_model")
                    if main_model_id and main_model_id in models:
                        main_model = models[main_model_id]
                        self.selected_main_model = main_model.get("id", self.main_model)
                        logger.info(f"Using selected main model: {self.selected_main_model}")
                    
                    fallback_model_id = selection.get("fallback_model")
                    if fallback_model_id and fallback_model_id in models:
                        fallback_model = models[fallback_model_id]
                        self.selected_fallback_models = [fallback_model.get("id", "gemini-2.5-pro")]
                        logger.info(f"Using selected fallback model: {self.selected_fallback_models}")
                    return
        except Exception as e:
            logger.warning(f"Could not load provider selection: {e}")
        
        self.selected_main_model = self.main_model
        self.selected_fallback_models = self.fallback_models
    
    def is_configured(self) -> bool:
        """Check if Gemini API key is available."""
        return bool(self.gemini_api_key)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        self._load_provider_selection()
        return {
            "model": self.selected_main_model,
            "api_key": self.gemini_api_key,
            "provider": "google",
            "fallback_models": self.selected_fallback_models
        }
    
    def get_agent_defaults(self) -> Dict[str, Any]:
        """Get default settings for agent initialization."""
        return self.agent_defaults.copy()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status."""
        has_key = bool(self.gemini_api_key)
        return {
            "has_api_key": has_key,
            "is_production_ready": has_key,
            "provider": "google",
            "main_model": self.selected_main_model,
            "fallback_count": len(self.selected_fallback_models)
        }

# Global configuration instance
adk_config = ADKConfig()

def get_default_model() -> str:
    """Get the default model name."""
    return adk_config.default_model

def get_main_model() -> str:
    """Get the main model name."""
    adk_config._load_provider_selection()
    return adk_config.selected_main_model

def get_thinking_model() -> str:
    """Get the thinking model name for complex tasks."""
    return adk_config.thinking_model

def get_fallback_models() -> List[str]:
    """Get the list of fallback models."""
    adk_config._load_provider_selection()
    return adk_config.selected_fallback_models

def is_production_ready() -> bool:
    """Check if configuration is ready for production use."""
    return adk_config.validate_config()["is_production_ready"]

def get_provider() -> str:
    """Get the current AI provider."""
    return "google"
