"""
Unified LLM Client Factory for creating clients based on configuration.
"""

import logging
from typing import Dict, Any, Optional, Type, Union
from enum import Enum

from .base_llm_client import BaseLLMClient, BasePersistentLLMClient
from .anthropic_client import AnthropicClient, PersistentAnthropicClient
from .openai_client import OpenAiClient, PersistentOpenAiClient
from .gemini_client import GeminiClient, PersistentGeminiClient
from vianexus_agent_sdk.memory import BaseMemoryStore


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class LLMClientFactory:
    """
    Factory for creating unified LLM clients based on configuration.
    
    The factory automatically detects the appropriate LLM provider based on:
    1. Explicit 'provider' field in config
    2. Model name patterns (e.g., 'gpt-' for OpenAI, 'claude-' for Anthropic, 'gemini-' for Gemini)
    3. API key environment variable patterns
    4. Fallback to specified default provider
    
    Usage Examples:
    
    # Automatic detection based on model name
    config = {
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_API_KEY": "sk-...",
        "agentServers": {"viaNexus": {...}}
    }
    client = LLMClientFactory.create_client(config)
    
    # Explicit provider specification
    config = {
        "provider": "anthropic",
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "LLM_API_KEY": "sk-ant-...",
        "agentServers": {"viaNexus": {...}}
    }
    client = LLMClientFactory.create_client(config)
    
    # With memory configuration
    client = LLMClientFactory.create_client_with_memory(
        config, 
        memory_type="file", 
        storage_path="./conversations"
    )
    
    # Persistent client
    persistent_client = LLMClientFactory.create_persistent_client(config)
    """
    
    # Provider detection patterns
    MODEL_PATTERNS = {
        LLMProvider.OPENAI: ["gpt-", "o1-", "text-davinci", "text-curie", "text-babbage", "text-ada"],
        LLMProvider.ANTHROPIC: ["claude-", "claude_"],
        LLMProvider.GEMINI: ["gemini-", "gemini_", "bison", "gecko"]
    }
    
    API_KEY_PATTERNS = {
        LLMProvider.OPENAI: ["sk-", "sk_"],
        LLMProvider.ANTHROPIC: ["sk-ant-"],
        LLMProvider.GEMINI: ["AI"]  # Google API keys often contain "AI"
    }
    
    # Client class mappings
    CLIENT_CLASSES = {
        LLMProvider.ANTHROPIC: AnthropicClient,
        LLMProvider.OPENAI: OpenAiClient,
        LLMProvider.GEMINI: GeminiClient
    }
    
    PERSISTENT_CLIENT_CLASSES = {
        LLMProvider.ANTHROPIC: PersistentAnthropicClient,
        LLMProvider.OPENAI: PersistentOpenAiClient,
        LLMProvider.GEMINI: PersistentGeminiClient
    }
    
    @classmethod
    def detect_provider(cls, config: Dict[str, Any]) -> LLMProvider:
        """
        Automatically detect the LLM provider based on configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Detected LLM provider
            
        Raises:
            ValueError: If provider cannot be detected
        """
        # 1. Check explicit provider field
        if "provider" in config:
            provider_str = config["provider"].lower()
            for provider in LLMProvider:
                if provider.value == provider_str:
                    logging.info(f"Provider explicitly specified: {provider.value}")
                    return provider
            raise ValueError(f"Unknown provider specified: {provider_str}")
        
        # 2. Check model name patterns
        model_name = config.get("LLM_MODEL", "").lower()
        if model_name:
            for provider, patterns in cls.MODEL_PATTERNS.items():
                if any(model_name.startswith(pattern.lower()) for pattern in patterns):
                    logging.info(f"Provider detected from model name '{model_name}': {provider.value}")
                    return provider
        
        # 3. Check API key patterns
        api_key = config.get("LLM_API_KEY", "")
        if api_key:
            for provider, patterns in cls.API_KEY_PATTERNS.items():
                if any(api_key.startswith(pattern) for pattern in patterns):
                    logging.info(f"Provider detected from API key pattern: {provider.value}")
                    return provider
        
        # 4. Fallback - check for provider-specific config sections
        if "anthropic" in str(config).lower():
            logging.info("Provider detected from config content: anthropic")
            return LLMProvider.ANTHROPIC
        elif "openai" in str(config).lower():
            logging.info("Provider detected from config content: openai")
            return LLMProvider.OPENAI
        elif "gemini" in str(config).lower():
            logging.info("Provider detected from config content: gemini")
            return LLMProvider.GEMINI
        
        # Cannot detect provider
        raise ValueError(
            "Cannot detect LLM provider. Please specify 'provider' in config or ensure "
            "LLM_MODEL/LLM_API_KEY follows recognizable patterns. "
            f"Supported providers: {[p.value for p in LLMProvider]}"
        )
    
    @classmethod
    def create_client(
        cls,
        config: Dict[str, Any],
        provider: Optional[Union[str, LLMProvider]] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        Create a standard LLM client based on configuration.
        
        Args:
            config: Configuration dictionary
            provider: Optional explicit provider (overrides auto-detection)
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured LLM client instance
        """
        # Resolve provider
        if provider is None:
            detected_provider = cls.detect_provider(config)
        elif isinstance(provider, str):
            detected_provider = LLMProvider(provider.lower())
        else:
            detected_provider = provider
        
        # Get client class
        client_class = cls.CLIENT_CLASSES[detected_provider]
        
        # Create client with default memory configuration
        logging.info(f"Creating {detected_provider.value} client with InMemoryStore")
        return client_class.with_in_memory_store(config, **kwargs)
    
    @classmethod
    def create_persistent_client(
        cls,
        config: Dict[str, Any],
        provider: Optional[Union[str, LLMProvider]] = None,
        **kwargs
    ) -> BasePersistentLLMClient:
        """
        Create a persistent LLM client based on configuration.
        
        Args:
            config: Configuration dictionary
            provider: Optional explicit provider (overrides auto-detection)
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured persistent LLM client instance
        """
        # Resolve provider
        if provider is None:
            detected_provider = cls.detect_provider(config)
        elif isinstance(provider, str):
            detected_provider = LLMProvider(provider.lower())
        else:
            detected_provider = provider
        
        # Get persistent client class
        client_class = cls.PERSISTENT_CLIENT_CLASSES[detected_provider]
        
        # Create persistent client with default memory configuration
        logging.info(f"Creating persistent {detected_provider.value} client with InMemoryStore")
        return client_class.with_in_memory_store(config, **kwargs)
    
    @classmethod
    def create_client_with_memory(
        cls,
        config: Dict[str, Any],
        memory_type: str = "in_memory",
        storage_path: str = "conversations",
        memory_store: Optional[BaseMemoryStore] = None,
        provider: Optional[Union[str, LLMProvider]] = None,
        **kwargs
    ) -> BaseLLMClient:
        """
        Create an LLM client with specific memory configuration.
        
        Args:
            config: Configuration dictionary
            memory_type: Type of memory store ("in_memory", "file", "none")
            storage_path: Path for file-based storage (if memory_type="file")
            memory_store: Custom memory store instance (overrides memory_type)
            provider: Optional explicit provider (overrides auto-detection)
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured LLM client instance
        """
        # Resolve provider
        if provider is None:
            detected_provider = cls.detect_provider(config)
        elif isinstance(provider, str):
            detected_provider = LLMProvider(provider.lower())
        else:
            detected_provider = provider
        
        # Get client class
        client_class = cls.CLIENT_CLASSES[detected_provider]
        
        # Create client based on memory configuration
        if memory_store is not None:
            logging.info(f"Creating {detected_provider.value} client with custom memory store")
            return client_class(config=config, memory_store=memory_store, **kwargs)
        elif memory_type == "in_memory":
            logging.info(f"Creating {detected_provider.value} client with InMemoryStore")
            return client_class.with_in_memory_store(config, **kwargs)
        elif memory_type == "file":
            logging.info(f"Creating {detected_provider.value} client with FileMemoryStore at {storage_path}")
            return client_class.with_file_memory_store(config, storage_path=storage_path, **kwargs)
        elif memory_type == "none":
            logging.info(f"Creating {detected_provider.value} client without memory")
            return client_class.without_memory(config, **kwargs)
        else:
            raise ValueError(f"Unknown memory_type: {memory_type}. Supported: 'in_memory', 'file', 'none'")
    
    @classmethod
    def create_persistent_client_with_memory(
        cls,
        config: Dict[str, Any],
        memory_type: str = "in_memory",
        storage_path: str = "conversations",
        memory_store: Optional[BaseMemoryStore] = None,
        provider: Optional[Union[str, LLMProvider]] = None,
        **kwargs
    ) -> BasePersistentLLMClient:
        """
        Create a persistent LLM client with specific memory configuration.
        
        Args:
            config: Configuration dictionary
            memory_type: Type of memory store ("in_memory", "file", "none")
            storage_path: Path for file-based storage (if memory_type="file")
            memory_store: Custom memory store instance (overrides memory_type)
            provider: Optional explicit provider (overrides auto-detection)
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured persistent LLM client instance
        """
        # Resolve provider
        if provider is None:
            detected_provider = cls.detect_provider(config)
        elif isinstance(provider, str):
            detected_provider = LLMProvider(provider.lower())
        else:
            detected_provider = provider
        
        # Get persistent client class
        client_class = cls.PERSISTENT_CLIENT_CLASSES[detected_provider]
        
        # Create persistent client based on memory configuration
        if memory_store is not None:
            logging.info(f"Creating persistent {detected_provider.value} client with custom memory store")
            return client_class(config=config, memory_store=memory_store, **kwargs)
        elif memory_type == "in_memory":
            logging.info(f"Creating persistent {detected_provider.value} client with InMemoryStore")
            return client_class.with_in_memory_store(config, **kwargs)
        elif memory_type == "file":
            logging.info(f"Creating persistent {detected_provider.value} client with FileMemoryStore at {storage_path}")
            return client_class.with_file_memory_store(config, storage_path=storage_path, **kwargs)
        elif memory_type == "none":
            logging.info(f"Creating persistent {detected_provider.value} client without memory")
            return client_class.without_memory(config, **kwargs)
        else:
            raise ValueError(f"Unknown memory_type: {memory_type}. Supported: 'in_memory', 'file', 'none'")
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider names."""
        return [provider.value for provider in LLMProvider]
    
    @classmethod
    def get_provider_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about supported providers and their detection patterns."""
        return {
            provider.value: {
                "model_patterns": cls.MODEL_PATTERNS[provider],
                "api_key_patterns": cls.API_KEY_PATTERNS[provider],
                "client_class": cls.CLIENT_CLASSES[provider].__name__,
                "persistent_client_class": cls.PERSISTENT_CLIENT_CLASSES[provider].__name__
            }
            for provider in LLMProvider
        }
