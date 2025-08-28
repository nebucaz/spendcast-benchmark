"""Configuration management for the chatbot application."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MCP Server Configuration
    mcp_server_host: str = Field(default="localhost")
    mcp_server_port: int = Field(default=3000)
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="mistral")
    
    # GraphDB Configuration (for Story 1.2)
    graphdb_url: str = Field(default="http://localhost:7200/repositories/demo")
    graphdb_user: str = Field(default="bernhaeckt")
    graphdb_password: str = Field(default="bernhaeckt")
    
    # Logging Configuration
    log_level: str = Field(default="INFO")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="",
        extra="ignore"
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
