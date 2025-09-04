"""End-to-end tests for the intelligent agent architecture."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.intelligent_agent import IntelligentAgent
from src.mcp_server_manager import MCPServerManager
from src.llm_client import LLMClient


class TestEndToEndArchitecture:
    """Test the complete intelligent agent architecture end-to-end."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock_client = Mock()
        mock_client.generate_response = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mock MCP manager."""
        mock_manager = Mock()
        mock_manager.get_available_tools.return_value = []
        mock_manager.get_available_resources.return_value = []
        mock_manager.call_tool = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def intelligent_agent(self, mock_llm_client, mock_mcp_manager):
        """Create an intelligent agent with mocked dependencies."""
        return IntelligentAgent(mock_llm_client, mock_mcp_manager)
    
    @pytest.mark.asyncio
    async def test_complete_user_request_flow(self, intelligent_agent, mock_llm_client, mock_mcp_manager):
        """Test the complete flow from user request to response."""
        # Mock the LLM responses for the two-phase strategy
        mock_llm_client.generate_response.side_effect = [
            "financial_database, user_profiles",  # Phase 1: Resources
            "query_financial_data, analyze_spending",  # Phase 1: Tools
            "I'll help you analyze your spending. Let me query the financial data.",  # Phase 2: Execution
        ]
        
        # Mock available tools and resources
        mock_tool = Mock()
        mock_tool.name = "query_financial_data"
        mock_tool.description = "Query financial data"
        mock_tool.server_name = "spendcast-graphdb"
        
        mock_resource = Mock()
        mock_resource.name = "financial_database"
        mock_resource.description = "Financial transaction database"
        
        mock_mcp_manager.get_available_tools.return_value = [mock_tool]
        mock_mcp_manager.get_available_resources.return_value = [mock_resource]
        
        # Test the complete flow
        result = await intelligent_agent.process_user_request("What's my spending this month?")
        
        # Verify the two-phase strategy was executed
        assert mock_llm_client.generate_response.call_count == 3
        
        # Verify the result contains the expected response
        assert "I'll help you analyze your spending" in result
    
    @pytest.mark.asyncio
    async def test_tool_execution_flow(self, intelligent_agent, mock_llm_client, mock_mcp_manager):
        """Test the flow when tools need to be executed."""
        # Mock the LLM responses
        mock_llm_client.generate_response.side_effect = [
            "query_financial_data",  # Phase 1: Tools (resources skipped since none available)
            """I'll query your financial data.
TOOL_CALL: query_financial_data
PARAMETERS: {"month": "2024-01"}""",  # Phase 2: Execution with tool call
        ]
        
        # Mock available tools
        mock_tool = Mock()
        mock_tool.name = "query_financial_data"
        mock_tool.description = "Query financial data"
        mock_tool.server_name = "spendcast-graphdb"
        
        # Mock available tools and resources
        mock_mcp_manager.get_available_tools.return_value = [mock_tool]
        mock_mcp_manager.get_available_resources.return_value = []
        mock_mcp_manager.call_tool.return_value = "Spending data for January 2024: $2,500"
        
        # Debug: verify the mock setup
        print(f"DEBUG: Available tools: {mock_mcp_manager.get_available_tools()}")
        print(f"DEBUG: Tool names: {[t.name for t in mock_mcp_manager.get_available_tools()]}")
        print(f"DEBUG: Available resources: {mock_mcp_manager.get_available_resources()}")
        
        # Test the complete flow
        result = await intelligent_agent.process_user_request("What's my spending this month?")
        
        # Debug: print the actual result
        print(f"DEBUG: Actual result: {result}")
        print(f"DEBUG: LLM calls: {mock_llm_client.generate_response.call_count}")
        print(f"DEBUG: Mock calls: {mock_llm_client.generate_response.mock_calls}")
        
        # The result should be the final response from execute_with_context
        assert "I'll query your financial data" in result
        
        # Verify tool was called (since the response contains a tool call)
        mock_mcp_manager.call_tool.assert_called_once_with("query_financial_data", {"month": "2024-01"})
    
    @pytest.mark.asyncio
    async def test_no_tools_needed_flow(self, intelligent_agent, mock_llm_client, mock_mcp_manager):
        """Test the flow when no tools are needed."""
        # Mock the LLM responses
        mock_llm_client.generate_response.side_effect = [
            "I can help you with general questions about finance and budgeting.",  # Phase 2: Execution (resources and tools skipped since none available)
        ]
        
        # Mock no available tools/resources
        mock_mcp_manager.get_available_tools.return_value = []
        mock_mcp_manager.get_available_resources.return_value = []
        
        # Test the complete flow
        result = await intelligent_agent.process_user_request("What is budgeting?")
        
        # The result should be the final response from execute_with_context
        assert "I can help you with general questions about finance and budgeting" in result
        
        # Verify no tools were called
        mock_mcp_manager.call_tool.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_flow(self, intelligent_agent, mock_llm_client, mock_mcp_manager):
        """Test error handling in the flow."""
        # Mock an error in the first phase
        mock_mcp_manager.get_available_resources.side_effect = Exception("Database connection failed")
        
        # Test the complete flow
        result = await intelligent_agent.process_user_request("What's my spending this month?")
        
        # Verify error handling
        assert "encountered an error" in result
        assert "Database connection failed" in result
    
    @pytest.mark.asyncio
    async def test_mcp_server_manager_integration(self):
        """Test that MCP Server Manager can be instantiated and configured."""
        manager = MCPServerManager()
        
        # Test initialization
        assert manager.servers == {}
        assert manager.server_configs == {}
        assert manager.available_tools == []
        assert manager.available_resources == []
        
        # Test configuration loading (mocked)
        with patch.object(manager, '_load_mcp_config', return_value={}):
            result = await manager.start_all_servers()
            assert result is False  # No servers configured
    
    @pytest.mark.asyncio
    async def test_intelligent_agent_with_real_classes(self):
        """Test that Intelligent Agent can work with real class instances."""
        # Create real instances
        llm_client = LLMClient()
        mcp_manager = MCPServerManager()
        agent = IntelligentAgent(llm_client, mcp_manager)
        
        # Test initialization
        assert agent.llm_client == llm_client
        assert agent.mcp_manager == mcp_manager
        
        # Test that methods exist
        assert hasattr(agent, 'process_user_request')
        assert hasattr(agent, 'determine_needed_resources')
        assert hasattr(agent, 'determine_needed_tools')
        assert hasattr(agent, 'execute_with_context')
