"""
AnthropicClient implementation using composition for cleaner architecture.
This replaces the inheritance-based approach with better separation of concerns.
"""
from anthropic import AsyncAnthropic
import logging
import json
import base64
from contextlib import AsyncExitStack
from typing import Optional, Any

from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient

# Default financial system prompt constant
DEFAULT_FINANCIAL_SYSTEM_PROMPT = """You are a skilled Financial Analyst. You will use the tools provided to you to answer the question. You will only use the tools provided to you and not any other tools that are not provided to you. Use the `search` tool to find the appropriate dataset for the question. Use the `fetch` tool to fetch the data from the dataset."""


class AnthropicClient(EnhancedMCPClient):
    """
    AnthropicClient using inheritance from EnhancedMCPClient for simplicity.
    
    System Prompt Priority Order:
    1. 'system_prompt' config parameter (highest priority)
    2. 'system_prompt' or 'systemPrompt' field in software_statement JWT (automatic extraction)
    3. DEFAULT_FINANCIAL_SYSTEM_PROMPT (fallback)
    
    The software_statement JWT is provided by viaNexus API. The client automatically
    extracts system prompts from the JWT payload, supporting both snake_case and 
    camelCase field names and nested 'claims' objects if needed.
    """
    
    @staticmethod
    def _extract_system_prompt_from_jwt(jwt_token: str) -> Optional[str]:
        """
        Extract system_prompt from JWT software statement.
        
        Args:
            jwt_token: The JWT token string
            
        Returns:
            The system prompt if found in the JWT payload, None otherwise
        """
        try:
            # Split JWT into parts (header.payload.signature)
            parts = jwt_token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode the payload (second part)
            payload_b64 = parts[1]
            
            # Add padding if needed for base64 decoding
            padding = '=' * (4 - len(payload_b64) % 4)
            payload_b64 += padding
            
            # Decode base64 and parse JSON
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Look for system_prompt in various possible locations
            system_prompt = payload.get('system_prompt') or payload.get('systemPrompt')
            
            # Could also check nested structures if needed
            if not system_prompt and 'claims' in payload:
                claims = payload['claims']
                system_prompt = claims.get('system_prompt') or claims.get('systemPrompt')
            
            return system_prompt
            
        except (ValueError, json.JSONDecodeError, KeyError, IndexError) as e:
            logging.debug(f"Could not extract system prompt from JWT: {e}")
            return None
    
    def __init__(self, config: dict):
        # Initialize parent class with MCP config
        super().__init__(config["agentServers"]["viaNexus"])
        
        # Anthropic-specific configuration
        self.anthropic = AsyncAnthropic(api_key=config.get("LLM_API_KEY"))
        self.model = config.get("LLM_MODEL", "claude-sonnet-4-20250514")
        self.max_tokens = config.get("max_tokens", 1000)
        self.messages = []
        self.max_history_length = config.get("max_history_length", 50)
        
        # Determine system prompt priority: config > JWT > default
        self.system_prompt = config.get("system_prompt")
        
        if not self.system_prompt:
            # Try to extract from software_statement JWT stored in StreamableHttpSetup
            software_statement = self.connection_manager.software_statement
            if software_statement:
                jwt_system_prompt = self._extract_system_prompt_from_jwt(software_statement)
                if jwt_system_prompt:
                    self.system_prompt = jwt_system_prompt
                    logging.info("Using system prompt from software_statement JWT")
        
        # Fall back to default if still not set
        if not self.system_prompt:
            self.system_prompt = DEFAULT_FINANCIAL_SYSTEM_PROMPT
            logging.debug("Using default financial system prompt")
    
    async def process_query(self, query: str) -> str:
        """
        Process query with streaming output (implements abstract method).
        """
        if not self.session:
            return "Error: MCP session not initialized."
        
        tools = await self._get_available_tools()
        self.messages.append({"role": "user", "content": query})
        
        while True:
            async with self.anthropic.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=self.messages,
                tools=tools or None,
                system=self.system_prompt
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and getattr(event.delta, "type", "") == "text_delta":
                        print(event.delta.text, end="", flush=True)
                
                msg = await stream.get_final_message()
            
            tool_uses = [b for b in msg.content if getattr(b, "type", None) == "tool_use"]
            self.messages.append({"role": "assistant", "content": msg.content})
            
            if not tool_uses:
                print()
                self._trim_history()
                return ""
            
            # Execute tools
            result_blocks = await self._execute_tool_calls(tool_uses)
            self.messages.append({"role": "user", "content": result_blocks})
    
    async def _get_available_tools(self) -> list:
        """Get list of available MCP tools."""
        if not self.session:
            return []
        
        try:
            tool_list = await self.session.list_tools()
            return [{
                "name": t.name,
                "description": t.description or "",
                "input_schema": getattr(t, "inputSchema", {}) or {},
            } for t in (tool_list.tools or [])]
        except Exception as e:
            logging.error("Error listing tools: %s", e)
            return []
    
    async def _execute_tool_calls(self, tool_uses: list) -> list:
        """Execute MCP tool calls and return results."""
        result_blocks = []
        
        for tub in tool_uses:
            name = tub.name
            args = tub.input if isinstance(tub.input, dict) else {}
            
            try:
                logging.info(f"Calling tool: {name} with args: {args}")
                result = await self.session.call_tool(name, args)
                payload = result.content
                
                # Handle different payload types safely
                text_payload = ""
                if isinstance(payload, list):
                    if len(payload) > 0 and hasattr(payload[0], 'text'):
                        text_payload = payload[0].text
                    elif len(payload) > 0:
                        text_payload = str(payload[0])
                    else:
                        text_payload = "No content returned"
                elif isinstance(payload, dict):
                    text_payload = payload.get('text', payload.get('content', str(payload)))
                else:
                    text_payload = str(payload)
                
                result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tub.id,
                    "content": [{"type": "text", "text": text_payload}],
                })
                
            except Exception as e:
                logging.error("Tool '%s' failed: %s", name, e)
                result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tub.id,
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                })
        
        return result_blocks
    
    def _trim_history(self):
        """Keep conversation history within reasonable bounds."""
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length:]
    
    async def ask_single_question(self, question: str) -> str:
        """
        Ask a single question without maintaining conversation history.
        """
        if not self.session:
            return "Error: MCP session not initialized."
        
        # Get available tools
        tools = await self._get_available_tools()
        
        # Create temporary message list for this single question
        temp_messages = [{"role": "user", "content": question}]
        response_content = ""
        
        while True:
            # Call Anthropic API
            response = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=temp_messages,
                tools=tools or None,
                system=self.system_prompt
            )
            
            # Extract text content
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    response_content += block.text
            
            temp_messages.append({"role": "assistant", "content": response.content})
            
            # Check for tool uses
            tool_uses = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
            
            if not tool_uses:
                break
            
            # Execute tools
            result_blocks = await self._execute_tool_calls(tool_uses)
            temp_messages.append({"role": "user", "content": result_blocks})
        
        return response_content.strip()
    
    async def ask_question(self, question: str, maintain_history: bool = False) -> str:
        """
        Ask a question with optional conversation history.
        
        Args:
            question: The question to ask
            maintain_history: Whether to maintain conversation context
        
        Returns:
            The response as a string
        """
        if maintain_history:
            # Add to ongoing conversation
            self.messages.append({"role": "user", "content": question})
            
            tools = await self._get_available_tools()
            response_content = ""
            
            while True:
                response = await self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=self.messages,
                    tools=tools or None,
                    system=self.system_prompt
                )
                
                # Extract text content
                for block in response.content:
                    if getattr(block, "type", None) == "text":
                        response_content += block.text
                
                self.messages.append({"role": "assistant", "content": response.content})
                
                # Check for tool uses
                tool_uses = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
                
                if not tool_uses:
                    break
                
                # Execute tools
                result_blocks = await self._execute_tool_calls(tool_uses)
                self.messages.append({"role": "user", "content": result_blocks})
            
            self._trim_history()
            return response_content.strip()
        else:
            # Use single question method
            return await self.ask_single_question(question)


class PersistentAnthropicClient(AnthropicClient):
    """
    Custom AnthropicClient that maintains persistent MCP connections.
    Overrides the base class to keep connections open across multiple requests.
    """
    
    def __init__(self, config):
        super().__init__(config)
        self._connection_active = False
        self._connection_context = None
        self._persistent_exit_stack = AsyncExitStack()
        self._mcp_session_id = None
        
    async def establish_persistent_connection(self) -> str:
        """Establish and maintain a persistent MCP connection."""
        if self._connection_active and self._mcp_session_id:
            return self._mcp_session_id
            
        try:
            # Ensure auth layer is set up first
            if not await self.setup_connection():
                raise RuntimeError("Failed to setup connection")
            
            # Set up the connection context that will stay open
            self._connection_context = await self._persistent_exit_stack.enter_async_context(
                self.connection_manager.connection_context()
            )
            
            readstream, writestream, get_session_id = self._connection_context
            
            # Set the streams on the client
            self.readstream = readstream
            self.writestream = writestream
            
            # Connect to the MCP server
            if not await self.connect_to_server():
                raise RuntimeError("Failed to initialize MCP session")
            
            # Get the session ID from the connection
            try:
                mcp_session_id = get_session_id() if get_session_id else None
                if not mcp_session_id:
                    raise RuntimeError("Failed to get MCP session ID")
                
                self._mcp_session_id = str(mcp_session_id)
                self._connection_active = True
                logging.info(f"Established persistent MCP connection: {self._mcp_session_id}")
                
                return self._mcp_session_id
                
            except Exception as e:
                raise RuntimeError(f"Failed to get MCP session ID: {e}")
                
        except Exception as e:
            logging.error(f"Error establishing persistent MCP connection: {e}")
            await self.close_persistent_connection()
            raise RuntimeError(f"Failed to establish persistent MCP connection: {e}")
    
    async def close_persistent_connection(self):
        """Close the persistent MCP connection."""
        try:
            if self._persistent_exit_stack:
                await self._persistent_exit_stack.aclose()
            self._connection_active = False
            self._mcp_session_id = None
            self._connection_context = None
            logging.info("Closed persistent MCP connection")
        except Exception as e:
            logging.error(f"Error closing persistent MCP connection: {e}")
    
    @property
    def mcp_session_id(self) -> str | None:
        """Get the current MCP session ID."""
        return self._mcp_session_id
    
    @property
    def is_connected(self) -> bool:
        """Check if the persistent connection is active."""
        return self._connection_active and self._mcp_session_id is not None
    
    async def ask_with_persistent_session(self, question: str) -> str:
        """Ask a question using the persistent connection."""
        if not self.is_connected:
            raise RuntimeError("No persistent MCP connection available")
        
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        
        # Use the ask_single_question method but with persistent session
        return await self.ask_single_question(question)
    
    async def cleanup(self) -> None:
        """Clean up both persistent and base class resources."""
        await self.close_persistent_connection()
        await super().cleanup()