"""
Enhanced session management for guaranteed isolation and retrieval.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base_memory import BaseMemoryStore, ConversationSession, UniversalMessage


class SessionManager:
    """
    Manages conversation sessions with guaranteed isolation and retrieval.
    Ensures each session has its own isolated memory space.
    """
    
    def __init__(self, memory_store: BaseMemoryStore):
        self.memory_store = memory_store
        # Session registry for active sessions (prevents conflicts)
        self._active_sessions: Dict[str, ConversationSession] = {}
        # Session locks to prevent concurrent access issues
        self._session_locks: Dict[str, bool] = {}
    
    def generate_session_id(
        self, 
        user_id: Optional[str] = None, 
        client_type: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate a unique session ID with guaranteed uniqueness.
        
        Args:
            user_id: User identifier
            client_type: Type of client (anthropic, gemini, etc.)
            context: Optional context descriptor
            
        Returns:
            Unique session ID
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        parts = []
        if client_type:
            parts.append(client_type)
        if user_id:
            parts.append(user_id)
        if context:
            parts.append(context.replace(" ", "_"))
        
        parts.extend([timestamp, unique_id])
        session_id = "_".join(parts)
        
        # Ensure uniqueness (very unlikely collision, but safety first)
        counter = 0
        original_session_id = session_id
        while session_id in self._active_sessions:
            counter += 1
            session_id = f"{original_session_id}_{counter}"
        
        return session_id
    
    async def create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        client_type: Optional[str] = None,
        system_prompt: Optional[str] = None,
        context_tags: Optional[List[str]] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> ConversationSession:
        """
        Create a new conversation session with guaranteed isolation.
        
        Args:
            session_id: Specific session ID (auto-generated if None)
            user_id: User identifier
            client_type: Client type
            system_prompt: System prompt for the session
            context_tags: Tags for categorization
            session_metadata: Additional metadata
            force_new: Force creation of new session even if one exists
            
        Returns:
            ConversationSession object
            
        Raises:
            ValueError: If session_id already exists and force_new is False
        """
        # Generate session ID if not provided
        if not session_id:
            context = session_metadata.get("context", None) if session_metadata else None
            session_id = self.generate_session_id(user_id, client_type, context)
        
        # Check if session already exists
        existing_session = await self.memory_store.get_session(session_id)
        if existing_session and not force_new:
            raise ValueError(f"Session {session_id} already exists. Use force_new=True to override.")
        
        # Acquire session lock
        if session_id in self._session_locks:
            raise RuntimeError(f"Session {session_id} is currently being modified")
        
        try:
            self._session_locks[session_id] = True
            
            # Create new session
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                client_type=client_type,
                system_prompt=system_prompt,
                context_tags=context_tags or [],
                session_metadata=session_metadata or {}
            )
            
            # Save to persistent storage
            success = await self.memory_store.save_session(session)
            if not success:
                raise RuntimeError(f"Failed to save session {session_id}")
            
            # Register in active sessions
            self._active_sessions[session_id] = session
            
            logging.info(f"Created new session: {session_id}")
            return session
            
        finally:
            # Release session lock
            self._session_locks.pop(session_id, None)
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Retrieve session with guaranteed isolation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSession or None if not found
        """
        # Check active sessions first (faster)
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]
        
        # Load from persistent storage
        session = await self.memory_store.get_session(session_id)
        if session:
            # Cache in active sessions
            self._active_sessions[session_id] = session
            logging.debug(f"Loaded session from storage: {session_id}")
        
        return session
    
    async def ensure_session_exists(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        client_type: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ConversationSession:
        """
        Ensure session exists, create if not found.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            client_type: Client type
            system_prompt: System prompt
            **kwargs: Additional session metadata
            
        Returns:
            ConversationSession (existing or newly created)
        """
        session = await self.get_session(session_id)
        
        if not session:
            session = await self.create_session(
                session_id=session_id,
                user_id=user_id,
                client_type=client_type,
                system_prompt=system_prompt,
                session_metadata=kwargs
            )
        
        return session
    
    async def isolate_session_memory(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete isolated memory for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session metadata and all messages
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get all messages for this session
        messages = await self.memory_store.get_conversation_history(session_id)
        
        return {
            "session": session.to_dict(),
            "messages": [msg.to_dict() for msg in messages],
            "message_count": len(messages),
            "session_size_bytes": self._calculate_session_size(session, messages)
        }
    
    async def clone_session(
        self, 
        source_session_id: str, 
        new_session_id: Optional[str] = None,
        new_user_id: Optional[str] = None
    ) -> ConversationSession:
        """
        Clone a session with all its messages to a new session.
        
        Args:
            source_session_id: Source session to clone
            new_session_id: New session ID (auto-generated if None)
            new_user_id: New user ID (keeps original if None)
            
        Returns:
            New ConversationSession
        """
        # Get source session
        source_session = await self.get_session(source_session_id)
        if not source_session:
            raise ValueError(f"Source session {source_session_id} not found")
        
        # Generate new session ID if not provided
        if not new_session_id:
            new_session_id = self.generate_session_id(
                new_user_id or source_session.user_id,
                source_session.client_type,
                "cloned"
            )
        
        # Create new session with same metadata
        new_session = await self.create_session(
            session_id=new_session_id,
            user_id=new_user_id or source_session.user_id,
            client_type=source_session.client_type,
            system_prompt=source_session.system_prompt,
            context_tags=source_session.context_tags.copy() if source_session.context_tags else None,
            session_metadata={
                **(source_session.session_metadata or {}),
                "cloned_from": source_session_id,
                "cloned_at": datetime.utcnow().isoformat()
            }
        )
        
        # Copy all messages
        source_messages = await self.memory_store.get_conversation_history(source_session_id)
        for msg in source_messages:
            # Create new message with new session ID
            new_msg = UniversalMessage(
                role=msg.role,
                content=msg.content,
                message_type=msg.message_type,
                session_id=new_session_id,  # New session ID
                user_id=new_user_id or msg.user_id,
                provider=msg.provider,
                raw_content=msg.raw_content,
                tool_calls=msg.tool_calls,
                tool_results=msg.tool_results,
                context_tags=msg.context_tags,
                metadata={
                    **(msg.metadata or {}),
                    "cloned_from": msg.message_id,
                    "original_session": source_session_id
                }
            )
            
            await self.memory_store.save_message(new_msg)
        
        logging.info(f"Cloned session {source_session_id} to {new_session_id} with {len(source_messages)} messages")
        return new_session
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics
        """
        session = await self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}
        
        messages = await self.memory_store.get_conversation_history(session_id)
        
        # Analyze message patterns
        role_counts = {}
        message_types = {}
        providers = set()
        
        for msg in messages:
            role_counts[msg.role.value] = role_counts.get(msg.role.value, 0) + 1
            message_types[msg.message_type.value] = message_types.get(msg.message_type.value, 0) + 1
            if msg.provider:
                providers.add(msg.provider)
        
        duration = None
        if session.created_at and session.last_activity:
            duration = (session.last_activity - session.created_at).total_seconds()
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "client_type": session.client_type,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "duration_seconds": duration,
            "message_count": len(messages),
            "role_distribution": role_counts,
            "message_types": message_types,
            "providers_used": list(providers),
            "context_tags": session.context_tags,
            "session_size_bytes": self._calculate_session_size(session, messages)
        }
    
    async def list_user_sessions(
        self, 
        user_id: str, 
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all sessions for a user with optional statistics.
        
        Args:
            user_id: User identifier
            include_stats: Whether to include detailed statistics
            
        Returns:
            List of session information
        """
        sessions = await self.memory_store.get_user_sessions(user_id)
        
        result = []
        for session in sessions:
            session_info = {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "client_type": session.client_type,
                "context_tags": session.context_tags,
                "message_count": session.message_count
            }
            
            if include_stats:
                stats = await self.get_session_statistics(session.session_id)
                session_info.update(stats)
            
            result.append(session_info)
        
        return result
    
    def _calculate_session_size(
        self, 
        session: ConversationSession, 
        messages: List[UniversalMessage]
    ) -> int:
        """Calculate approximate size of session in bytes."""
        try:
            session_size = len(session.to_json() if hasattr(session, 'to_json') else str(session))
            messages_size = sum(len(msg.to_json()) for msg in messages)
            return session_size + messages_size
        except Exception:
            return 0
    
    async def cleanup_inactive_sessions(self, inactive_hours: int = 24) -> int:
        """
        Clean up sessions that have been inactive for specified hours.
        
        Args:
            inactive_hours: Hours of inactivity before cleanup
            
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=inactive_hours)
        cleanup_count = 0
        
        # Clean up active session cache
        to_remove = []
        for session_id, session in self._active_sessions.items():
            if session.last_activity and session.last_activity < cutoff_time:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self._active_sessions[session_id]
            cleanup_count += 1
        
        # Note: Persistent storage cleanup is handled by the memory store
        
        logging.info(f"Cleaned up {cleanup_count} inactive sessions from cache")
        return cleanup_count
