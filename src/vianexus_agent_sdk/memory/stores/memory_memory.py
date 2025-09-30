"""
In-memory conversation storage for testing and development.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from ..base_memory import BaseMemoryStore, UniversalMessage, ConversationSession, MessageType


class InMemoryStore(BaseMemoryStore):
    """Simple in-memory storage for conversations (testing/development only)."""
    
    def __init__(self):
        self.messages: Dict[str, List[UniversalMessage]] = {}  # session_id -> messages
        self.sessions: Dict[str, ConversationSession] = {}  # session_id -> session
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        
    async def save_message(self, message: UniversalMessage) -> bool:
        """Save a message to in-memory storage."""
        try:
            session_id = message.session_id
            if not session_id:
                logging.error("Message has no session_id")
                return False
            
            if session_id not in self.messages:
                self.messages[session_id] = []
            
            self.messages[session_id].append(message)
            
            # Update session message count
            if session_id in self.sessions:
                self.sessions[session_id].message_count += 1
            
            logging.debug(f"Saved message to in-memory store: {message.role.value}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving message to memory: {e}")
            return False
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        message_types: Optional[List[MessageType]] = None
    ) -> List[UniversalMessage]:
        """Retrieve conversation history."""
        try:
            messages = self.messages.get(session_id, [])
            
            # Filter by message types if specified
            if message_types:
                messages = [msg for msg in messages if msg.message_type in message_types]
            
            # Filter by before_message_id if specified
            if before_message_id:
                cutoff_index = None
                for i, msg in enumerate(messages):
                    if msg.message_id == before_message_id:
                        cutoff_index = i
                        break
                if cutoff_index is not None:
                    messages = messages[:cutoff_index]
            
            # Apply limit
            if limit:
                messages = messages[-limit:]
            
            logging.debug(f"Retrieved {len(messages)} messages from in-memory store")
            return messages
            
        except Exception as e:
            logging.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def save_session(self, session: ConversationSession) -> bool:
        """Save session metadata."""
        try:
            self.sessions[session.session_id] = session
            
            # Track user sessions
            if session.user_id:
                if session.user_id not in self.user_sessions:
                    self.user_sessions[session.user_id] = []
                if session.session_id not in self.user_sessions[session.user_id]:
                    self.user_sessions[session.user_id].append(session.session_id)
            
            logging.debug(f"Saved session to in-memory store: {session.session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve session metadata."""
        return self.sessions.get(session_id)
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp."""
        try:
            if session_id in self.sessions:
                self.sessions[session_id].update_activity()
                return True
            return False
        except Exception as e:
            logging.error(f"Error updating session activity: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session and all messages."""
        try:
            # Remove messages
            if session_id in self.messages:
                del self.messages[session_id]
            
            # Remove session
            session = self.sessions.pop(session_id, None)
            
            # Remove from user sessions
            if session and session.user_id:
                user_sessions = self.user_sessions.get(session.user_id, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
            
            logging.debug(f"Deleted session from in-memory store: {session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting session: {e}")
            return False
    
    async def search_messages(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_ids: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[UniversalMessage]:
        """Simple text-based search across messages."""
        try:
            results = []
            query_lower = query.lower()
            
            # Determine which sessions to search
            search_sessions = session_ids or list(self.messages.keys())
            
            # Filter by user if specified
            if user_id:
                user_session_list = self.user_sessions.get(user_id, [])
                search_sessions = [sid for sid in search_sessions if sid in user_session_list]
            
            # Search through messages
            for session_id in search_sessions:
                messages = self.messages.get(session_id, [])
                for msg in messages:
                    # Simple text search in content
                    content_str = str(msg.content).lower()
                    if query_lower in content_str:
                        results.append(msg)
                        if len(results) >= limit:
                            break
                
                if len(results) >= limit:
                    break
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp or datetime.min, reverse=True)
            
            logging.debug(f"Search found {len(results)} messages")
            return results[:limit]
            
        except Exception as e:
            logging.error(f"Error searching messages: {e}")
            return []
    
    async def cleanup_old_sessions(self, older_than_days: int) -> int:
        """Clean up sessions older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            sessions_to_delete = []
            
            for session_id, session in self.sessions.items():
                if session.last_activity and session.last_activity < cutoff_date:
                    sessions_to_delete.append(session_id)
            
            for session_id in sessions_to_delete:
                await self.delete_session(session_id)
            
            logging.info(f"Cleaned up {len(sessions_to_delete)} old sessions")
            return len(sessions_to_delete)
            
        except Exception as e:
            logging.error(f"Error cleaning up sessions: {e}")
            return 0
    
    async def get_user_sessions(
        self, 
        user_id: str, 
        limit: Optional[int] = None
    ) -> List[ConversationSession]:
        """Get all sessions for a specific user."""
        try:
            session_ids = self.user_sessions.get(user_id, [])
            sessions = [self.sessions[sid] for sid in session_ids if sid in self.sessions]
            
            # Sort by last activity (most recent first)
            sessions.sort(key=lambda x: x.last_activity or datetime.min, reverse=True)
            
            if limit:
                sessions = sessions[:limit]
            
            return sessions
            
        except Exception as e:
            logging.error(f"Error getting user sessions: {e}")
            return []
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        total_messages = sum(len(msgs) for msgs in self.messages.values())
        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "total_users": len(self.user_sessions)
        }
