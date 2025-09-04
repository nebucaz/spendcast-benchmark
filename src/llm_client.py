"""LLM client for Ollama integration and local model interaction."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from pydantic import BaseModel

from .config import get_settings

logger = logging.getLogger(__name__)


class LLMRequest(BaseModel):
    """Request model for LLM interactions."""
    model: str
    prompt: str
    stream: bool = False
    options: Optional[Dict[str, Any]] = None


class LLMResponse(BaseModel):
    """Response model from LLM interactions."""
    response: str
    model: str
    done: bool = True
    total_duration: Optional[int] = None


class OllamaClient:
    """Client for interacting with Ollama local LLM service."""
    
    def __init__(self):
        """Initialize the Ollama client."""
        self.settings = get_settings()
        self.base_url = self.settings.ollama_host
        self.default_model = self.settings.ollama_model
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"Found {len(models)} models: {models}")
                return models
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def generate(self, prompt: str, model: Optional[str] = None) -> Optional[LLMResponse]:
        """Generate a response from the LLM."""
        if not model:
            model = self.default_model
            
        request_data = LLMRequest(
            model=model,
            prompt=prompt,
            stream=False
        )
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=request_data.model_dump()
            )
            
            if response.status_code == 200:
                data = response.json()
                return LLMResponse(
                    response=data.get("response", ""),
                    model=data.get("model", model),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration")
                )
            else:
                logger.error(f"LLM generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None
    
    async def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available."""
        models = await self.list_models()
        return model in models
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama hub."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {model}")
                return True
            else:
                logger.error(f"Failed to pull model {model}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class LLMClient:
    """High-level LLM client for generating responses."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.ollama = OllamaClient()
        
    async def setup(self):
        """Set up the LLM client and check model availability."""
        # Get available models from Ollama
        available_models = await self.ollama.list_models()
        
        if not available_models:
            logger.error("No models available on Ollama server")
            return False
        
        # Check if default model is available
        if self.ollama.default_model in available_models:
            logger.info(f"Using default model: {self.ollama.default_model}")
        else:
            # Use first available model
            self.ollama.default_model = available_models[0]
            logger.info(f"Default model not available, using: {self.ollama.default_model}")
        
        logger.info(f"LLM client ready with model: {self.ollama.default_model}")
        return True
    
    async def generate_response(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Generate a response from the LLM."""
        response = await self.ollama.generate(prompt, model)
        if response:
            return response.response
        return None
    
    async def close(self):
        """Close the LLM client."""
        await self.ollama.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
