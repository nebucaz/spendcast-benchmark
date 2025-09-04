"""Tests for MCP Server Manager functionality."""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from src.mcp_server_manager import MCPServerManager, MCPServerConfig


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


class TestMCPServerManager:
    """Test cases for MCP server manager functionality."""
    
    @pytest.fixture
    def mcp_manager(self):
        """Create an MCP server manager instance for testing."""
        return MCPServerManager()
    
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
                },
                "another-server": {
                    "command": "uv",
                    "args": ["run", "server"],
                    "env": {"API_KEY": "test_key"}
                }
            }
        }
    
    def test_mcp_manager_initialization(self, mcp_manager):
        """Test MCP server manager initialization."""
        assert mcp_manager.servers == {}
        assert mcp_manager.server_configs == {}
        assert mcp_manager.available_tools == []
        assert mcp_manager.available_resources == []
    
    def test_load_mcp_config_success(self, mcp_manager, sample_config):
        """Test successful loading of MCP configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            config_path = f.name
        
        try:
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', create=True) as mock_open:
                
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(sample_config)
                
                configs = mcp_manager._load_mcp_config()
                
                assert len(configs) == 2
                assert "spendcast-graphdb" in configs
                assert "another-server" in configs
                
                spendcast_config = configs["spendcast-graphdb"]
                assert spendcast_config.command == "python"
                assert spendcast_config.args == ["-m", "spendcast_mcp"]
                assert "GRAPHDB_URL" in spendcast_config.env
        finally:
            Path(config_path).unlink()
    
    def test_load_mcp_config_file_not_found(self, mcp_manager):
        """Test loading MCP configuration when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            configs = mcp_manager._load_mcp_config()
            assert configs == {}
    
    def test_load_mcp_config_empty_servers(self, mcp_manager):
        """Test loading MCP configuration with empty servers."""
        empty_config = {"mcpServers": {}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_config, f)
            config_path = f.name
        
        try:
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('builtins.open', create=True) as mock_open:
                
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(empty_config)
                
                configs = mcp_manager._load_mcp_config()
                assert configs == {}
        finally:
            Path(config_path).unlink()
    
    @pytest.mark.asyncio
    async def test_start_all_servers_success(self, mcp_manager, sample_config):
        """Test successful startup of all MCP servers."""
        with patch.object(mcp_manager, '_load_mcp_config', return_value={
            "server1": MCPServerConfig("server1", sample_config["mcpServers"]["spendcast-graphdb"]),
            "server2": MCPServerConfig("server2", sample_config["mcpServers"]["another-server"])
        }), \
        patch('src.mcp_server_manager.MCPClient') as mock_mcp_client_class:
            
            # Mock successful connections
            mock_client1 = AsyncMock()
            mock_client1.connect = AsyncMock(return_value=True)
            mock_client1.list_tools = AsyncMock(return_value=[])
            
            mock_client2 = AsyncMock()
            mock_client2.connect = AsyncMock(return_value=True)
            mock_client2.list_tools = AsyncMock(return_value=[])
            
            mock_mcp_client_class.side_effect = [mock_client1, mock_client2]
            
            # Test startup
            result = await mcp_manager.start_all_servers()
            
            assert result is True
            assert len(mcp_manager.servers) == 2
            assert "server1" in mcp_manager.servers
            assert "server2" in mcp_manager.servers
    
    @pytest.mark.asyncio
    async def test_start_all_servers_failure(self, mcp_manager):
        """Test startup failure when no servers are configured."""
        with patch.object(mcp_manager, '_load_mcp_config', return_value={}):
            result = await mcp_manager.start_all_servers()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_all_servers(self, mcp_manager):
        """Test stopping all MCP servers."""
        # Mock servers
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        
        mcp_manager.servers = {
            "server1": mock_client1,
            "server2": mock_client2
        }
        
        # Test stopping
        await mcp_manager.stop_all_servers()
        
        mock_client1.disconnect.assert_called_once()
        mock_client2.disconnect.assert_called_once()
        assert len(mcp_manager.servers) == 0
        assert len(mcp_manager.available_tools) == 0
    
    @pytest.mark.asyncio
    async def test_discover_all_capabilities(self, mcp_manager):
        """Test discovering capabilities from all servers."""
        # Mock servers with tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "First tool"
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Second tool"
        
        mock_client1 = AsyncMock()
        mock_client1.list_tools = AsyncMock(return_value=[mock_tool1])
        
        mock_client2 = AsyncMock()
        mock_client2.list_tools = AsyncMock(return_value=[mock_tool2])
        
        mcp_manager.servers = {
            "server1": mock_client1,
            "server2": mock_client2
        }
        
        # Test capability discovery
        await mcp_manager.discover_all_capabilities()
        
        assert len(mcp_manager.available_tools) == 2
        assert mcp_manager.available_tools[0].server_name == "server1"
        assert mcp_manager.available_tools[1].server_name == "server2"
    
    def test_get_available_tools(self, mcp_manager):
        """Test getting available tools."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.server_name = "server1"
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.server_name = "server2"
        
        mcp_manager.available_tools = [mock_tool1, mock_tool2]
        
        tools = mcp_manager.get_available_tools()
        assert len(tools) == 2
        assert tools[0].name == "tool1"
        assert tools[1].name == "tool2"
    
    def test_get_tools_by_server(self, mcp_manager):
        """Test getting tools from a specific server."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.server_name = "server1"
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.server_name = "server2"
        
        mcp_manager.available_tools = [mock_tool1, mock_tool2]
        
        server1_tools = mcp_manager.get_tools_by_server("server1")
        assert len(server1_tools) == 1
        assert server1_tools[0].name == "tool1"
        
        server2_tools = mcp_manager.get_tools_by_server("server2")
        assert len(server2_tools) == 1
        assert server2_tools[0].name == "tool2"
    
    def test_get_tool_descriptions(self, mcp_manager):
        """Test getting tool descriptions."""
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "First tool"
        mock_tool1.server_name = "server1"
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Second tool"
        mock_tool2.server_name = "server2"
        
        mcp_manager.available_tools = [mock_tool1, mock_tool2]
        
        descriptions = mcp_manager.get_tool_descriptions()
        
        expected = {
            "tool1 (server1)": "First tool",
            "tool2 (server2)": "Second tool"
        }
        assert descriptions == expected
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_manager):
        """Test successful tool call."""
        # Mock tools and servers
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.server_name = "server1"
        
        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value="Tool result")
        
        mcp_manager.available_tools = [mock_tool]
        mcp_manager.servers = {"server1": mock_client}
        
        # Test tool call
        result = await mcp_manager.call_tool("test_tool", {"param": "value"})
        
        assert result == "Tool result"
        mock_client.call_tool.assert_called_once_with("test_tool", {"param": "value"})
    
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, mcp_manager):
        """Test tool call when tool is not found."""
        mcp_manager.available_tools = []
        mcp_manager.servers = {}
        
        result = await mcp_manager.call_tool("nonexistent_tool", {})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mcp_manager):
        """Test async context manager functionality."""
        with patch.object(mcp_manager, 'start_all_servers', return_value=True) as mock_start, \
             patch.object(mcp_manager, 'stop_all_servers') as mock_stop:
            
            async with mcp_manager:
                mock_start.assert_called_once()
            
            mock_stop.assert_called_once()

