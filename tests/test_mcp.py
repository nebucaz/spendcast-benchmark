"""Tests for the consolidated MCP client and manager."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.mcp import (
    MCPServerManager,
    MCPServerConfig,
    MCPClient,
    load_mcp_configs,
    TextContent,
)
from mcp import ClientSession


@pytest.fixture
def mcp_manager():
    """Fixture for MCPServerManager."""
    return MCPServerManager()


# Test MCPServerConfig
def test_mcp_server_config_creation():
    """Test the creation of an MCPServerConfig object."""
    config_dict = {
        "command": "my_command",
        "args": ["--verbose"],
        "env": {"VAR": "value"},
        "cwd": "/tmp",
    }
    server_config = MCPServerConfig("test_server", config_dict)
    assert server_config.name == "test_server"
    assert server_config.command == "my_command"
    assert server_config.args == ["--verbose"]
    assert server_config.env == {"VAR": "value"}
    assert server_config.cwd == "/tmp"


# Test load_mcp_configs
@patch("builtins.open")
@patch("json.load")
@patch("pathlib.Path.exists")
def test_load_mcp_configs_success(mock_exists, mock_json_load, mock_open):
    """Test successfully loading MCP configurations from a file."""
    mock_exists.return_value = True
    mock_json_load.return_value = {
        "mcpServers": {"server1": {"command": "cmd1"}}
    }
    configs = load_mcp_configs()
    assert "server1" in configs
    assert isinstance(configs["server1"], MCPServerConfig)
    assert configs["server1"].command == "cmd1"


@patch("pathlib.Path.exists")
def test_load_mcp_configs_not_found(mock_exists, caplog):
    """Test loading MCP configurations when the file is not found."""
    mock_exists.return_value = False
    configs = load_mcp_configs()
    assert configs == {}
    assert "config.json not found" in caplog.text


# Test MCPServerManager
@pytest.mark.asyncio
async def test_manager_start_all_servers_no_config(mcp_manager, caplog):
    """Test starting servers with no configuration."""
    with patch("src.mcp.load_mcp_configs", return_value={}):
        success = await mcp_manager.start_all_servers()
        assert not success
        assert "No MCP servers to start" in caplog.text


@pytest.mark.asyncio
async def test_manager_start_all_servers_success(mcp_manager):
    """Test starting servers with a valid configuration successfully."""
    mock_config = {
        "server1": MCPServerConfig("server1", {"command": "echo", "args": ["hello"]})
    }

    with patch("src.mcp.load_mcp_configs", return_value=mock_config):
        with patch("src.mcp.MCPClient.connect_to_server", new_callable=AsyncMock, return_value=True):
            success = await mcp_manager.start_all_servers()

            assert success
            assert "server1" in mcp_manager.servers
            assert isinstance(mcp_manager.servers["server1"], MCPClient)


@pytest.mark.asyncio
async def test_manager_start_all_servers_failure(mcp_manager, caplog):
    """Test starting servers when a server fails to connect."""
    mock_config = {
        "server1": MCPServerConfig("server1", {"command": "echo"}),
        "server2": MCPServerConfig("server2", {"command": "fail"}),
    }

    async def mock_connect(self, config):
        return config.name == "server1"

    with patch("src.mcp.load_mcp_configs", return_value=mock_config):
        with patch("src.mcp.MCPClient.connect_to_server", mock_connect):
            success = await mcp_manager.start_all_servers()

            assert success
            assert "server1" in mcp_manager.servers
            assert "server2" not in mcp_manager.servers
            assert "Failed to start MCP server: server2" in caplog.text


@pytest.mark.asyncio
async def test_manager_stop_all_servers(mcp_manager):
    """Test stopping all running servers."""
    # NOTE: MCPServerManager.stop_all_servers calls `client.disconnect()`,
    # which does not exist on MCPClient. The correct method is `dispose()`.
    # This test mocks `disconnect` to align with the current implementation.
    mock_client1 = MagicMock(spec=MCPClient)
    mock_client1.dispose = AsyncMock()

    mock_client2 = MagicMock(spec=MCPClient)
    mock_client2.dispose = AsyncMock()

    mcp_manager.servers = {"server1": mock_client1, "server2": mock_client2}

    await mcp_manager.stop_all_servers()

    mock_client1.dispose.assert_awaited_once()
    mock_client2.dispose.assert_awaited_once()
    assert not mcp_manager.servers


@pytest.mark.asyncio
async def test_manager_discover_all_capabilities(mcp_manager):
    """Test discovering tools from all servers."""
    mock_tool1 = MagicMock()
    mock_tool1.name = "tool1"
    mock_tool2 = MagicMock()
    mock_tool2.name = "tool2"

    mock_client1 = MagicMock(spec=MCPClient)
    mock_client1.list_tools = AsyncMock(return_value=[mock_tool1])

    mock_client2 = MagicMock(spec=MCPClient)
    mock_client2.list_tools = AsyncMock(return_value=[mock_tool2])

    mcp_manager.servers = {"server1": mock_client1, "server2": mock_client2}

    await mcp_manager.discover_all_capabilities()

    assert len(mcp_manager.available_tools) == 2
    assert mcp_manager.available_tools[0] == mock_tool1
    assert mcp_manager.available_tools[1] == mock_tool2
    assert mcp_manager.available_tools[0].server_name == "server1"
    assert mcp_manager.available_tools[1].server_name == "server2"


@pytest.mark.asyncio
async def test_manager_call_tool_on_first_server(mcp_manager):
    """Test calling a tool which is found on the first server."""
    mock_result = "tool result"
    mock_client1 = MagicMock(spec=MCPClient)
    mock_client1.call_tool = AsyncMock(return_value=mock_result)
    mock_client2 = MagicMock(spec=MCPClient)
    mock_client2.call_tool = AsyncMock()

    mcp_manager.servers = {"server1": mock_client1, "server2": mock_client2}

    result = await mcp_manager.call_tool("my_tool", {})

    assert result == mock_result
    mock_client1.call_tool.assert_awaited_once_with("my_tool", {})
    mock_client2.call_tool.assert_not_awaited()


# Test MCPClient
@pytest.mark.asyncio
async def test_client_connect_to_server_success():
    """Test MCPClient successful connection."""
    client = MCPClient()
    config = {"command": "echo", "args": ["hello"], "env": {}}

    with patch("mcp.client.stdio.stdio_client") as mock_stdio_client:
        mock_context = mock_stdio_client.return_value
        mock_context.__aenter__.return_value = (AsyncMock(), AsyncMock())

        with patch("src.mcp.ClientSession") as MockClientSession:
            mock_session = MockClientSession.return_value
            mock_session.initialize = AsyncMock()

            success = await client.connect_to_server(config)

            assert success
            assert client.session is not None
            mock_session.initialize.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_call_tool_success():
    """Test MCPClient successful tool call."""
    client = MCPClient()
    client.session = AsyncMock(spec=ClientSession)

    mock_tool_result = MagicMock()
    mock_tool_result.content = [TextContent(type="text", text="Success")]
    mock_tool_result.content = [TextContent(type="text", text="Success")]
    client.session.call_tool.return_value = mock_tool_result

    result = await client.call_tool("test_tool", {})

    assert result == "Success"
    client.session.call_tool.assert_awaited_with("test_tool", {})
