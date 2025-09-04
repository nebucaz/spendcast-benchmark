"""Intelligent Agent for coordinating communication between user, LLM, and MCP servers."""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class IntelligentAgent:
    """Coordinates communication between user, LLM, and MCP servers."""
    
    def __init__(self, llm_client: LLMClient, mcp_manager):
        """Initialize the intelligent agent."""
        self.llm_client = llm_client
        self.mcp_manager = mcp_manager
        
    async def process_user_request(self, user_query: str) -> str:
        """Process a user request using the intelligent two-phase strategy."""
        logger.info(f"Processing user request: {user_query}")
        
        try:
            # Phase 1: Determine what resources and tools are needed
            needed_resources = await self.determine_needed_resources(user_query)
            needed_tools = await self.determine_needed_tools(user_query, needed_resources)
            
            logger.info(f"Phase 1 complete - Resources needed: {len(needed_resources)}, Tools needed: {len(needed_tools)}")
            
            # Phase 2: Execute with gathered context
            result = await self.execute_with_context(user_query, needed_resources, needed_tools)
            
            logger.info("Phase 2 complete - Request processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def determine_needed_resources(self, user_query: str) -> List[str]:
        """Phase 1: Determine what resources are needed for this request."""
        available_resources = self.mcp_manager.get_available_resources()
        
        if not available_resources:
            logger.info("No resources available, skipping resource determination")
            return []
        
        prompt = f"""
        User request: {user_query}
        
        Available resources:
        {self._format_available_resources(available_resources)}
        
        Which of these resources do you need to fulfill this request? 
        Respond with a list of resource names separated by commas, or 'none' if no resources are needed.
        
        Only respond with the resource names, nothing else.
        """
        
        response = await self.llm_client.generate_response(prompt)
        if not response:
            return []
        
        # Parse the response to extract resource names
        resource_names = self._parse_resource_selection(response)
        logger.info(f"Determined needed resources: {resource_names}")
        
        return resource_names
    
    async def determine_needed_tools(self, user_query: str, needed_resources: List[str]) -> List[str]:
        """Phase 1: Determine what tools are needed for this request."""
        available_tools = await self.mcp_manager.get_available_tools()
        
        if not available_tools:
            logger.info("No tools available, skipping tool determination")
            return []
        
        prompt = f"""
        User request: {user_query}
        
        Resources that will be available: {', '.join(needed_resources) if needed_resources else 'None'}
        
        Available tools:
        {self._format_available_tools(available_tools)}
        
        Which of these tools do you need to fulfill this request? 
        Respond with a list of tool names separated by commas, or 'none' if no tools are needed.
        
        Only respond with the tool names, nothing else.
        """
        
        response = await self.llm_client.generate_response(prompt)
        if not response:
            return []
        
        # Parse the response to extract tool names
        tool_names = self._parse_tool_selection(response)
        logger.info(f"Determined needed tools: {tool_names}")
        
        return tool_names
    
    async def execute_with_context(self, user_query: str, needed_resources: List[str], needed_tools: List[str]) -> str:
        """Phase 2: Execute the request with gathered context."""
        available_tools = await self.mcp_manager.get_available_tools()
        
        # Filter tools to only those that are needed
        relevant_tools = [tool for tool in available_tools if tool.name in needed_tools]
        
        prompt = f"""
        User request: {user_query}
        
        Available tools for this request:
        {self._format_available_tools(relevant_tools)}
        
        What should I do to fulfill this request? Use the available tools if needed.
        
        IMPORTANT: If you need to call a tool, format your response EXACTLY like this:
        TOOL_CALL: tool_name
        PARAMETERS: {{"param1": "value1", "param2": "value2"}}
        
        Rules:
        1. Use the exact tool names from the available tools list
        2. Provide valid JSON parameters (no extra text after the closing brace)
        3. If no tools are needed, just provide a helpful response
        4. Only call one tool at a time
        
        Provide a helpful response that addresses the user's request.
        """
        
        response = await self.llm_client.generate_response(prompt)
        if not response:
            return "I couldn't generate a response for your request."
        
        # Process any tool calls in the response
        processed_response = await self._process_tool_calls(response)
        
        # If tool calls were executed, feed results back to LLM for final response
        if "Tool '" in processed_response and processed_response != response:
            final_response = await self._generate_final_response(user_query, processed_response)
            return final_response
        
        return processed_response
    
    async def _process_tool_calls(self, response: str) -> str:
        """Process tool calls in the LLM response with enhanced parsing."""
        available_tools = await self.mcp_manager.get_available_tools()
        if not available_tools:
            return response
        
        logger.info(f"Processing LLM response for tool calls: {response[:200]}...")
        
        # Look for tool call patterns in the response
        tool_call_pattern = r'TOOL_CALL:\s*(\w+)\s*\nPARAMETERS:\s*(\{.*?\})'
        matches = re.findall(tool_call_pattern, response, re.MULTILINE | re.DOTALL)
        
        logger.info(f"Found {len(matches)} tool call matches: {matches}")
        
        if not matches:
            return response
        
        # Execute tool calls
        tool_results = []
        for tool_name, params_str in matches:
            try:
                # Parse parameters with better error handling
                import json
                params = self._parse_tool_parameters(params_str)
                
                if params is None:
                    tool_results.append(f"Tool '{tool_name}' parameters could not be parsed")
                    continue
                
                # Call the tool
                logger.info(f"Executing tool call: {tool_name} with params: {params}")
                result = await self.mcp_manager.call_tool(tool_name, params)
                
                if result:
                    tool_results.append(f"Tool '{tool_name}' result: {result}")
                else:
                    tool_results.append(f"Tool '{tool_name}' failed to execute")
                    
            except Exception as e:
                logger.error(f"Tool '{tool_name}' execution failed: {e}")
                tool_results.append(f"Tool '{tool_name}' execution failed: {e}")
        
        # Append tool results to the response
        if tool_results:
            response += "\n\n" + "\n".join(tool_results)
        
        return response
    
    def _parse_tool_parameters(self, params_str: str) -> Optional[Dict[str, Any]]:
        """Parse tool parameters with enhanced error handling."""
        import json
        
        # Clean up the parameters string
        params_str = params_str.strip()
        
        # Try to find the JSON object boundaries
        start_idx = params_str.find('{')
        if start_idx == -1:
            logger.error("No JSON object found in parameters")
            return None
        
        # Find the matching closing brace
        brace_count = 0
        end_idx = -1
        for i, char in enumerate(params_str[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx == -1:
            logger.error("No matching closing brace found in parameters")
            return None
        
        # Extract the JSON part
        json_str = params_str[start_idx:end_idx + 1]
        
        try:
            params = json.loads(json_str)
            return params
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool parameters: {e}")
            logger.error(f"JSON string: {json_str}")
            return None
    
    async def _generate_final_response(self, user_query: str, tool_results: str) -> str:
        """Generate final response using tool results."""
        prompt = f"""
        User request: {user_query}
        
        Tool execution results:
        {tool_results}
        
        Based on the tool results above, provide a helpful and complete response to the user's request.
        Summarize the key information from the tool results and answer their question directly.
        """
        
        final_response = await self.llm_client.generate_response(prompt)
        if not final_response:
            return f"I executed the requested tools but couldn't generate a final response. Here are the tool results:\n\n{tool_results}"
        
        return final_response
    
    def _format_available_resources(self, resources: List[Any]) -> str:
        """Format available resources for the prompt."""
        if not resources:
            return "No resources available"
        
        formatted = []
        for resource in resources:
            name = getattr(resource, 'name', 'Unknown')
            description = getattr(resource, 'description', 'No description')
            formatted.append(f"- {name}: {description}")
        
        return "\n".join(formatted)
    
    def _format_available_tools(self, tools: List[Any]) -> str:
        """Format available tools for the prompt."""
        if not tools:
            return "No tools available"
        
        formatted = []
        for tool in tools:
            name = tool.name
            description = tool.description
            server_name = getattr(tool, 'server_name', 'unknown')
            formatted.append(f"- {name} ({server_name}): {description}")
        
        return "\n".join(formatted)
    
    def _parse_resource_selection(self, response: str) -> List[str]:
        """Parse resource selection from LLM response."""
        response = response.strip().lower()
        
        if 'none' in response or 'no resources' in response:
            return []
        
        # Extract resource names (simple comma-separated parsing)
        resources = [r.strip() for r in response.split(',') if r.strip()]
        return resources
    
    def _parse_tool_selection(self, response: str) -> List[str]:
        """Parse tool selection from LLM response."""
        response = response.strip().lower()
        
        if 'none' in response or 'no tools' in response:
            return []
        
        # Extract tool names (simple comma-separated parsing)
        tools = [t.strip() for t in response.split(',') if t.strip()]
        return tools
