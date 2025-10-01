"""
Universal memory mixin that any client can use for conversation memory.
"""

from typing import Optional, List, Dict, Any
import logging
import uuid

from .base_memory import BaseMemoryStore, UniversalMessage, ConversationSession, MessageRole, MessageType
from .converters import ConverterRegistry
from .session_manager import SessionManager


class ConversationMemoryMixin:
    """
    Universal mixin that any client can use for conversation memory.
    Provides client-agnostic memory operations.
    """
    
    def __init__(
        self, 
        memory_store: Optional[BaseMemoryStore] = None,
        memory_session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        provider_name: str = "unknown",
        **kwargs
    ):
        # Memory configuration
        self.memory_store = memory_store
        self.memory_session_id = memory_session_id
        self.user_id = user_id
        self.provider_name = provider_name
        self.memory_enabled = memory_store is not None
        
        # Initialize session manager for guaranteed isolation
        self.session_manager = SessionManager(memory_store) if memory_store else None
        
        # Get the appropriate converter if available
        self.message_converter = None
        if provider_name != "unknown" and ConverterRegistry.has_converter(provider_name):
            self.message_converter = ConverterRegistry.get_converter(provider_name)
        
        # Memory policies
        self.memory_config = {
            'auto_persist': True,
            'max_context_messages': 1000,
            'compression_threshold': 200,
            'retention_days': 30,
            'load_history_on_init': False,
            'guarantee_isolation': True  # New: Guarantee session isolation
        }
        
        # Session management
        self._session_initialized = False
        self._current_session: Optional[ConversationSession] = None
        
        # Call parent __init__ if this is used as a mixin
        super().__init__(**kwargs)
    
    def configure_memory(self, **config) -> None:
        """Configure memory behavior."""
        self.memory_config.update(config)
    
    async def memory_initialize_session(
        self, 
        context_tags: Optional[List[str]] = None,
        session_metadata: Optional[Dict] = None,
        system_prompt: Optional[str] = None
    ) -> bool:
        """Initialize or resume a conversation session with guaranteed isolation."""
        if not self.memory_enabled or self._session_initialized:
            return True
        
        if not self.session_manager:
            logging.error("Session manager not initialized")
            return False
        
        try:
            # Generate memory session ID if not provided using session manager
            if not self.memory_session_id:
                self.memory_session_id = self.session_manager.generate_session_id(
                    user_id=self.user_id,
                    client_type=self.provider_name,
                    context=session_metadata.get("context") if session_metadata else None
                )
            
            # Prepare session metadata with MCP session correlation
            enhanced_metadata = session_metadata or {}
            
            # Add MCP session correlation if available (but don't use as primary ID)
            mcp_session_id = self._get_mcp_session_id()
            if mcp_session_id:
                enhanced_metadata["mcp_session_id"] = mcp_session_id
                enhanced_metadata["mcp_session_correlation"] = f"memory:{self.memory_session_id} <-> mcp:{mcp_session_id}"
                logging.debug(f"Correlating memory session {self.memory_session_id} with MCP session {mcp_session_id}")
            
            # Ensure session exists with guaranteed isolation
            session = await self.session_manager.ensure_session_exists(
                session_id=self.memory_session_id,
                user_id=self.user_id,
                client_type=self.provider_name,
                system_prompt=system_prompt or getattr(self, 'system_prompt', None),
                context_tags=context_tags,
                session_metadata=enhanced_metadata
            )
            
            # Store current session reference
            self._current_session = session
            self._session_initialized = True
            
            logging.info(f"Initialized isolated session: {self.memory_session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize memory session: {e}")
            return False
    
    async def memory_save_message(
        self, 
        role: str, 
        content: Any,
        message_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Save a message to memory storage."""
        if not self.memory_enabled:
            return True
        
        try:
            # Ensure session is initialized
            await self.memory_initialize_session()
            
            # Determine message type
            msg_type = MessageType.TEXT
            if message_type:
                try:
                    msg_type = MessageType(message_type)
                except ValueError:
                    logging.warning(f"Unknown message type: {message_type}, using TEXT")
            
            # Create universal message
            universal_message = UniversalMessage(
                role=MessageRole(role),
                content=content,
                message_type=msg_type,
                session_id=self.memory_session_id,
                user_id=self.user_id,
                provider=self.provider_name,
                metadata=metadata
            )
            
            # Save to storage
            success = await self.memory_store.save_message(universal_message)
            
            if success:
                # Update session activity
                await self.memory_store.update_session_activity(self.memory_session_id)
                logging.debug(f"Saved {role} message to memory")
            
            return success
            
        except Exception as e:
            logging.error(f"Failed to save message to memory: {e}")
            return False
    
    async def memory_load_history(
        self, 
        limit: Optional[int] = None,
        convert_to_provider_format: bool = True,
        message_types: Optional[List[str]] = None
    ) -> List[Any]:
        """Load conversation history from memory."""
        if not self.memory_enabled:
            return []
        
        try:
            # Ensure session is initialized
            await self.memory_initialize_session()
            
            # Convert message type strings to enums
            type_filters = None
            if message_types:
                type_filters = []
                for msg_type in message_types:
                    try:
                        type_filters.append(MessageType(msg_type))
                    except ValueError:
                        logging.warning(f"Unknown message type filter: {msg_type}")
            
            # Load universal messages
            universal_messages = await self.memory_store.get_conversation_history(
                self.memory_session_id,
                limit=limit or self.memory_config['max_context_messages'],
                message_types=type_filters
            )
            
            # Convert to provider format if requested and converter available
            if convert_to_provider_format and self.message_converter:
                return self.message_converter.from_universal_batch(universal_messages)
            
            return universal_messages
            
        except Exception as e:
            logging.error(f"Failed to load conversation history: {e}")
            return []
    
    async def memory_search_conversations(
        self,
        query: str,
        limit: int = 20,
        all_user_sessions: bool = False
    ) -> List[UniversalMessage]:
        """Search across conversation history."""
        if not self.memory_enabled:
            return []
        
        try:
            session_ids = None
            if not all_user_sessions and self.memory_session_id:
                session_ids = [self.memory_session_id]
            
            return await self.memory_store.search_messages(
                query=query,
                user_id=self.user_id,
                session_ids=session_ids,
                limit=limit
            )
        except Exception as e:
            logging.error(f"Failed to search conversations: {e}")
            return []
    
    async def memory_clear_session(self) -> bool:
        """Clear current session from memory."""
        if not self.memory_enabled or not self.memory_session_id:
            return True
        
        try:
            success = await self.memory_store.delete_session(self.memory_session_id)
            if success:
                self._session_initialized = False
                logging.info(f"Cleared memory session: {self.memory_session_id}")
            return success
        except Exception as e:
            logging.error(f"Failed to clear session: {e}")
            return False
    
    async def memory_switch_session(
        self, 
        new_session_id: str,
        create_if_not_exists: bool = True
    ) -> bool:
        """Switch to a different conversation session with guaranteed isolation."""
        if not self.memory_enabled or not self.session_manager:
            return True
        
        try:
            # Validate new session exists or can be created
            if create_if_not_exists:
                new_session = await self.session_manager.ensure_session_exists(
                    session_id=new_session_id,
                    user_id=self.user_id,
                    client_type=self.provider_name
                )
            else:
                new_session = await self.session_manager.get_session(new_session_id)
                if not new_session:
                    logging.error(f"Session {new_session_id} does not exist")
                    return False
            
            # Switch session with proper isolation
            old_session_id = self.memory_session_id
            self.memory_session_id = new_session_id
            self._session_initialized = True  # Already validated
            self._current_session = new_session
            
            logging.info(f"Switched from session {old_session_id} to {new_session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to switch session: {e}")
            return False
    
    async def memory_get_user_sessions(self, limit: Optional[int] = None) -> List[ConversationSession]:
        """Get all sessions for the current user."""
        if not self.memory_enabled or not self.user_id:
            return []
        
        try:
            return await self.memory_store.get_user_sessions(self.user_id, limit)
        except Exception as e:
            logging.error(f"Failed to get user sessions: {e}")
            return []
    
    def memory_get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        return {
            'memory_session_id': self.memory_session_id,
            'user_id': self.user_id,
            'provider': self.provider_name,
            'memory_enabled': self.memory_enabled,
            'session_initialized': self._session_initialized,
            'has_converter': self.message_converter is not None,
            'memory_config': self.memory_config.copy()
        }
    
    async def memory_cleanup_old_sessions(self, older_than_days: int = 30) -> int:
        """Clean up old sessions (admin function)."""
        if not self.memory_enabled:
            return 0
        
        try:
            return await self.memory_store.cleanup_old_sessions(older_than_days)
        except Exception as e:
            logging.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    # Enhanced session management methods
    
    async def memory_create_isolated_session(
        self,
        session_context: Optional[str] = None,
        context_tags: Optional[List[str]] = None,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new isolated session with guaranteed uniqueness.
        
        Args:
            session_context: Context description for session naming
            context_tags: Tags for categorization
            session_metadata: Additional metadata
            
        Returns:
            New session ID
        """
        if not self.memory_enabled or not self.session_manager:
            raise RuntimeError("Memory not enabled or session manager not available")
        
        session = await self.session_manager.create_session(
            user_id=self.user_id,
            client_type=self.provider_name,
            system_prompt=getattr(self, 'system_prompt', None),
            context_tags=context_tags,
            session_metadata={
                **(session_metadata or {}),
                "context": session_context,
                "created_by": f"{self.provider_name}_client"
            }
        )
        
        return session.session_id
    
    async def memory_get_session_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics for the current session."""
        if not self.memory_enabled or not self.session_manager or not self.memory_session_id:
            return {}
        
        return await self.session_manager.get_session_statistics(self.memory_session_id)
    
    async def memory_get_isolated_session_data(self) -> Dict[str, Any]:
        """Get complete isolated data for the current session."""
        if not self.memory_enabled or not self.session_manager or not self.memory_session_id:
            return {}
        
        return await self.session_manager.isolate_session_memory(self.memory_session_id)
    
    async def memory_clone_current_session(
        self, 
        new_session_context: Optional[str] = None,
        new_user_id: Optional[str] = None
    ) -> str:
        """
        Clone the current session to a new isolated session.
        
        Args:
            new_session_context: Context for the new session
            new_user_id: User ID for the new session (keeps current if None)
            
        Returns:
            New session ID
        """
        if not self.memory_enabled or not self.session_manager or not self.memory_session_id:
            raise RuntimeError("Cannot clone session: memory not enabled or no active session")
        
        new_session = await self.session_manager.clone_session(
            source_session_id=self.memory_session_id,
            new_user_id=new_user_id
        )
        
        return new_session.session_id
    
    async def memory_list_user_sessions_with_stats(self) -> List[Dict[str, Any]]:
        """List all user sessions with detailed statistics."""
        if not self.memory_enabled or not self.session_manager or not self.user_id:
            return []
        
        return await self.session_manager.list_user_sessions(
            self.user_id, 
            include_stats=True
        )
    
    def memory_get_current_session_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the current session."""
        base_info = self.memory_get_session_info()
        
        if self._current_session:
            base_info.update({
                "session_created_at": self._current_session.created_at.isoformat() if self._current_session.created_at else None,
                "session_last_activity": self._current_session.last_activity.isoformat() if self._current_session.last_activity else None,
                "session_message_count": self._current_session.message_count,
                "session_context_tags": self._current_session.context_tags,
                "session_metadata": self._current_session.session_metadata,
                "session_isolation_guaranteed": self.memory_config.get('guarantee_isolation', False)
            })
        
        return base_info
    
    def _get_mcp_session_id(self) -> Optional[str]:
        """
        Get the current MCP session ID for correlation purposes.
        
        Returns:
            MCP session ID if available, None otherwise
        """
        try:
            # Check if this is a PersistentAnthropicClient with MCP session
            if hasattr(self, '_mcp_session_id') and self._mcp_session_id:
                return str(self._mcp_session_id)
            
            # Check if we have an active MCP session through the base client
            if hasattr(self, 'session') and self.session:
                # Try to get session info from the MCP ClientSession
                if hasattr(self.session, '_session_id'):
                    return str(self.session._session_id)
                elif hasattr(self.session, 'session_id'):
                    return str(self.session.session_id)
            
            # Check if we're in a connection context with get_session_id function
            if hasattr(self, '_connection_context') and self._connection_context:
                try:
                    readstream, writestream, get_session_id = self._connection_context
                    if get_session_id:
                        mcp_id = get_session_id()
                        if mcp_id:
                            return str(mcp_id)
                except Exception:
                    pass
            
            return None
            
        except Exception as e:
            logging.debug(f"Could not retrieve MCP session ID: {e}")
            return None
