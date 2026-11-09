"""
AI Generation Service for InsightIQ
Unified interface for Google Gemini model interactions.
Supports model fallback, response caching, and structured output.
"""

import os
import asyncio
import logging
import hashlib
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.adk_config import adk_config, get_main_model, get_fallback_models

logger = logging.getLogger(__name__)

@dataclass
class ModelResponse:
    """Standardized response from AI models."""
    content: str
    model_used: str
    tokens_used: int = 0
    response_time: float = 0.0
    cached: bool = False
    fallback_used: bool = False
    error: Optional[str] = None

class LiteLLMService:
    """Service for handling AI model interactions through Gemini API."""
    
    def __init__(self):
        self.config = adk_config
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=1)
        self.model_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "fallback_usage": 0,
            "cache_hits": 0,
            "error_count": 0
        }
        
    def _get_cache_key(self, prompt: str, model: str, max_tokens: int) -> str:
        """Generate cache key for response caching."""
        content = f"{prompt}:{model}:{max_tokens}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if not cache_entry:
            return False
        timestamp = cache_entry.get("timestamp")
        if not timestamp:
            return False
        return datetime.now() - timestamp < self.cache_ttl
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_cache: bool = True,
        context: Optional[str] = None
    ) -> ModelResponse:
        """
        Generate AI response using Gemini API with fallback support.
        """
        start_time = time.time()
        self.model_stats["total_requests"] += 1
        
        target_model = model or get_main_model()
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(full_prompt, target_model, max_tokens)
            cached = self.response_cache.get(cache_key)
            if cached and self._is_cache_valid(cached):
                self.model_stats["cache_hits"] += 1
                return ModelResponse(
                    content=cached["content"],
                    model_used=cached["model"],
                    tokens_used=cached.get("tokens", 0),
                    response_time=time.time() - start_time,
                    cached=True
                )
        
        api_key = self.config.gemini_api_key
        if not api_key:
            return ModelResponse(
                content="Gemini API Key is not configured. Please set GEMINI_API_KEY.",
                model_used=target_model,
                tokens_used=0,
                response_time=time.time() - start_time,
                error="Missing GEMINI_API_KEY"
            )
        
        models_to_try = [target_model] + [m for m in get_fallback_models() if m != target_model]
        
        last_error = None
        for current_model in models_to_try:
            try:
                # Clean model name if it has prefixes
                clean_model_name = current_model.replace("gemini/", "").replace("google/", "")
                
                # Attempt generation using google-generativeai
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                gen_model = genai.GenerativeModel(
                    clean_model_name,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                
                # Run sync generate_content in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: gen_model.generate_content(full_prompt)
                )
                
                content = response.text if response and hasattr(response, 'text') else ""
                tokens_used = int(len(content.split()) * 1.3)
                elapsed = time.time() - start_time
                
                if use_cache:
                    cache_key = self._get_cache_key(full_prompt, current_model, max_tokens)
                    self.response_cache[cache_key] = {
                        "content": content,
                        "model": current_model,
                        "tokens": tokens_used,
                        "timestamp": datetime.now()
                    }
                
                self.model_stats["successful_requests"] += 1
                return ModelResponse(
                    content=content,
                    model_used=current_model,
                    tokens_used=tokens_used,
                    response_time=elapsed,
                    fallback_used=(current_model != target_model)
                )
            except Exception as e:
                logger.warning(f"Error calling {current_model}: {e}")
                last_error = str(e)
                continue
        
        self.model_stats["error_count"] += 1
        return ModelResponse(
            content=f"AI generation encountered an error: {last_error}",
            model_used=target_model,
            tokens_used=0,
            response_time=time.time() - start_time,
            error=last_error
        )

# Global service instance
litellm_service = LiteLLMService()

async def generate_ai_response(prompt: str, **kwargs) -> ModelResponse:
    return await litellm_service.generate(prompt, **kwargs)

async def generate_structured_ai_response(prompt: str, **kwargs) -> Dict[str, Any]:
    resp = await litellm_service.generate(prompt, **kwargs)
    import json
    try:
        return json.loads(resp.content)
    except Exception:
        return {"raw": resp.content}

