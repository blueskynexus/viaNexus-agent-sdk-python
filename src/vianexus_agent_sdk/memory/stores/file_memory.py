"""
File-based conversation storage for persistent local memory.
"""

import os
import json
import aiofiles
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging
from pathlib import Path

from ..base_memory import BaseMemoryStore, UniversalMessage, ConversationSession, MessageType


class FileMemoryStore(BaseMemoryStore):
    """File-based storage for conversations (simple persistence)."""
    
    def __init__(self, storage_dir: str = "conversation_memory"):
        """
        Initialize file-based memory store.
        
        Args:
            storage_dir: Directory to store conversation files
        """
        self.storage_dir = Path(storage_dir)
        self.sessions_dir = self.storage_dir / "sessions"
        self.messages_dir = self.storage_dir / "messages"
        
        # Create directories
        self.storage_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        self.messages_dir.mkdir(exist_ok=True)
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get session metadata file path."""
        return self.sessions_dir / f"{session_id}.json"
    
    def _get_messages_file(self, session_id: str) -> Path:
        """Get messages file path for a session."""
        return self.messages_dir / f"{session_id}.jsonl"
    
    async def save_message(self, message: UniversalMessage) -> bool:
        """Save a message to file."""
        try:
            session_id = message.session_id
            if not session_id:
                logging.error("Message has no session_id")
                return False
            
            messages_file = self._get_messages_file(session_id)
            
            # Append message to JSONL file
            async with aiofiles.open(messages_file, mode='a', encoding='utf-8') as f:
                await f.write(message.to_json() + '\n')
            
            logging.debug(f"Saved message to file: {message.role.value}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving message to file: {e}")
            return False
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        message_types: Optional[List[MessageType]] = None
    ) -> List[UniversalMessage]:
        """Retrieve conversation history from file."""
        try:
            messages_file = self._get_messages_file(session_id)
            
            if not messages_file.exists():
                return []
            
            messages = []
            
            # Read messages from JSONL file
            async with aiofiles.open(messages_file, mode='r', encoding='utf-8') as f:
                async for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message = UniversalMessage.from_json(line)
                            messages.append(message)
                        except Exception as e:
                            logging.warning(f"Skipping corrupted message line: {e}")
            
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
            
            # Apply limit (get most recent)
            if limit:
                messages = messages[-limit:]
            
            logging.debug(f"Retrieved {len(messages)} messages from file")
            return messages
            
        except Exception as e:
            logging.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def save_session(self, session: ConversationSession) -> bool:
        """Save session metadata to file."""
        try:
            session_file = self._get_session_file(session.session_id)
            
            async with aiofiles.open(session_file, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(session.to_dict(), default=str, ensure_ascii=False))
            
            logging.debug(f"Saved session to file: {session.session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve session metadata from file."""
        try:
            session_file = self._get_session_file(session_id)
            
            if not session_file.exists():
                return None
            
            async with aiofiles.open(session_file, mode='r', encoding='utf-8') as f:
                data = json.loads(await f.read())
                return ConversationSession.from_dict(data)
                
        except Exception as e:
            logging.error(f"Error retrieving session: {e}")
            return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp."""
        try:
            session = await self.get_session(session_id)
            if session:
                session.update_activity()
                return await self.save_session(session)
            return False
        except Exception as e:
            logging.error(f"Error updating session activity: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session and all messages."""
        try:
            session_file = self._get_session_file(session_id)
            messages_file = self._get_messages_file(session_id)
            
            # Remove files if they exist
            if session_file.exists():
                session_file.unlink()
            if messages_file.exists():
                messages_file.unlink()
            
            logging.debug(f"Deleted session files: {session_id}")
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
        """Search across message files."""
        try:
            results = []
            query_lower = query.lower()
            
            # Determine which sessions to search
            if session_ids:
                search_sessions = session_ids
            else:
                # Get all session files
                search_sessions = [f.stem for f in self.sessions_dir.glob("*.json")]
            
            # Filter by user if specified
            if user_id:
                filtered_sessions = []
                for session_id in search_sessions:
                    session = await self.get_session(session_id)
                    if session and session.user_id == user_id:
                        filtered_sessions.append(session_id)
                search_sessions = filtered_sessions
            
            # Search through messages
            for session_id in search_sessions:
                messages = await self.get_conversation_history(session_id)
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
            
            # Check all session files
            for session_file in self.sessions_dir.glob("*.json"):
                session_id = session_file.stem
                session = await self.get_session(session_id)
                
                if session and session.last_activity and session.last_activity < cutoff_date:
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
            sessions = []
            
            # Check all session files
            for session_file in self.sessions_dir.glob("*.json"):
                session_id = session_file.stem
                session = await self.get_session(session_id)
                
                if session and session.user_id == user_id:
                    sessions.append(session)
            
            # Sort by last activity (most recent first)
            sessions.sort(key=lambda x: x.last_activity or datetime.min, reverse=True)
            
            if limit:
                sessions = sessions[:limit]
            
            return sessions
            
        except Exception as e:
            logging.error(f"Error getting user sessions: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        try:
            session_count = len(list(self.sessions_dir.glob("*.json")))
            message_count = 0
            
            for messages_file in self.messages_dir.glob("*.jsonl"):
                try:
                    async with aiofiles.open(messages_file, mode='r', encoding='utf-8') as f:
                        async for line in f:
                            if line.strip():
                                message_count += 1
                except Exception:
                    pass
            
            return {
                "total_sessions": session_count,
                "total_messages": message_count,
                "storage_path": str(self.storage_dir)
            }
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return {}
