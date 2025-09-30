"""
Core memory interfaces and data models for client-agnostic conversation storage.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Protocol
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid
import json


class MessageRole(Enum):
    """Universal message roles across all LLM providers."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    FUNCTION = "function"  # For OpenAI compatibility


class MessageType(Enum):
    """Types of messages for better categorization."""
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


@dataclass
class UniversalMessage:
    """
    Provider-agnostic message format that works with any LLM client.
    Can be converted to/from specific provider formats (Anthropic, Gemini, etc.)
    """
    role: MessageRole
    content: Any  # Flexible content - text, structured data, multimodal
    message_type: MessageType = MessageType.TEXT
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Provider-specific metadata
    provider: Optional[str] = None  # "anthropic", "gemini", "openai", etc.
    raw_content: Optional[Any] = None  # Original provider format
    
    # Conversation metadata
    token_count: Optional[int] = None
    tool_calls: Optional[List[Dict]] = None
    tool_results: Optional[List[Dict]] = None
    
    # User/context metadata
    user_id: Optional[str] = None
    context_tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        
        # Convert enums to strings
        data['role'] = self.role.value
        data['message_type'] = self.message_type.value
        
        # Convert datetime to ISO string
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversalMessage":
        """Create from dictionary (loaded from storage)."""
        # Handle enum conversion
        if isinstance(data.get('role'), str):
            data['role'] = MessageRole(data['role'])
        if isinstance(data.get('message_type'), str):
            data['message_type'] = MessageType(data['message_type'])
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string for storage."""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "UniversalMessage":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class ConversationSession:
    """Universal conversation session metadata."""
    session_id: str
    user_id: Optional[str] = None
    client_type: Optional[str] = None  # "anthropic", "gemini", etc.
    system_prompt: Optional[str] = None
    
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    message_count: int = 0
    
    # Session configuration
    max_context_length: Optional[int] = None
    memory_strategy: str = "fifo"  # "fifo", "priority", "semantic"
    
    # Context and tags
    context_tags: Optional[List[str]] = None
    session_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        
        # Convert datetime to ISO string
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.last_activity:
            data['last_activity'] = self.last_activity.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        """Create from dictionary (loaded from storage)."""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('last_activity'), str):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        
        return cls(**data)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()


class MessageConverter(Protocol):
    """Protocol for converting between provider formats and UniversalMessage."""
    
    def to_universal(self, provider_message: Any) -> UniversalMessage:
        """Convert provider-specific message to UniversalMessage."""
        ...
    
    def from_universal(self, universal_message: UniversalMessage) -> Any:
        """Convert UniversalMessage to provider-specific format."""
        ...
    
    def to_universal_batch(self, provider_messages: List[Any]) -> List[UniversalMessage]:
        """Convert batch of provider messages."""
        ...
    
    def from_universal_batch(self, universal_messages: List[UniversalMessage]) -> List[Any]:
        """Convert batch of universal messages."""
        ...


class BaseMemoryStore(ABC):
    """Client-agnostic conversation memory storage interface."""
    
    @abstractmethod
    async def save_message(self, message: UniversalMessage) -> bool:
        """Save a universal message to storage."""
        pass
    
    @abstractmethod
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        message_types: Optional[List[MessageType]] = None
    ) -> List[UniversalMessage]:
        """Retrieve conversation history with optional filtering."""
        pass
    
    @abstractmethod
    async def save_session(self, session: ConversationSession) -> bool:
        """Save session metadata."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve session metadata."""
        pass
    
    @abstractmethod
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session and all messages."""
        pass
    
    @abstractmethod
    async def search_messages(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_ids: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[UniversalMessage]:
        """Semantic search across messages."""
        pass
    
    @abstractmethod
    async def cleanup_old_sessions(self, older_than_days: int) -> int:
        """Clean up sessions older than specified days."""
        pass
    
    @abstractmethod
    async def get_user_sessions(
        self, 
        user_id: str, 
        limit: Optional[int] = None
    ) -> List[ConversationSession]:
        """Get all sessions for a specific user."""
        pass
