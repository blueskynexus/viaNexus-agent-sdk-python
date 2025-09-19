"""
Client-agnostic conversation memory system for viaNexus Agent SDK.

This module provides universal memory management that works with any LLM client
(Anthropic, Gemini, OpenAI, etc.) through a standardized message format and
pluggable storage backends.
"""

from .base_memory import (
    UniversalMessage,
    ConversationSession,
    MessageRole,
    MessageType,
    BaseMemoryStore,
    MessageConverter
)
from .memory_mixin import ConversationMemoryMixin
from .session_manager import SessionManager

__all__ = [
    "UniversalMessage",
    "ConversationSession", 
    "MessageRole",
    "MessageType",
    "BaseMemoryStore",
    "MessageConverter",
    "ConversationMemoryMixin",
    "SessionManager"
]
