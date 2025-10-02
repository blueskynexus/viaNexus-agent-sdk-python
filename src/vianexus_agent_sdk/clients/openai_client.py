"""
OpenAI Client implementation with universal memory management support.
"""
import asyncio
import json
import logging
import base64
from contextlib import AsyncExitStack
from openai import AsyncOpenAI
from typing import Any, Dict, List, Optional
from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient
from vianexus_agent_sdk.memory import ConversationMemoryMixin, BaseMemoryStore
from vianexus_agent_sdk.memory.stores.memory_memory import InMemoryStore
from .base_llm_client import BaseLLMClient, BasePersistentLLMClient

# Default financial system prompt constant (matching Anthropic client)
DEFAULT_FINANCIAL_SYSTEM_PROMPT = """You are a skilled Financial Analyst. You will use the tools provided to you to answer the question. You will only use the tools provided to you and not any other tools that are not provided to you. Use the `search` tool to find the appropriate dataset for the question. Use the `fetch` tool to fetch the data from the dataset."""


class OpenAiClient(BaseLLMClient, EnhancedMCPClient, ConversationMemoryMixin):
    """
    OpenAI Client with universal memory management support.
    
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
    ) -> "OpenAiClient":
        """
        Create OpenAiClient with InMemoryStore for fast, temporary conversations.
        Perfect for development, testing, and short-lived interactions.
        
        Args:
            config: Client configuration
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            OpenAiClient configured with InMemoryStore
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
    ) -> "OpenAiClient":
        """
        Create OpenAiClient with FileMemoryStore for persistent local storage.
        Conversations survive application restarts.
        
        Args:
            config: Client configuration
            storage_path: Directory path for conversation storage
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            OpenAiClient configured with FileMemoryStore
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
    ) -> "OpenAiClient":
        """
        Create OpenAiClient without memory system for stateless interactions.
        Each conversation is independent with no history retention.
        
        Args:
            config: Client configuration
            **kwargs: Additional client parameters
            
        Returns:
            OpenAiClient with memory disabled
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
            provider_name="openai"
        )
        
        # Initialize parent MCP client
        EnhancedMCPClient.__init__(self, config["agentServers"]["viaNexus"])
        
        # OpenAI-specific configuration
        self.openai = AsyncOpenAI(api_key=config.get("LLM_API_KEY"))
        self.model = config.get("LLM_MODEL", "gpt-4o-mini")
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

    @staticmethod
    def _map_tool(t):
        """Map MCP tool to OpenAI function format"""
        schema = getattr(t, "inputSchema", None)
        if not isinstance(schema, dict) or schema.get("type") != "object":
            schema = {"type": "object", "properties": {}}

        return {
            "type": "function",
            "name": t.name,
            "description": (t.description or "").strip(),
            "parameters": schema,  # leave as-is; not strict
            "strict": False  # Allow flexible parameter validation
        }

    async def _get_available_tools(self) -> list:
        """Get list of available MCP tools."""
        if not self.session:
            return []
        
        try:
            tool_list = await self.session.list_tools()
            return [self._map_tool(t) for t in (tool_list.tools or [])]
        except Exception as e:
            logging.error("Error listing tools: %s", e)
            return []

    async def _stream_assistant(self, input_text, tools, timeout=60):
        """Stream assistant response with tool call handling using responses API"""
        text_out = []
        pending = {}

        stream = await self.openai.responses.create(
            model=self.model,
            input=input_text,
            instructions=self.system_prompt,
            tools=tools or None,
            stream=True,
            max_output_tokens=self.max_tokens,
            timeout=timeout,
            tool_choice="auto",
        )

        async for event in stream:
            # Handle different event types from responses API
            if hasattr(event, 'type'):
                if event.type == 'response.text.delta':
                    if hasattr(event, 'delta') and event.delta:
                        print(event.delta, end="", flush=True)
                        text_out.append(event.delta)
                elif event.type == 'response.tool_calls.delta':
                    # Handle tool call deltas from responses API
                    if hasattr(event, 'tool_calls'):
                        for tc in event.tool_calls:
                            idx = getattr(tc, "index", None)
                            if idx is None:
                                continue  # ignore until index arrives
                            slot = pending.setdefault(idx, {"id": None, "name": None, "arguments": ""})

                            if getattr(tc, "id", None):
                                slot["id"] = tc.id

                            fn = getattr(tc, "function", None)
                            if fn:
                                if getattr(fn, "name", None):
                                    slot["name"] = fn.name
                                if getattr(fn, "arguments", None):
                                    slot["arguments"] += fn.arguments

        # Finalize tool_calls: only keep complete ones
        complete_calls = []
        for idx in sorted(pending.keys()):
            call = pending[idx]
            if call["id"] and call["name"]:
                complete_calls.append({
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": call["arguments"] or "{}",
                    },
                })

        assistant_msg = {"role": "assistant", "content": "".join(text_out)}
        if complete_calls:
            assistant_msg["tool_calls"] = complete_calls
            # Return tool_calls keyed by id for execution
            tool_calls_by_id = {c["id"]: c for c in complete_calls}
            return assistant_msg["content"], tool_calls_by_id, assistant_msg
        
        return assistant_msg["content"], {}, assistant_msg

    async def _execute_tool_calls(self, tool_calls_by_id: dict) -> list:
        """Execute MCP tool calls and return results."""
        result_blocks = []
        
        for call_id, call in tool_calls_by_id.items():
            name = call["function"]["name"]
            arg_str = call["function"]["arguments"] or "{}"
            
            try:
                args = json.loads(arg_str) if arg_str.strip() else {}
            except json.JSONDecodeError:
                args = {"_raw": arg_str}

            try:
                logging.info(f"Calling tool: {name} with args: {args}")
                result = await self.session.call_tool(name, args)
                payload = getattr(result, "content", result)
                
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
                    "tool_call_id": call_id,
                    "content": text_payload[:100_000]  # Truncate large responses
                })
                
            except Exception as e:
                logging.error("Tool '%s' failed: %s", name, e)
                result_blocks.append({
                    "type": "tool_result",
                    "tool_call_id": call_id,
                    "content": f"Error calling tool '{name}': {e}"
                })
        
        return result_blocks

    async def process_query(self, query: str) -> str:
        """
        Process query with streaming output (implements abstract method).
        Maintains conversation history like Anthropic client.
        """
        if not self.session:
            return "Error: MCP session not initialized."

        tools = await self._get_available_tools()
        self.messages.append({"role": "user", "content": query})

        while True:
            # Prepare input text from conversation history for responses API
            conversation_context = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in self.messages[-10:]  # Last 10 messages for context
            ])
            current_input = conversation_context

            text, tool_calls, assistant_msg = await self._stream_assistant(current_input, tools)
            
            # Store assistant message in conversation history
            self.messages.append({"role": "assistant", "content": text})

            if not tool_calls:
                print()
                self._trim_history()
                return ""

            # Execute tools and add results to conversation
            result_blocks = await self._execute_tool_calls(tool_calls)
            
            # Add tool results as user messages (OpenAI conversation pattern)
            for result in result_blocks:
                self.messages.append({
                    "role": "user", 
                    "content": f"Tool '{result['tool_call_id']}' result: {result['content']}"
                })

    def _trim_history(self):
        """Keep conversation history within reasonable bounds"""
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length:]

    async def ask_single_question(self, question: str) -> str:
        """
        Ask a single question without maintaining conversation history.
        Works with both persistent connections and creates temporary connections as needed.
        """
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

        logging.info(f"Tools: {tools}")
        
        response_content = ""
        current_input = question
        
        while True:
            # Call OpenAI responses API (non-streaming for single questions)
            response = await self.openai.responses.create(
                model=self.model,
                max_output_tokens=self.max_tokens,
                input=current_input,
                instructions=self.system_prompt,
                tools=tools or None
            )
            
            # Extract text content from responses API
            if hasattr(response, 'output') and response.output:
                if hasattr(response.output, 'content'):
                    response_content += response.output.content
            
            # Check for tool calls in responses API format
            if not hasattr(response, 'tool_calls') or not response.tool_calls:
                break
            
            # Execute tools
            tool_calls_by_id = {tc.id: {
                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
            } for tc in response.tool_calls}
            
            result_blocks = await self._execute_tool_calls(tool_calls_by_id)
            
            # Add tool results to input for next iteration
            tool_results = "\n".join([f"Tool result: {result['content']}" for result in result_blocks])
            current_input = f"{current_input}\n{tool_results}"
        
        return response_content.strip()

    async def ask_question(
        self, 
        question: str, 
        maintain_history: bool = False,
        use_memory: bool = True,
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
        """
        # Load conversation history from memory if requested
        if use_memory and maintain_history and load_from_memory:
            memory_messages = await self.memory_load_history()
            if memory_messages:
                self.messages = memory_messages
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
                # Prepare conversation context for responses API
                conversation_context = "\n".join([
                    f"{msg['role']}: {msg['content']}" for msg in self.messages[-10:]  # Last 10 messages
                ])
                
                logging.info(f"Tools: {tools[0] if tools else 'No tools available'}")
                
                response = await self.openai.responses.create(
                    model=self.model,
                    max_output_tokens=self.max_tokens,
                    input=conversation_context,
                    instructions=self.system_prompt,
                    tools=tools or None
                )
                
                # Extract content from responses API
                assistant_content = ""
                if hasattr(response, 'output') and response.output:
                    if hasattr(response.output, 'content'):
                        assistant_content = response.output.content
                        response_content += assistant_content
                
                self.messages.append({
                    "role": "assistant", 
                    "content": assistant_content
                })
                
                # Save assistant response to memory
                if use_memory:
                    await self.memory_save_message("assistant", assistant_content)
                
                # Check for tool calls in responses API format
                if not hasattr(response, 'tool_calls') or not response.tool_calls:
                    break
                
                # Execute tools
                tool_calls_by_id = {tc.id: {
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                } for tc in response.tool_calls}
                
                result_blocks = await self._execute_tool_calls(tool_calls_by_id)
                
                # Add tool results to conversation
                for result in result_blocks:
                    self.messages.append({
                        "role": "user",
                        "content": f"Tool result: {result['content']}"
                    })
                    
                    # Save tool results to memory
                    if use_memory:
                        await self.memory_save_message("user", result['content'], "tool_result")
            
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


class PersistentOpenAiClient(BasePersistentLLMClient, OpenAiClient):
    """
    Custom OpenAiClient that maintains persistent MCP connections.
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
        maintain_history: bool = True,
        use_memory: bool = True,
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
        logging.info(f"Auto-establish connection: {auto_establish_connection}")
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
        logging.info(f"Asking question: {question}")
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