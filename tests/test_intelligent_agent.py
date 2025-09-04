"""Tests for Intelligent Agent functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.intelligent_agent import IntelligentAgent


class TestIntelligentAgent:
    """Test cases for Intelligent Agent functionality."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client for testing."""
        mock_client = Mock()
        mock_client.generate_response = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mock MCP manager for testing."""
        mock_manager = Mock()
        mock_manager.get_available_tools.return_value = []
        mock_manager.get_available_resources.return_value = []
        return mock_manager
    
    @pytest.fixture
    def intelligent_agent(self, mock_llm_client, mock_mcp_manager):
        """Create an Intelligent Agent instance for testing."""
        return IntelligentAgent(mock_llm_client, mock_mcp_manager)
    
    @pytest.fixture
    def sample_tools(self):
        """Sample tools for testing."""
        tool1 = Mock()
        tool1.name = "query_financial_data"
        tool1.description = "Query financial data from GraphDB"
        tool1.server_name = "spendcast-graphdb"
        
        tool2 = Mock()
        tool2.name = "analyze_spending"
        tool2.description = "Analyze spending patterns"
        tool2.server_name = "spendcast-graphdb"
        
        return [tool1, tool2]
    
    @pytest.fixture
    def sample_resources(self):
        """Sample resources for testing."""
        resource1 = Mock()
        resource1.name = "financial_database"
        resource1.description = "Financial transaction database"
        
        resource2 = Mock()
        resource2.name = "user_profiles"
        resource2.description = "User profile information"
        
        return [resource1, resource2]
    
    def test_intelligent_agent_initialization(self, intelligent_agent, mock_llm_client, mock_mcp_manager):
        """Test Intelligent Agent initialization."""
        assert intelligent_agent.llm_client == mock_llm_client
        assert intelligent_agent.mcp_manager == mock_mcp_manager
    
    @pytest.mark.asyncio
    async def test_process_user_request_success(self, intelligent_agent, mock_llm_client, mock_mcp_manager):
        """Test successful processing of a user request."""
        # Mock the two-phase process
        with patch.object(intelligent_agent, 'determine_needed_resources', return_value=[]) as mock_resources, \
             patch.object(intelligent_agent, 'determine_needed_tools', return_value=[]) as mock_tools, \
             patch.object(intelligent_agent, 'execute_with_context', return_value="Response") as mock_execute:
            
            result = await intelligent_agent.process_user_request("What's my spending this month?")
            
            assert result == "Response"
            mock_resources.assert_called_once_with("What's my spending this month?")
            mock_tools.assert_called_once_with("What's my spending this month?", [])
            mock_execute.assert_called_once_with("What's my spending this month?", [], [])
    
    @pytest.mark.asyncio
    async def test_process_user_request_error(self, intelligent_agent):
        """Test error handling in user request processing."""
        with patch.object(intelligent_agent, 'determine_needed_resources', side_effect=Exception("Test error")):
            result = await intelligent_agent.process_user_request("Test query")
            
            assert "encountered an error" in result
            assert "Test error" in result
    
    @pytest.mark.asyncio
    async def test_determine_needed_resources_with_resources(self, intelligent_agent, mock_llm_client, mock_mcp_manager, sample_resources):
        """Test determining needed resources when resources are available."""
        mock_mcp_manager.get_available_resources.return_value = sample_resources
        mock_llm_client.generate_response.return_value = "financial_database, user_profiles"
        
        result = await intelligent_agent.determine_needed_resources("What's my spending this month?")
        
        assert result == ["financial_database", "user_profiles"]
        mock_llm_client.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_determine_needed_resources_no_resources(self, intelligent_agent, mock_mcp_manager):
        """Test determining needed resources when no resources are available."""
        mock_mcp_manager.get_available_resources.return_value = []
        
        result = await intelligent_agent.determine_needed_resources("What's my spending this month?")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_determine_needed_resources_none_response(self, intelligent_agent, mock_llm_client, mock_mcp_manager, sample_resources):
        """Test determining needed resources when LLM returns 'none'."""
        mock_mcp_manager.get_available_resources.return_value = sample_resources
        mock_llm_client.generate_response.return_value = "none"
        
        result = await intelligent_agent.determine_needed_resources("What's my spending this month?")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_determine_needed_tools_with_tools(self, intelligent_agent, mock_llm_client, mock_mcp_manager, sample_tools):
        """Test determining needed tools when tools are available."""
        mock_mcp_manager.get_available_tools.return_value = sample_tools
        mock_llm_client.generate_response.return_value = "query_financial_data, analyze_spending"
        
        result = await intelligent_agent.determine_needed_tools("What's my spending this month?", ["financial_database"])
        
        assert result == ["query_financial_data", "analyze_spending"]
        mock_llm_client.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_determine_needed_tools_no_tools(self, intelligent_agent, mock_mcp_manager):
        """Test determining needed tools when no tools are available."""
        mock_mcp_manager.get_available_tools.return_value = []
        
        result = await intelligent_agent.determine_needed_tools("What's my spending this month?", [])
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_execute_with_context_success(self, intelligent_agent, mock_llm_client, mock_mcp_manager, sample_tools):
        """Test successful execution with context."""
        mock_mcp_manager.get_available_tools.return_value = sample_tools
        mock_llm_client.generate_response.return_value = "I'll help you with that."
        
        with patch.object(intelligent_agent, '_process_tool_calls', return_value="Processed response"):
            result = await intelligent_agent.execute_with_context("What's my spending this month?", ["financial_database"], ["query_financial_data"])
            
            assert result == "Processed response"
            mock_llm_client.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_context_no_response(self, intelligent_agent, mock_llm_client, mock_mcp_manager, sample_tools):
        """Test execution with context when LLM returns no response."""
        mock_mcp_manager.get_available_tools.return_value = sample_tools
        mock_llm_client.generate_response.return_value = None
        
        result = await intelligent_agent.execute_with_context("What's my spending this month?", [], [])
        
        assert result == "I couldn't generate a response for your request."
    
    @pytest.mark.asyncio
    async def test_process_tool_calls_with_tool_calls(self, intelligent_agent, mock_mcp_manager):
        """Test processing tool calls in LLM response."""
        mock_mcp_manager.get_available_tools.return_value = [Mock()]
        mock_mcp_manager.call_tool = AsyncMock(return_value="Tool result")
        
        response = """I'll help you with that.
TOOL_CALL: query_financial_data
PARAMETERS: {"month": "2024-01"}"""
        
        result = await intelligent_agent._process_tool_calls(response)
        
        assert "Tool 'query_financial_data' result: Tool result" in result
    
    @pytest.mark.asyncio
    async def test_process_tool_calls_no_tool_calls(self, intelligent_agent, mock_mcp_manager):
        """Test processing response with no tool calls."""
        mock_mcp_manager.get_available_tools.return_value = []
        
        response = "I'll help you with that."
        result = await intelligent_agent._process_tool_calls(response)
        
        assert result == response
    
    @pytest.mark.asyncio
    async def test_process_tool_calls_invalid_json(self, intelligent_agent, mock_mcp_manager):
        """Test processing tool calls with invalid JSON parameters."""
        mock_mcp_manager.get_available_tools.return_value = [Mock()]
        
        response = """I'll help you with that.
TOOL_CALL: query_financial_data
PARAMETERS: {invalid json}"""
        
        result = await intelligent_agent._process_tool_calls(response)
        
        assert "parameters invalid" in result
    
    def test_format_available_resources(self, intelligent_agent, sample_resources):
        """Test formatting available resources for prompts."""
        result = intelligent_agent._format_available_resources(sample_resources)
        
        assert "financial_database: Financial transaction database" in result
        assert "user_profiles: User profile information" in result
    
    def test_format_available_resources_empty(self, intelligent_agent):
        """Test formatting empty resources list."""
        result = intelligent_agent._format_available_resources([])
        
        assert result == "No resources available"
    
    def test_format_available_tools(self, intelligent_agent, sample_tools):
        """Test formatting available tools for prompts."""
        result = intelligent_agent._format_available_tools(sample_tools)
        
        assert "query_financial_data (spendcast-graphdb): Query financial data from GraphDB" in result
        assert "analyze_spending (spendcast-graphdb): Analyze spending patterns" in result
    
    def test_format_available_tools_empty(self, intelligent_agent):
        """Test formatting empty tools list."""
        result = intelligent_agent._format_available_tools([])
        
        assert result == "No tools available"
    
    def test_parse_resource_selection(self, intelligent_agent):
        """Test parsing resource selection from LLM response."""
        # Test normal response
        result = intelligent_agent._parse_resource_selection("financial_database, user_profiles")
        assert result == ["financial_database", "user_profiles"]
        
        # Test 'none' response
        result = intelligent_agent._parse_resource_selection("none")
        assert result == []
        
        # Test 'no resources' response
        result = intelligent_agent._parse_resource_selection("no resources needed")
        assert result == []
    
    def test_parse_tool_selection(self, intelligent_agent):
        """Test parsing tool selection from LLM response."""
        # Test normal response
        result = intelligent_agent._parse_tool_selection("query_financial_data, analyze_spending")
        assert result == ["query_financial_data", "analyze_spending"]
        
        # Test 'none' response
        result = intelligent_agent._parse_tool_selection("none")
        assert result == []
        
        # Test 'no tools' response
        result = intelligent_agent._parse_tool_selection("no tools needed")
        assert result == []
