"""
Registry for message converters by provider.
"""

from typing import Dict
from ..base_memory import MessageConverter
from .anthropic_converter import AnthropicMessageConverter


class ConverterRegistry:
    """Registry for message converters by provider."""
    
    _converters: Dict[str, MessageConverter] = {
        "anthropic": AnthropicMessageConverter(),
    }
    
    @classmethod
    def get_converter(cls, provider: str) -> MessageConverter:
        """Get converter for a specific provider."""
        if provider not in cls._converters:
            raise ValueError(f"No converter found for provider: {provider}")
        return cls._converters[provider]
    
    @classmethod
    def register_converter(cls, provider: str, converter: MessageConverter):
        """Register a new converter."""
        cls._converters[provider] = converter
    
    @classmethod
    def list_providers(cls) -> list:
        """List all registered providers."""
        return list(cls._converters.keys())
    
    @classmethod
    def has_converter(cls, provider: str) -> bool:
        """Check if converter exists for provider."""
        return provider in cls._converters
