"""Tests for the configuration module."""

import pytest
from src.config import Settings, get_settings


def test_settings_defaults():
    """Test that settings have correct default values."""
    settings = Settings()
    
    assert settings.mcp_server_host == "localhost"
    assert settings.mcp_server_port == 3000
    assert settings.ollama_host == "http://localhost:11434"
    assert settings.ollama_model == "mistral"
    assert settings.log_level == "INFO"


def test_get_settings():
    """Test that get_settings returns the global instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2
    assert isinstance(settings1, Settings)


def test_settings_env_override(monkeypatch):
    """Test that environment variables override defaults."""
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    settings = Settings()
    
    assert settings.ollama_model == "mistral"
    assert settings.log_level == "DEBUG"
