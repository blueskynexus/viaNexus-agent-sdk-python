"""
Gemini Client implementation with universal memory management support.
"""
import asyncio
import json
import logging
import base64
from contextlib import AsyncExitStack
from google import genai
from typing import Any, Dict, List, Optional
from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient
from vianexus_agent_sdk.memory import ConversationMemoryMixin, BaseMemoryStore
from vianexus_agent_sdk.memory.stores.memory_memory import InMemoryStore
from .base_llm_client import BaseLLMClient, BasePersistentLLMClient

# Default financial system prompt constant (matching other clients)
DEFAULT_FINANCIAL_SYSTEM_PROMPT = """You are a skilled Financial Analyst. You will use the tools provided to you to answer the question. You will only use the tools provided to you and not any other tools that are not provided to you. Use the `search` tool to find the appropriate dataset for the question. Use the `fetch` tool to fetch the data from the dataset."""


class GeminiClient(BaseLLMClient, EnhancedMCPClient, ConversationMemoryMixin):
    """
    Gemini Client with universal memory management support.
    
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
    
    Note: Gemini API uses a different message format than OpenAI/Anthropic:
    - Messages have 'role' and 'parts' structure
    - System instructions are handled separately via system_instruction parameter
    - Tool calls use function_call format in parts
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
    ) -> "GeminiClient":
        """
        Create GeminiClient with InMemoryStore for fast, temporary conversations.
        Perfect for development, testing, and short-lived interactions.
        
        Args:
            config: Client configuration
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            GeminiClient configured with InMemoryStore
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
    ) -> "GeminiClient":
        """
        Create GeminiClient with FileMemoryStore for persistent local storage.
        Conversations survive application restarts.
        
        Args:
            config: Client configuration
            storage_path: Directory path for conversation storage
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            GeminiClient configured with FileMemoryStore
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
    ) -> "GeminiClient":
        """
        Create GeminiClient without memory system for stateless interactions.
        Each conversation is independent with no history retention.
        
        Args:
            config: Client configuration
            **kwargs: Additional client parameters
            
        Returns:
            GeminiClient with memory disabled
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
            provider_name="gemini"
        )
        
        # Initialize parent MCP client
        EnhancedMCPClient.__init__(self, config["agentServers"]["viaNexus"])
        
        # Gemini-specific configuration
        self.client = genai.Client(api_key=config.get("LLM_API_KEY"))
        self._model_name = config.get("LLM_MODEL", "gemini-2.5-flash")
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
    
    async def _get_available_tools(self) -> Optional[genai.types.Tool]:
        """Get list of available MCP tools formatted for Gemini API."""
        if not self.session:
            return None
        
        try:
            tool_list = await self.session.list_tools()
            if not tool_list.tools:
                return None
            
            logging.debug(f"Retrieved {len(tool_list.tools)} tools from MCP server")
            formatted_tools = []
            for tool in tool_list.tools:
                # Convert MCP tool schema to Gemini format
                schema = getattr(tool, "inputSchema", None)
                if schema:
                    gemini_schema = self._convert_schema_for_gemini(schema)
                else:
                    # Fallback schema for tools without proper schema
                    gemini_schema = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                
                formatted_tool = {
                    "name": tool.name,
                    "description": tool.description or f"Tool: {tool.name}",
                    "parameters": gemini_schema
                }
                formatted_tools.append(formatted_tool)
            
            return genai.types.Tool(function_declarations=formatted_tools)
            
        except Exception as e:
            logging.error(f"Error listing tools: {e}")
            return None

    async def process_query(self, query: str) -> str:
        """
        Process query with streaming output (implements abstract method).
        Maintains conversation history like other clients.
        Works with both persistent connections and creates temporary connections as needed.
        """
        # Check if we have a persistent connection
        if hasattr(self, '_connection_active') and self._connection_active and self.session:
            # Use existing persistent connection
            return await self._process_query_with_session(query)
        else:
            # Create temporary connection for this request
            async with self.connection_manager.connection_context() as (readstream, writestream, get_session_id):
                self.readstream = readstream
                self.writestream = writestream
                
                if not await self.connect_to_server():
                    return "Error: Failed to establish MCP connection."
                
                try:
                    return await self._process_query_with_session(query)
                finally:
                    # Clean up temporary session
                    if hasattr(self, 'session') and self.session:
                        try:
                            await self.session.close()
                            self.session = None
                        except Exception as e:
                            logging.debug(f"Error closing temporary session: {e}")
    
    async def _process_query_with_session(self, query: str) -> str:
        """Helper method that assumes session is already established."""
        tools = await self._get_available_tools()
        self.messages.append(genai.types.Content(role="user", parts=[genai.types.Part.from_text(text=query)]))

        while True:
            try:
                response = await self.client.aio.models.generate_content(
                    model=self._model_name,
                    contents=self.messages,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=self.max_tokens,
                        system_instruction=self.system_prompt,
                        tools=[tools] if tools else None
                    )
                )

                # Check for a text response first
                if response.text:
                    print(response.text, end="", flush=True)
                    self.messages.append(genai.types.Content(
                        role="model", 
                        parts=[genai.types.Part.from_text(text=response.text)]
                    ))
                    print()  # Add newline
                    self._trim_history()
                    return ""

                # Check if the response contains content, to prevent NoneType error
                if response.candidates and response.candidates[0].content:
                    # Check if the model is calling a tool
                    tool_calls = [p.function_call for p in response.candidates[0].content.parts if hasattr(p, 'function_call') and p.function_call]

                    if tool_calls:
                        # Add the model's response to the history (preserving function calls for context)
                        assistant_content = self._extract_text_only_content(response.candidates[0].content)
                        if assistant_content:
                            self.messages.append(assistant_content)

                        # Execute tools
                        tool_results = await self._execute_tool_calls(tool_calls)
                        self.messages.append(genai.types.Content(role="user", parts=tool_results))
                    else:
                        # Handle cases where there is content, but it's not a text or tool call
                        logging.warning("Unexpected content format in Gemini response")
                        self._trim_history()
                        return "No valid response content received from Gemini API"
                else:
                    # Handle the 'None' content case
                    finish_reason = response.candidates[0].finish_reason if response.candidates else "unknown"
                    logging.warning(f"Model response has no content. Finish reason: {finish_reason}")
                    self._trim_history()
                    return f"No response content available. Finish reason: {finish_reason}"
                    
            except Exception as e:
                logging.error(f"Error in process_query: {e}")
                return f"Error processing query: {e}"
    
    async def _execute_tool_calls(self, tool_calls: list) -> list:
        """Execute MCP tool calls and return results formatted for Gemini."""
        tool_results = []
        
        for tool_call in tool_calls:
            name = tool_call.name
            args = dict(tool_call.args) if tool_call.args else {}
            
            try:
                logging.debug(f"Executing tool: {name}")
                result = await self.session.call_tool(name, args)
                
                # Handle different payload types safely
                text_payload = ""
                if hasattr(result, 'content') and result.content:
                    payload = result.content
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
                else:
                    text_payload = str(result)
                
                # Create Gemini-formatted tool response
                tool_response_part = genai.types.Part.from_function_response(
                    name=name,
                    response={"result": text_payload[:1_000_000]}  # Truncate large responses (consistent with other clients)
                )
                tool_results.append(tool_response_part)
                
            except Exception as e:
                logging.error(f"Tool '{name}' failed: {e}")
                # Create error response
                error_response_part = genai.types.Part.from_function_response(
                    name=name,
                    response={"error": f"Tool execution failed: {e}"}
                )
                tool_results.append(error_response_part)
        
        return tool_results
    

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
                    if hasattr(self, 'session') and self.session:
                        try:
                            await self.session.close()
                            self.session = None
                        except Exception as e:
                            logging.debug(f"Error closing temporary session: {e}")
    
    async def _ask_single_question_with_session(self, question: str) -> str:
        """Helper method that assumes session is already established."""
        # Get available tools
        tools = await self._get_available_tools()
        
        # Create temporary message list for this single question
        temp_messages = [genai.types.Content(role="user", parts=[genai.types.Part.from_text(text=question)])]
        response_content = ""
        
        while True:
            try:
                response = await self.client.aio.models.generate_content(
                    model=self._model_name,
                    contents=temp_messages,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=self.max_tokens,
                        system_instruction=self.system_prompt,
                        tools=[tools] if tools else None
                    )
                )
                # Extract text content
                if response.text:
                    response_content += response.text
                
                # Check for tool calls
                if response.candidates and response.candidates[0].content:
                    tool_calls = [p.function_call for p in response.candidates[0].content.parts if hasattr(p, 'function_call') and p.function_call]
                    if not tool_calls:
                        break
                    
                    # Add model response to temp conversation
                    temp_messages.append(response.candidates[0].content)
                    # Execute tools
                    tool_results = await self._execute_tool_calls(tool_calls)
                    temp_messages.append(genai.types.Content(role="user", parts=tool_results))
                else:
                    break
                    
            except Exception as e:
                logging.error(f"Error in ask_single_question: {e}")
                return f"Error: {e}"
        
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
                # Convert memory messages to Gemini format
                self.messages = self._convert_memory_to_gemini_messages(memory_messages)
                logging.debug(f"Loaded {len(memory_messages)} messages from memory")
        
        # Save user question to memory
        if use_memory:
            await self.memory_save_message("user", question)
        
        if maintain_history:
            # Add to ongoing conversation
            self.messages.append(genai.types.Content(role="user", parts=[genai.types.Part.from_text(text=question)]))
            
            tools = await self._get_available_tools()
            response_content = ""
            
            while True:
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self._model_name,
                        contents=self.messages,
                        config=genai.types.GenerateContentConfig(
                            temperature=0.7,
                            max_output_tokens=self.max_tokens,
                            system_instruction=self.system_prompt,
                            tools=[tools] if tools else None
                        )
                    )
                    
                    # Extract text content
                    if response.text:
                        response_content += response.text
                    
                    # Add assistant response to conversation (preserving function calls for context)
                    if response.candidates and response.candidates[0].content:
                        assistant_content = self._extract_text_only_content(response.candidates[0].content)
                        if assistant_content:
                            self.messages.append(assistant_content)
                        
                        # Save assistant response to memory
                        if use_memory and response.text:
                            await self.memory_save_message("assistant", response.text)
                        
                        # Check for tool calls
                        tool_calls = [p.function_call for p in response.candidates[0].content.parts if hasattr(p, 'function_call') and p.function_call]
                        
                        if not tool_calls:
                            break
                        
                        # Execute tools
                        tool_results = await self._execute_tool_calls(tool_calls)
                        self.messages.append(genai.types.Content(role="user", parts=tool_results))
                        
                        # Save tool results to memory
                        if use_memory:
                            for result_part in tool_results:
                                if hasattr(result_part, 'function_response'):
                                    await self.memory_save_message("user", str(result_part.function_response), "tool_result")
                    else:
                        break
                        
                except Exception as e:
                    logging.error(f"Error in ask_question: {e}")
                    return f"Error: {e}"
            
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
    
    def _extract_text_only_content(self, response_content: 'genai.types.Content') -> Optional['genai.types.Content']:
        """
        Extract text and function call parts from a Gemini response content.
        Preserves function calls to maintain conversation context for multi-turn tool interactions.
        
        Args:
            response_content: The original response content from Gemini API
            
        Returns:
            A new Content object with text and function call parts, or None if no relevant parts found
        """
        relevant_parts = []
        for part in response_content.parts:
            # Include text parts
            if hasattr(part, 'text') and part.text:
                relevant_parts.append(genai.types.Part.from_text(text=part.text))
            # Include function call parts to maintain tool interaction context
            elif hasattr(part, 'function_call') and part.function_call:
                relevant_parts.append(part)
        
        if relevant_parts:
            return genai.types.Content(role="model", parts=relevant_parts)
        return None
    
    def _convert_memory_to_gemini_messages(self, memory_messages: list) -> list:
        """Convert universal memory messages to Gemini format."""
        gemini_messages = []
        
        for msg in memory_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Map roles to Gemini format
            if role == "assistant":
                gemini_role = "model"
            else:
                gemini_role = "user"
            
            # Create Gemini message
            gemini_msg = genai.types.Content(
                role=gemini_role,
                parts=[genai.types.Part.from_text(text=str(content))]
            )
            gemini_messages.append(gemini_msg)
        
        return gemini_messages

    def _convert_schema_for_gemini(self, schema: dict) -> dict:
        """
        Recursively sanitizes an MCP tool schema to be compatible with Gemini's API
        by keeping only the supported fields and ensuring proper format.
        """
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}, "required": []}
        
        # Supported fields in Gemini's function declaration schema
        supported_keys = {'type', 'description', 'required', 'properties', 'items', 'enum'}
        gemini_schema = {}
        
        for key, value in schema.items():
            if key in supported_keys:
                if key == 'properties' and isinstance(value, dict):
                    # Recursively convert nested properties
                    gemini_schema[key] = {
                        prop_name: self._convert_schema_for_gemini(prop_schema)
                        for prop_name, prop_schema in value.items()
                    }
                elif key == 'items' and isinstance(value, dict):
                    # Recursively convert array items schema
                    gemini_schema[key] = self._convert_schema_for_gemini(value)
                elif key == 'required' and isinstance(value, list):
                    # Ensure required is a list of strings
                    gemini_schema[key] = [str(item) for item in value]
                else:
                    gemini_schema[key] = value
        
        # Ensure required fields exist
        if 'type' not in gemini_schema:
            gemini_schema['type'] = 'object'
        if gemini_schema['type'] == 'object' and 'properties' not in gemini_schema:
            gemini_schema['properties'] = {}
        
        return gemini_schema

    def _trim_history(self):
        """Keep conversation history within reasonable bounds."""
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length:]
    
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
        if hasattr(self, 'session') and self.session:
            try:
                await self.session.close()
            except Exception as e:
                logging.error(f"Error closing session: {e}")
    
    # provider_name, model_name and system_prompt are already implemented via memory mixin, base class and instance attribute


class PersistentGeminiClient(BasePersistentLLMClient, GeminiClient):
    """
    Custom GeminiClient that maintains persistent MCP connections.
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