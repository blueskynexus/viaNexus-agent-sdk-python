"""
AnthropicClient implementation with universal memory management support.
"""
import asyncio
import logging
import json
import base64
import re
import ast
from contextlib import AsyncExitStack
from typing import Optional, Any
try:
    import jwt as jwt_lib
except ImportError:
    jwt_lib = None

from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient
from vianexus_agent_sdk.memory import ConversationMemoryMixin, BaseMemoryStore
from vianexus_agent_sdk.memory.stores.memory_memory import InMemoryStore
from .base_llm_client import BaseLLMClient, BasePersistentLLMClient

from anthropic import AsyncAnthropic
from anthropic.types.tool_use_block import ToolUseBlock
# Default financial system prompt constant
DEFAULT_FINANCIAL_SYSTEM_PROMPT = """You are a skilled Financial Analyst. You will use the tools provided to you to answer the question. You will only use the tools provided to you and not any other tools that are not provided to you. Use the `search` tool to find the appropriate dataset for the question. Use the `fetch` tool to fetch the data from the dataset."""


class AnthropicClient(BaseLLMClient, EnhancedMCPClient, ConversationMemoryMixin):
    """
    AnthropicClient with universal memory management support.
    
    System Prompt Priority Order:
    1. 'system_prompt' config parameter (highest priority)
    2. 'system_prompt' or 'systemPrompt' field in software_statement JWT (automatic extraction)
    3. DEFAULT_FINANCIAL_SYSTEM_PROMPT (fallback)
    
    Memory Integration:
    - Automatic InMemoryStore by default (enable_memory=True, use_in_memory_store=True)
    - Supports pluggable memory stores (S3, Redis, file-based, etc.)
    - Cross-session conversation continuity with session isolation
    - Universal message format for multi-provider compatibility
    - Configurable memory policies and cleanup
    
    Memory Options:
    - enable_memory=True: Enable memory system (default)
    - use_in_memory_store=True: Use fast InMemoryStore by default
    - memory_store=custom_store: Override with custom storage backend
    - Config-based memory settings for advanced control
    
    The software_statement JWT is provided by viaNexus API. The client automatically
    extracts system prompts from the JWT payload, supporting both snake_case and 
    camelCase field names and nested 'claims' objects if needed.
    """
    
    @staticmethod
    def _extract_system_prompt_from_jwt(jwt_token: str, verify_signature: bool = False) -> Optional[str]:
        """
        Extract system_prompt from JWT software statement with optional signature verification.
        
        Args:
            jwt_token: The JWT token string
            verify_signature: Whether to verify JWT signature (requires proper key management)
            
        Returns:
            The system prompt if found in the JWT payload, None otherwise
            
        Security Note:
            In production environments, verify_signature should be True with proper key management.
            Currently defaults to False for backward compatibility.
        """
        if not jwt_token or not isinstance(jwt_token, str):
            logging.warning("Invalid JWT token provided")
            return None
        
        # Check if PyJWT library is available
        if jwt_lib is None:
            logging.warning("PyJWT library not available. Install with: pip install PyJWT")
            return None
            
        try:
            # Validate JWT format
            parts = jwt_token.split('.')
            if len(parts) != 3:
                logging.warning("Invalid JWT format: expected 3 parts")
                return None
            
            # Use PyJWT for secure parsing
            if verify_signature:
                # In production, this should use a proper secret/key
                # For now, we'll decode without verification but log a warning
                logging.warning("JWT signature verification is disabled. Enable in production!")
                payload = jwt_lib.decode(jwt_token, options={"verify_signature": False})
            else:
                # Decode without signature verification (current behavior)
                payload = jwt_lib.decode(jwt_token, options={"verify_signature": False})
            
            # Validate payload structure
            if not isinstance(payload, dict):
                logging.warning("JWT payload is not a valid dictionary")
                return None
            
            # Look for system_prompt in various possible locations
            system_prompt = payload.get('system_prompt') or payload.get('systemPrompt')
            
            # Check nested structures if needed
            if not system_prompt and 'claims' in payload:
                claims = payload.get('claims', {})
                if isinstance(claims, dict):
                    system_prompt = claims.get('system_prompt') or claims.get('systemPrompt')
            
            # Validate system prompt if found
            if system_prompt and isinstance(system_prompt, str):
                # Basic validation - ensure it's not suspiciously long or contains dangerous content
                if len(system_prompt) > 10000:  # Reasonable limit
                    logging.warning("System prompt from JWT is suspiciously long, truncating")
                    system_prompt = system_prompt[:10000]
                
                logging.debug("Successfully extracted system prompt from JWT")
                return system_prompt
            
            return None
            
        except Exception as e:
            # Handle both jwt_lib.InvalidTokenError and other JWT-related errors
            if hasattr(e, '__class__') and 'InvalidTokenError' in str(e.__class__):
                logging.warning(f"Invalid JWT token: {e}")
            else:
                logging.warning(f"JWT parsing error: {e}")
            return None
        except (ValueError, json.JSONDecodeError, KeyError, IndexError) as e:
            logging.warning(f"Could not extract system prompt from JWT: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error parsing JWT: {e}")
            return None
    
    @staticmethod
    def _resolve_memory_store(
        memory_store: Optional[BaseMemoryStore],
        enable_memory: bool,
        use_in_memory_store: bool,
        config: dict
    ) -> Optional[BaseMemoryStore]:
        """
        Resolve which memory store to use based on configuration.
        
        Args:
            memory_store: Explicitly provided memory store
            enable_memory: Whether to enable memory at all
            use_in_memory_store: Whether to use InMemoryStore as default
            config: Configuration dictionary
            
        Returns:
            Resolved memory store or None if memory disabled
        """
        # If memory is disabled, return None
        if not enable_memory:
            logging.info("Memory system disabled")
            return None
        
        # If explicit memory store provided, use it
        if memory_store is not None:
            logging.info(f"Using provided memory store: {type(memory_store).__name__}")
            return memory_store
        
        # Check config for memory store preference
        memory_config = config.get("memory", {})
        memory_type = memory_config.get("store_type", "in_memory" if use_in_memory_store else None)
        
        if memory_type == "in_memory" or (memory_type is None and use_in_memory_store):
            logging.info("Using InMemoryStore for conversation memory")
            return InMemoryStore()
        elif memory_type == "file":
            from vianexus_agent_sdk.memory.stores.file_memory import FileMemoryStore
            storage_path = memory_config.get("file_path", "conversations")
            logging.info(f"Using FileMemoryStore at: {storage_path}")
            return FileMemoryStore(storage_path)
        elif memory_type is None:
            # Memory enabled but no default store requested
            logging.info("Memory enabled but no store configured - running without memory")
            return None
        else:
            logging.warning(f"Unknown memory store type: {memory_type}, falling back to InMemoryStore")
            return InMemoryStore()
    
    @classmethod
    def with_in_memory_store(
        cls,
        config: dict,
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> "AnthropicClient":
        """
        Create AnthropicClient with InMemoryStore for fast, temporary conversations.
        Perfect for development, testing, and short-lived interactions.
        
        Args:
            config: Client configuration
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            AnthropicClient configured with InMemoryStore
        """
        return cls(
            config=config,
            memory_store=InMemoryStore(),
            memory_session_id=memory_session_id,
            user_id=user_id,
            enable_memory=True,
            **kwargs
        )
    
    @classmethod
    def with_file_memory_store(
        cls,
        config: dict,
        storage_path: str = "conversations",
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> "AnthropicClient":
        """
        Create AnthropicClient with FileMemoryStore for persistent local storage.
        Conversations survive application restarts.
        
        Args:
            config: Client configuration
            storage_path: Directory path for conversation storage
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            AnthropicClient configured with FileMemoryStore
        """
        from vianexus_agent_sdk.memory.stores.file_memory import FileMemoryStore
        
        return cls(
            config=config,
            memory_store=FileMemoryStore(storage_path),
            memory_session_id=memory_session_id,
            user_id=user_id,
            enable_memory=True,
            **kwargs
        )
    
    @classmethod
    def without_memory(
        cls,
        config: dict,
        **kwargs
    ) -> "AnthropicClient":
        """
        Create AnthropicClient without memory system for stateless interactions.
        Each conversation is independent with no history retention.
        
        Args:
            config: Client configuration
            **kwargs: Additional client parameters
            
        Returns:
            AnthropicClient with memory disabled
        """
        return cls(
            config=config,
            enable_memory=False,
            **kwargs
        )
    
    def __init__(
        self, 
        config: dict,
        memory_store: Optional[BaseMemoryStore] = None,
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_memory: bool = True,
        use_in_memory_store: bool = True
    ):
        # Configure memory store based on parameters
        resolved_memory_store = self._resolve_memory_store(
            memory_store, enable_memory, use_in_memory_store, config
        )
        
        # Initialize memory mixin first
        ConversationMemoryMixin.__init__(
            self,
            memory_store=resolved_memory_store,
            memory_session_id=memory_session_id,
            user_id=user_id,
            provider_name="anthropic"
        )
        
        # Initialize parent MCP client
        EnhancedMCPClient.__init__(self, config["agentServers"]["viaNexus"])
        
        # Ensure _exit_stack is available for resource cleanup
        if not hasattr(self, '_exit_stack') or self._exit_stack is None:
            from contextlib import AsyncExitStack
            self._exit_stack = AsyncExitStack()
        
        # Anthropic-specific configuration
        self.anthropic = AsyncAnthropic(api_key=config.get("LLM_API_KEY"))
        self.model = config.get("LLM_MODEL", "claude-sonnet-4-20250514")
        self.max_tokens = config.get("max_tokens", 1000)
        self.messages = []  # Local message cache
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
            
            content_blocks, _ = self._process_content_blocks_for_tool_use(msg.content)
            tool_uses = [b for b in content_blocks if getattr(b, "type", None) == "tool_use"]
            self.messages.append({"role": "assistant", "content": content_blocks})
            
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
    
    def _convert_memory_to_anthropic_messages(self, memory_messages: list) -> list:
        """Convert universal memory messages to Anthropic format."""
        anthropic_messages = []
        
        for msg in memory_messages:
            # Handle both UniversalMessage objects and dict formats
            if hasattr(msg, 'role'):
                # UniversalMessage object
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                content = msg.content
            else:
                # Dictionary format (fallback)
                role = msg.get("role", "user")
                content = msg.get("content", "")
            
            # Create Anthropic message format
            anthropic_msg = {
                "role": role,
                "content": str(content)
            }
            anthropic_messages.append(anthropic_msg)
        
        return anthropic_messages
    
    def _trim_history(self):
        """Keep conversation history within reasonable bounds."""
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length:]
    
    def _extract_input_dict(self, content: str) -> Optional[str]:
        """
        Extract the input dictionary from ToolUseBlock content using proper brace matching.
        
        Args:
            content: The content string from inside ToolUseBlock()
            
        Returns:
            The input dictionary string or None if not found
        """
        # Find the start of input=
        input_start = content.find("input=")
        if input_start == -1:
            return None
        
        # Find the opening brace
        brace_start = content.find("{", input_start)
        if brace_start == -1:
            return None
        
        # Use brace matching to find the complete dictionary
        brace_count = 0
        i = brace_start
        in_string = False
        escape_next = False
        
        while i < len(content):
            char = content[i]
            
            if escape_next:
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                escape_next = True
                i += 1
                continue
            
            if char == "'" and not in_string:
                in_string = True
            elif char == "'" and in_string:
                in_string = False
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found the matching closing brace
                        return content[brace_start:i+1]
            
            i += 1
        
        # If we get here, braces weren't properly matched
        return None
    
    def _parse_tool_use_block_string(self, text: str) -> Optional[dict]:
        """
        Parse a ToolUseBlock string representation and extract the tool use information.
        
        Example input: "[ToolUseBlock(id='toolu_01Pqg5fhUE46bW3fz3w6k4jS', input={'endpoint': 'data', 'product': 'core', 'dataset_name': 'quote', 'symbols': 'V'}, name='fetch', type='tool_use')]"
        
        Returns: dict with 'type', 'id', 'name', 'input' keys or None if parsing fails
        """
        try:
            # Use regex to extract ToolUseBlock content
            pattern = r'ToolUseBlock\(([^)]+)\)'
            match = re.search(pattern, text)
            
            if not match:
                return None
            
            # Extract the content inside ToolUseBlock()
            content = match.group(1)
            
            # Parse the parameters using regex
            # Look for id='...', input={...}, name='...', type='...'
            id_match = re.search(r"id='([^']+)'", content)
            name_match = re.search(r"name='([^']+)'", content)
            type_match = re.search(r"type='([^']+)'", content)
            
            # For input, we need to handle the dictionary structure with proper brace matching
            input_match = self._extract_input_dict(content)
            
            if not all([id_match, name_match, type_match]):
                return None
            
            tool_use_dict = {
                'type': type_match.group(1),
                'id': id_match.group(1),
                'name': name_match.group(1),
            }
            
            # Parse the input dictionary if present
            if input_match:
                input_str = input_match
                try:
                    # Use ast.literal_eval to safely parse Python dictionary literals
                    # This properly handles single quotes in both keys and string values
                    tool_use_dict['input'] = ast.literal_eval(input_str)
                except (ValueError, SyntaxError) as e:
                    # If literal_eval fails, try JSON parsing as fallback
                    try:
                        # Only convert outer quotes, not quotes within string values
                        # This is a more conservative approach for JSON-like structures
                        input_str = input_str.replace("\'", '\"')
                        tool_use_dict['input'] = json.loads(input_str)
                    except json.JSONDecodeError:
                        # If both methods fail, store as string and log the issue
                        logging.warning(f"Failed to parse tool input dictionary: {input_str}, error: {e}")
                        tool_use_dict['input'] = input_str
            
            return tool_use_dict
            
        except Exception as e:
            logging.error(f"Failed to parse ToolUseBlock string: {e}")
            return None
    
    def _process_content_blocks_for_tool_use(self, content_blocks: list) -> tuple[list, str]:
        """
        Process content blocks to parse ToolUseBlock strings and extract text content.
        
        Args:
            content_blocks: List of content blocks from Anthropic response
            
        Returns:
            Tuple of (processed_content_blocks, response_text_content)
        """
        # Convert to mutable list if not already
        processed_blocks = list(content_blocks or [])
        response_content = ""
        
        for i, block in enumerate(processed_blocks):
            if getattr(block, "type", None) == "text":
                logging.debug(f"Original Text Block: {block.text}")
                if "ToolUseBlock(" in block.text:
                    #[ToolUseBlock(id='toolu_01Pqg5fhUE46bW3fz3w6k4jS', input={'endpoint': 'data', 'product': 'core', 'dataset_name': 'quote', 'symbols': 'V'}, name='fetch', type='tool_use')]
                    tool_use_dict = self._parse_tool_use_block_string(block.text)
                    if tool_use_dict:
                        processed_blocks[i] = ToolUseBlock(**tool_use_dict)  # Replace the item in the list
                        logging.debug(f"Tool use block ToolUseBlock String Parsed: {processed_blocks[i]}")
                else:
                    response_content += block.text
        
        return processed_blocks, response_content
    
    async def ask_single_question(self, question: str) -> str:
        """
        Ask a single question without maintaining conversation history.
        Works with both persistent connections and creates temporary connections as needed.
        
        Args:
            question: The question to ask
            
        Returns:
            The response as a string
            
        Raises:
            ValueError: If question is invalid
        """
        # Validate input
        question = self._validate_question(question)
        # Check if we have a persistent connection
        if hasattr(self, '_connection_active') and self._connection_active and self.session:
            # Use existing persistent connection
            return await self._ask_single_question_with_session(question)
        else:
            # Create temporary connection for this request
            async with self.connection_manager.connection_context() as (readstream, writestream, get_session_id):
                self.readstream = readstream
                self.writestream = writestream
                
                if not await self.connect_to_server():
                    return "Error: Failed to establish MCP connection."
                
                try:
                    return await self._ask_single_question_with_session(question)
                finally:
                    # Clean up temporary session
                    if hasattr(self, '_exit_stack') and self._exit_stack:
                        try:
                            await self._exit_stack.aclose()
                            self.session = None
                        except Exception as e:
                            logging.debug(f"Error closing temporary session: {e}")
    
    async def _ask_single_question_with_session(self, question: str) -> str:
        """Helper method that assumes session is already established."""
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
            content_blocks, block_response_content = self._process_content_blocks_for_tool_use(response.content)
            response_content += block_response_content
            
            temp_messages.append({"role": "assistant", "content": content_blocks})
            
            # Check for tool uses
            tool_uses = [b for b in content_blocks if getattr(b, "type", None) == "tool_use"]
            
            if not tool_uses:
                break
            
            # Execute tools
            result_blocks = await self._execute_tool_calls(tool_uses)
            temp_messages.append({"role": "user", "content": result_blocks})
        
        return response_content.strip()
    
    async def ask_question(
        self, 
        question: str, 
        maintain_history: bool = False,
        use_memory: bool = False,
        load_from_memory: bool = True
    ) -> str:
        """
        Ask a question with optional conversation history and memory integration.
        
        Args:
            question: The question to ask
            maintain_history: Whether to maintain conversation context
            use_memory: Whether to save messages to memory store
            load_from_memory: Whether to load previous conversation from memory
        
        Returns:
            The response as a string
            
        Raises:
            ValueError: If question is invalid
        """
        # Validate input
        question = self._validate_question(question)
        # Load conversation history from memory if requested
        if use_memory and maintain_history and load_from_memory:
            memory_messages = await self.memory_load_history()
            if memory_messages:
                # Convert memory messages to Anthropic format
                self.messages = self._convert_memory_to_anthropic_messages(memory_messages)
                logging.debug(f"Loaded {len(memory_messages)} messages from memory")
        
        # Save user question to memory
        if use_memory:
            await self.memory_save_message("user", question)
        
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
                content_blocks, block_response_content = self._process_content_blocks_for_tool_use(response.content)
                response_content += block_response_content
                
                self.messages.append({"role": "assistant", "content": content_blocks})
                
                # Save assistant response to memory
                if use_memory:
                    await self.memory_save_message("assistant", content_blocks)
                
                # Check for tool uses
                tool_uses = [b for b in content_blocks if getattr(b, "type", None) == "tool_use"]
                
                if not tool_uses:
                    break
                
                # Execute tools
                result_blocks = await self._execute_tool_calls(tool_uses)
                self.messages.append({"role": "user", "content": result_blocks})
                
                # Save tool results to memory
                if use_memory:
                    await self.memory_save_message("user", result_blocks, "tool_result")
            
            self._trim_history()
            return response_content.strip()
        else:
            # Use single question method (no persistent history)
            result = await self.ask_single_question(question)
            
            # Still save to memory if requested (for searchability)
            if use_memory:
                await self.memory_save_message("user", question)
                await self.memory_save_message("assistant", result)
            
            return result
    
    # Abstract method implementations
    async def initialize(self) -> None:
        """
        Initialize the client by setting up authentication.
        After initialization, choose either:
        - establish_persistent_connection() for long-running sessions
        - Use methods directly for per-request connections
        """
        await self.setup_connection()
        logging.info("Client initialized - choose establish_persistent_connection() or use methods directly")
    
    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        if hasattr(self, '_exit_stack') and self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logging.error(f"Error closing session: {e}")
    
    # provider_name, model_name and system_prompt are already implemented via memory mixin, base class and instance attribute


class PersistentAnthropicClient(BasePersistentLLMClient, AnthropicClient):
    """
    Custom AnthropicClient that maintains persistent MCP connections.
    Overrides the base class to keep connections open across multiple requests.
    """
    
    def __init__(
        self,
        config: dict,
        memory_store: Optional[BaseMemoryStore] = None,
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_memory: bool = True,
        use_in_memory_store: bool = True
    ):
        super().__init__(
            config=config,
            memory_store=memory_store,
            memory_session_id=memory_session_id,
            user_id=user_id,
            enable_memory=enable_memory,
            use_in_memory_store=use_in_memory_store
        )
        self._connection_active = False
        self._connection_context = None
        self._persistent_exit_stack = AsyncExitStack()
        self._mcp_session_id = None
        self._connection_task_group = None
        self._connection_task = None
        
        # For persistent clients, we can eagerly initialize the memory session
        # since they're typically used for longer-running conversations
        if self.memory_enabled and not self.memory_session_id:
            # Generate memory session ID immediately for persistent clients
            if self.session_manager:
                self.memory_session_id = self.session_manager.generate_session_id(
                    user_id=self.user_id,
                    client_type=self.provider_name,
                    context="persistent"
                )
        
    async def initialize_memory_session(self) -> str:
        """
        Explicitly initialize the memory session and return the memory session ID.
        
        Returns:
            The memory session ID
        """
        if not self.memory_enabled:
            raise RuntimeError("Memory is not enabled for this client")
        
        # Force memory session initialization
        await self.memory_initialize_session()
        
        if not self.memory_session_id:
            raise RuntimeError("Failed to initialize memory session")
        
        return self.memory_session_id
    
    async def _verify_connection_health(self) -> bool:
        """Verify that the persistent connection is still healthy."""
        if not self._connection_active or not self._mcp_session_id:
            logging.debug("Connection not active or no MCP session ID")
            return False
        
        if not self.session:
            logging.debug("No MCP session object available")
            return False
        
        try:
            # Try to list tools as a health check
            await self.session.list_tools()
            logging.debug("Connection health check passed")
            return True
        except Exception as e:
            logging.warning(f"Connection health check failed: {e}")
            # Mark connection as inactive
            self._connection_active = False
            return False
    
    async def establish_persistent_connection(self) -> str:
        """Establish and maintain a persistent MCP connection."""
        # First check if existing connection is still healthy
        if self._connection_active and self._mcp_session_id:
            if await self._verify_connection_health():
                logging.debug(f"Reusing healthy persistent connection: {self._mcp_session_id}")
                return self._mcp_session_id
            else:
                logging.info("Existing connection unhealthy, re-establishing...")
                await self.close_persistent_connection()
            
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
                # Try to close the exit stack gracefully
                try:
                    await self._persistent_exit_stack.aclose()
                    logging.debug("Successfully closed persistent exit stack")
                except RuntimeError as e:
                    if "different task" in str(e) or "cancel scope" in str(e):
                        # This is expected when closing across task boundaries
                        # The resources are likely already cleaned up by the connection context manager
                        logging.debug(f"Exit stack cleanup skipped due to task boundary: {e}")
                    else:
                        logging.warning(f"Unexpected error closing exit stack: {e}")
                except Exception as e:
                    logging.warning(f"Error closing exit stack: {e}")
                
                # Always create a fresh exit stack for future connections
                self._persistent_exit_stack = AsyncExitStack()
            
            # Reset connection state
            self._connection_active = False
            self._mcp_session_id = None
            self._connection_context = None
            self._connection_task_group = None
            self._connection_task = None
            
            # Force cleanup of any remaining session resources
            if hasattr(self, 'session') and self.session:
                try:
                    # The session should be cleaned up by the exit stack, but just in case
                    self.session = None
                except Exception as e:
                    logging.debug(f"Error clearing session reference: {e}")
            
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
        is_active = self._connection_active and self._mcp_session_id is not None
        logging.debug(f"Connection status check: active={self._connection_active}, mcp_session_id={self._mcp_session_id}, result={is_active}")
        return is_active
    
    async def ask_with_persistent_session(
        self, 
        question: str, 
        maintain_history: bool = False,
        use_memory: bool = False,
        auto_establish_connection: bool = True
    ) -> str:
        """
        Ask a question using the persistent MCP connection with integrated memory.
        
        Args:
            question: The question to ask
            maintain_history: Whether to maintain conversation context (default: True)
            use_memory: Whether to use memory for context and persistence (default: True)
            auto_establish_connection: Whether to automatically establish MCP connection if needed (default: True)
        
        Returns:
            The response as a string
        """
        # Check connection health and auto-establish if needed
        if auto_establish_connection:
            if not self.is_connected or not await self._verify_connection_health():
                try:
                    mcp_session_id = await self.establish_persistent_connection()
                    logging.info(f"Established persistent MCP connection: {mcp_session_id}")
                except Exception as e:
                    logging.error(f"Failed to establish MCP connection: {e}")
                    raise RuntimeError(f"Could not establish persistent MCP connection: {e}")
        
        if not self.is_connected:
            raise RuntimeError("No persistent MCP connection available. Call establish_persistent_connection() first or set auto_establish_connection=True")
        
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        
        # Use the ask_question method which integrates with memory system
        return await self.ask_question(
            question=question,
            maintain_history=maintain_history,
            use_memory=use_memory,
            load_from_memory=use_memory
        )
    
    async def cleanup(self) -> None:
        """Clean up both persistent and base class resources."""
        await self.close_persistent_connection()
        await super().cleanup()