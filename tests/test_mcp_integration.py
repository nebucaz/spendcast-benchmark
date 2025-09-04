"""Tests for MCP integration functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from src.mcp_client import MCPClient, MCPServerConfig
from src.mcp_server_manager import MCPServerManager


class TestMCPServerConfig:
    """Test cases for MCP server configuration."""
    
    def test_mcp_server_config_initialization(self):
        """Test MCP server configuration initialization."""
        config_data = {
            "command": "python",
            "args": ["-m", "spendcast_mcp"],
            "env": {"TEST": "value"}
        }
        
        config = MCPServerConfig("test-server", config_data)
        
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.args == ["-m", "spendcast_mcp"]
        assert config.env == {"TEST": "value"}
    
    def test_mcp_server_config_defaults(self):
        """Test MCP server configuration with default values."""
        config_data = {}
        
        config = MCPServerConfig("test-server", config_data)
        
        assert config.name == "test-server"
        assert config.command == ""
        assert config.args == []
        assert config.env == {}


class TestMCPClient:
    """Test cases for MCP client functionality."""
    
    @pytest.fixture
    def mcp_client(self):
        """Create an MCP client instance for testing."""
        return MCPClient()
    
    def test_mcp_client_initialization(self, mcp_client):
        """Test MCP client initialization."""
        assert mcp_client.session is None
        assert mcp_client.tools == []
        assert mcp_client.server_process is None
        assert mcp_client.server_config is None
    
    def test_get_available_tools_empty(self, mcp_client):
        """Test getting available tools when none are loaded."""
        tools = mcp_client.get_available_tools()
        assert tools == []
    
    def test_get_tool_descriptions_empty(self, mcp_client):
        """Test getting tool descriptions when none are loaded."""
        descriptions = mcp_client.get_tool_descriptions()
        assert descriptions == {}
    
    def test_get_available_tools_with_mock_tools(self, mcp_client):
        """Test getting available tools when tools are loaded."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "First tool"
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Second tool"
        
        mcp_client.tools = [mock_tool1, mock_tool2]
        
        tools = mcp_client.get_available_tools()
        assert tools == ["tool1", "tool2"]
    
    def test_get_tool_descriptions_with_mock_tools(self, mcp_client):
        """Test getting tool descriptions when tools are loaded."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "First tool"
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Second tool"
        
        mcp_client.tools = [mock_tool1, mock_tool2]
        
        descriptions = mcp_client.get_tool_descriptions()
        expected = {"tool1": "First tool", "tool2": "Second tool"}
        assert descriptions == expected
    
    @pytest.mark.asyncio
    async def test_connect_no_config(self, mcp_client):
        """Test connection attempt without configuration."""
        result = await mcp_client.connect()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self, mcp_client):
        """Test listing tools when not connected."""
        tools = await mcp_client.list_tools()
        assert tools == []
    
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, mcp_client):
        """Test calling tool when not connected."""
        result = await mcp_client.call_tool("test_tool", {})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, mcp_client):
        """Test disconnect cleanup."""
        # Mock session and process
        mock_session = AsyncMock()
        mock_process = Mock()
        
        mcp_client.session = mock_session
        mcp_client.server_process = mock_process
        
        await mcp_client.disconnect()
        
        mock_session.aclose.assert_called_once()
        mock_process.terminate.assert_called_once()
        assert mcp_client.session is None
        assert mcp_client.server_process is None


class TestMCPIntegration:
    """Test cases for MCP integration with real configuration."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample MCP configuration for testing."""
        return {
            "mcpServers": {
                "spendcast-graphdb": {
                    "command": "python",
                    "args": ["-m", "spendcast_mcp"],
                    "env": {
                        "GRAPHDB_URL": "http://localhost:7200/repositories/demo",
                        "GRAPHDB_USER": "test_user",
                        "GRAPHDB_PASSWORD": "test_password"
                    }
                }
            }
        }
    
    def test_mcp_client_with_real_config(self, sample_config):
        """Test MCP client with real configuration data."""
        config_data = sample_config["mcpServers"]["spendcast-graphdb"]
        config = MCPServerConfig("spendcast-graphdb", config_data)
        
        assert config.name == "spendcast-graphdb"
        assert config.command == "python"
        assert config.args == ["-m", "spendcast_mcp"]
        assert "GRAPHDB_URL" in config.env
        assert "GRAPHDB_USER" in config.env
        assert "GRAPHDB_PASSWORD" in config.env
    
    def test_configuration_values(self, sample_config):
        """Test that configuration values are correctly set."""
        config_data = sample_config["mcpServers"]["spendcast-graphdb"]
        config = MCPServerConfig("spendcast-graphdb", config_data)
        
        assert config.env["GRAPHDB_URL"] == "http://localhost:7200/repositories/demo"
        assert config.env["GRAPHDB_USER"] == "test_user"
        assert config.env["GRAPHDB_PASSWORD"] == "test_password"

