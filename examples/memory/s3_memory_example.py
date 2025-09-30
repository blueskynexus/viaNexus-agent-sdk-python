#!/usr/bin/env python3
"""
S3 memory store example (implementation template).
This shows how to implement a production-ready S3 backend for conversation storage.
"""

import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.memory.base_memory import BaseMemoryStore, UniversalMessage, ConversationSession, MessageType, MessageRole


class S3MemoryStore(BaseMemoryStore):
    """
    S3-based conversation memory storage (implementation template).
    
    This is a template implementation showing how to create an S3 backend.
    In production, you would need to add proper error handling, retry logic,
    connection pooling, and other production considerations.
    
    IMPORTANT: When working with ConversationSession objects, always use:
    - session.session_id (NOT session.memory_session_id)
    - session.user_id
    - session.last_activity
    
    The 'memory_session_id' is a property of the client/mixin, not the session object.
    """
    
    def __init__(
        self, 
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        prefix: str = "conversations/"
    ):
        self.bucket_name = bucket_name
        self.prefix = prefix.rstrip('/') + '/'
        self.region_name = region_name
        
        # In a real implementation, you would initialize boto3 client here
        # self.s3_client = boto3.client(
        #     's3',
        #     aws_access_key_id=aws_access_key_id,
        #     aws_secret_access_key=aws_secret_access_key,
        #     region_name=region_name
        # )
        
        # For this template, we'll use a mock storage
        self._mock_storage = {}
        
        logging.info(f"S3MemoryStore initialized (MOCK) - bucket: {bucket_name}, prefix: {prefix}")
    
    def _get_session_key(self, session_id: str) -> str:
        """Get S3 key for session metadata."""
        return f"{self.prefix}sessions/{session_id}.json"
    
    def _get_messages_key(self, session_id: str) -> str:
        """Get S3 key for session messages."""
        return f"{self.prefix}messages/{session_id}.jsonl"
    
    async def save_message(self, message: UniversalMessage) -> bool:
        """Save a message to S3."""
        try:
            session_id = message.session_id
            if not session_id:
                logging.error("Message has no session_id")
                return False
            
            messages_key = self._get_messages_key(session_id)
            
            # In real S3 implementation, you would:
            # 1. Get existing messages file
            # 2. Append new message
            # 3. Upload back to S3
            # For JSONL format, you might use S3 multipart uploads
            
            # Mock implementation
            if messages_key not in self._mock_storage:
                self._mock_storage[messages_key] = []
            
            self._mock_storage[messages_key].append(message.to_json())
            
            logging.debug(f"[MOCK S3] Saved message to {messages_key}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving message to S3: {e}")
            return False
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        before_message_id: Optional[str] = None,
        message_types: Optional[List[MessageType]] = None
    ) -> List[UniversalMessage]:
        """Retrieve conversation history from S3."""
        try:
            messages_key = self._get_messages_key(session_id)
            
            # In real S3 implementation:
            # response = self.s3_client.get_object(Bucket=self.bucket_name, Key=messages_key)
            # content = response['Body'].read().decode('utf-8')
            
            # Mock implementation
            if messages_key not in self._mock_storage:
                return []
            
            messages = []
            for json_line in self._mock_storage[messages_key]:
                try:
                    message = UniversalMessage.from_json(json_line)
                    messages.append(message)
                except Exception as e:
                    logging.warning(f"Skipping corrupted message: {e}")
            
            # Apply filters
            if message_types:
                messages = [msg for msg in messages if msg.message_type in message_types]
            
            if before_message_id:
                cutoff_index = None
                for i, msg in enumerate(messages):
                    if msg.message_id == before_message_id:
                        cutoff_index = i
                        break
                if cutoff_index is not None:
                    messages = messages[:cutoff_index]
            
            if limit:
                messages = messages[-limit:]
            
            logging.debug(f"[MOCK S3] Retrieved {len(messages)} messages from {messages_key}")
            return messages
            
        except Exception as e:
            logging.error(f"Error retrieving conversation history from S3: {e}")
            return []
    
    async def save_session(self, session: ConversationSession) -> bool:
        """Save session metadata to S3."""
        try:
            # Note: ConversationSession uses session.session_id, not session.memory_session_id
            session_key = self._get_session_key(session.session_id)
            
            # In real S3 implementation:
            # self.s3_client.put_object(
            #     Bucket=self.bucket_name,
            #     Key=session_key,
            #     Body=json.dumps(session.to_dict(), default=str),
            #     ContentType='application/json'
            # )
            
            # Mock implementation
            self._mock_storage[session_key] = session.to_dict()
            
            logging.debug(f"[MOCK S3] Saved session to {session_key}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving session to S3: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve session metadata from S3."""
        try:
            session_key = self._get_session_key(session_id)
            
            # Mock implementation
            if session_key not in self._mock_storage:
                return None
            
            session_data = self._mock_storage[session_key]
            return ConversationSession.from_dict(session_data)
            
        except Exception as e:
            logging.error(f"Error retrieving session from S3: {e}")
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
        """Delete a conversation session and all messages from S3."""
        try:
            session_key = self._get_session_key(session_id)
            messages_key = self._get_messages_key(session_id)
            
            # In real S3 implementation:
            # self.s3_client.delete_object(Bucket=self.bucket_name, Key=session_key)
            # self.s3_client.delete_object(Bucket=self.bucket_name, Key=messages_key)
            
            # Mock implementation
            self._mock_storage.pop(session_key, None)
            self._mock_storage.pop(messages_key, None)
            
            logging.debug(f"[MOCK S3] Deleted session {session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting session from S3: {e}")
            return False
    
    async def search_messages(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_ids: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[UniversalMessage]:
        """Search across messages in S3."""
        try:
            results = []
            query_lower = query.lower()
            
            # In real S3 implementation, you might use:
            # 1. S3 Select for server-side filtering
            # 2. ElasticSearch/OpenSearch for full-text search
            # 3. Athena for SQL-like queries
            # 4. Lambda functions for complex processing
            
            # Mock implementation - search through all stored messages
            for key, content in self._mock_storage.items():
                if key.startswith(f"{self.prefix}messages/"):
                    if isinstance(content, list):  # Messages file
                        for json_line in content:
                            try:
                                message = UniversalMessage.from_json(json_line)
                                
                                # Apply filters
                                if user_id and message.user_id != user_id:
                                    continue
                                
                                if session_ids and message.session_id not in session_ids:
                                    continue
                                
                                # Simple text search
                                content_str = str(message.content).lower()
                                if query_lower in content_str:
                                    results.append(message)
                                    if len(results) >= limit:
                                        break
                                        
                            except Exception as e:
                                logging.warning(f"Skipping corrupted message in search: {e}")
                
                if len(results) >= limit:
                    break
            
            # Sort by timestamp
            results.sort(key=lambda x: x.timestamp or datetime.min, reverse=True)
            
            logging.debug(f"[MOCK S3] Search found {len(results)} messages")
            return results[:limit]
            
        except Exception as e:
            logging.error(f"Error searching messages in S3: {e}")
            return []
    
    async def cleanup_old_sessions(self, older_than_days: int) -> int:
        """Clean up sessions older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            sessions_to_delete = []
            
            # In real S3 implementation, you would:
            # 1. List objects with session prefix
            # 2. Check last modified dates
            # 3. Use S3 lifecycle policies for automatic cleanup
            
            # Mock implementation
            for key, content in self._mock_storage.items():
                if key.startswith(f"{self.prefix}sessions/"):
                    try:
                        session_data = content
                        session = ConversationSession.from_dict(session_data)
                        if session.last_activity and session.last_activity < cutoff_date:
                            # Correct: use session.session_id (not session.memory_session_id)
                            sessions_to_delete.append(session.session_id)
                    except Exception:
                        pass
            
            for session_id in sessions_to_delete:
                await self.delete_session(session_id)
            
            logging.info(f"[MOCK S3] Cleaned up {len(sessions_to_delete)} old sessions")
            return len(sessions_to_delete)
            
        except Exception as e:
            logging.error(f"Error cleaning up old sessions: {e}")
            return 0
    
    async def get_user_sessions(
        self, 
        user_id: str, 
        limit: Optional[int] = None
    ) -> List[ConversationSession]:
        """Get all sessions for a specific user."""
        try:
            sessions = []
            
            # In real S3 implementation, you would:
            # 1. Use object tagging for user_id
            # 2. Use prefix-based organization
            # 3. Maintain user index in DynamoDB
            
            # Mock implementation
            for key, content in self._mock_storage.items():
                if key.startswith(f"{self.prefix}sessions/"):
                    try:
                        session_data = content
                        session = ConversationSession.from_dict(session_data)
                        # Correct: use session.user_id (ConversationSession attribute)
                        if session.user_id == user_id:
                            sessions.append(session)
                    except Exception:
                        pass
            
            # Sort by last activity
            sessions.sort(key=lambda x: x.last_activity or datetime.min, reverse=True)
            
            if limit:
                sessions = sessions[:limit]
            
            return sessions
            
        except Exception as e:
            logging.error(f"Error getting user sessions: {e}")
            return []


async def demo_s3_memory_store():
    """Demonstrate S3 memory store usage."""
    print("☁️  S3 MEMORY STORE DEMO (MOCK)")
    print("=" * 60)
    print("This demo shows how to implement S3-based conversation storage.")
    print("In production, this would use real AWS S3 with boto3.\n")
    
    # Create S3 memory store
    s3_store = S3MemoryStore(
        bucket_name="my-conversations-bucket",
        prefix="viaNexus/conversations/",
        region_name="us-west-2"
    )
    
    # Create a session
    session = ConversationSession(
        session_id="s3_demo_session",
        user_id="enterprise_user_001",
        client_type="anthropic",
        system_prompt="You are a financial advisor",
        session_metadata={"department": "trading", "region": "us-west"}
    )
    
    print("💾 Saving session to S3...")
    await s3_store.save_session(session)
    
    # Save some messages
    messages = [
        UniversalMessage(
            role=MessageRole.USER,
            content="What's the outlook for renewable energy stocks?",
            session_id="s3_demo_session",
            user_id="enterprise_user_001",
            provider="anthropic"
        ),
        UniversalMessage(
            role=MessageRole.ASSISTANT, 
            content="Renewable energy stocks show strong potential...",
            session_id="s3_demo_session",
            user_id="enterprise_user_001",
            provider="anthropic"
        ),
        UniversalMessage(
            role=MessageRole.USER,
            content="Which specific companies should I consider?",
            session_id="s3_demo_session", 
            user_id="enterprise_user_001",
            provider="anthropic"
        )
    ]
    
    print("📝 Saving messages to S3...")
    for msg in messages:
        await s3_store.save_message(msg)
    
    # Retrieve conversation
    print("📚 Loading conversation from S3...")
    history = await s3_store.get_conversation_history("s3_demo_session")
    print(f"✓ Loaded {len(history)} messages")
    
    for i, msg in enumerate(history, 1):
        print(f"  {i}. [{msg.role.value}] {str(msg.content)[:60]}...")
    
    # Search messages
    print("\n🔍 Searching messages...")
    search_results = await s3_store.search_messages("renewable energy")
    print(f"✓ Found {len(search_results)} matching messages")
    
    # Get user sessions
    print("\n👤 Getting user sessions...")
    user_sessions = await s3_store.get_user_sessions("enterprise_user_001")
    print(f"✓ User has {len(user_sessions)} sessions")
    
    print("\n✅ S3 memory store demo completed!")
    print("💡 In production, this would provide:")
    print("   - Unlimited storage capacity")
    print("   - Cross-region replication")
    print("   - Automatic lifecycle management")
    print("   - Integration with AWS analytics services")


async def main():
    """Run S3 memory store demonstration."""
    try:
        await demo_s3_memory_store()
        
        print("\n" + "=" * 60)
        print("📋 Production Implementation Notes:")
        print("=" * 60)
        print("1. Install: pip install boto3")
        print("2. Set up AWS credentials")
        print("3. Implement proper error handling")
        print("4. Add retry logic with exponential backoff")
        print("5. Use S3 lifecycle policies for cost optimization")
        print("6. Consider using S3 Select for server-side filtering")
        print("7. Implement connection pooling")
        print("8. Add monitoring and metrics")
        print("9. Use DynamoDB for session indexing")
        print("10. Consider ElasticSearch for advanced search")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("S3 demo error")


if __name__ == "__main__":
    asyncio.run(main())
