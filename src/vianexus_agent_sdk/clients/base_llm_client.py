"""
Abstract base class defining the unified LLM client interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from vianexus_agent_sdk.memory import BaseMemoryStore
import logging


class BaseLLMClient(ABC):
    """
    Abstract base class defining the unified interface for all LLM clients.
    
    This interface ensures consistency across Anthropic, OpenAI, and Gemini clients,
    providing a common API for factory-based client creation and usage.
    """
    
    @staticmethod
    def _validate_question(question: str) -> str:
        """
        Validate and sanitize user input questions.
        
        Args:
            question: The user's question
            
        Returns:
            Validated question string
            
        Raises:
            ValueError: If question is invalid
        """
        if not question:
            raise ValueError("Question cannot be None or empty")
        
        if not isinstance(question, str):
            raise ValueError("Question must be a string")
        
        # Strip whitespace
        question = question.strip()
        
        if not question:
            raise ValueError("Question cannot be empty or whitespace only")
        
        # Check reasonable length limits
        if len(question) > 100000:  # 100KB limit
            raise ValueError("Question is too long (max 100,000 characters)")
        
        # Basic content validation - prevent potential injection attacks
        # This is a basic check; more sophisticated validation could be added
        if question.count('\x00') > 0:
            raise ValueError("Question contains null bytes")
        
        return question
    
    # Factory Methods (Class Methods)
    @classmethod
    @abstractmethod
    def with_in_memory_store(
        cls,
        config: Dict[str, Any],
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> "BaseLLMClient":
        """
        Create client with InMemoryStore for fast, temporary conversations.
        
        Args:
            config: Client configuration dictionary
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            Client instance configured with InMemoryStore
        """
        pass
    
    @classmethod
    @abstractmethod
    def with_file_memory_store(
        cls,
        config: Dict[str, Any],
        storage_path: str = "conversations",
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> "BaseLLMClient":
        """
        Create client with FileMemoryStore for persistent local storage.
        
        Args:
            config: Client configuration dictionary
            storage_path: Directory path for conversation storage
            memory_session_id: Optional memory session identifier
            user_id: Optional user identifier
            **kwargs: Additional client parameters
            
        Returns:
            Client instance configured with FileMemoryStore
        """
        pass
    
    @classmethod
    @abstractmethod
    def without_memory(
        cls,
        config: Dict[str, Any],
        **kwargs
    ) -> "BaseLLMClient":
        """
        Create client without memory system for stateless interactions.
        
        Args:
            config: Client configuration dictionary
            **kwargs: Additional client parameters
            
        Returns:
            Client instance with memory disabled
        """
        pass
    
    # Core Interface Methods
    @abstractmethod
    async def ask_single_question(self, question: str) -> str:
        """
        Ask a single question without maintaining conversation history.
        
        Args:
            question: The question to ask
            
        Returns:
            The response as a string
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def process_query(self, query: str) -> str:
        """
        Process query with streaming output and conversation history.
        
        Args:
            query: The query to process
            
        Returns:
            Empty string (output is streamed to console)
        """
        pass
    
    # Lifecycle Methods
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the client and establish connections."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        pass
    
    # Properties
    # provider_name is implemented by ConversationMemoryMixin
    
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        # Default implementation - can be overridden by subclasses
        if hasattr(self, 'model'):
            return self.model
        elif hasattr(self, '_model_name'):
            return self._model_name
        else:
            return 'unknown'
    
    # system_prompt is implemented as an instance attribute in concrete clients


class BasePersistentLLMClient(BaseLLMClient):
    """
    Abstract base class for persistent LLM clients that maintain long-running connections.
    """
    
    @abstractmethod
    async def establish_persistent_connection(self) -> str:
        """
        Establish and maintain a persistent MCP connection.
        
        Returns:
            The MCP session ID
        """
        pass
    
    @abstractmethod
    async def close_persistent_connection(self) -> None:
        """Close the persistent MCP connection."""
        pass
    
    @abstractmethod
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
            maintain_history: Whether to maintain conversation context
            use_memory: Whether to use memory for context and persistence
            auto_establish_connection: Whether to automatically establish MCP connection if needed
            
        Returns:
            The response as a string
        """
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the persistent connection is active."""
        pass
    
    @property
    @abstractmethod
    def mcp_session_id(self) -> Optional[str]:
        """Get the current MCP session ID."""
        pass
