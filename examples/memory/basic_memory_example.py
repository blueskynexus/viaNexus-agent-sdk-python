#!/usr/bin/env python3
"""
Basic memory integration example with AnthropicClient.
Demonstrates how to use in-memory and file-based storage for conversation persistence.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import the necessary components
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient
from vianexus_agent_sdk.memory.stores.memory_memory import InMemoryStore
from vianexus_agent_sdk.memory.stores.file_memory import FileMemoryStore


async def demo_in_memory_storage():
    """Demonstrate in-memory conversation storage."""
    print("=" * 60)
    print("IN-MEMORY STORAGE DEMO")
    print("=" * 60)
    
    # Create in-memory store
    memory_store = InMemoryStore()
    
    # Sample configuration
    config = {
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "sample.jwt.token"
            }
        },
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-sonnet-4-20250514",
        "system_prompt": "You are a helpful financial analyst assistant."
    }
    
    # Create client with memory
    client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        memory_session_id="demo_session_001",
        user_id="demo_user"
    )
    
    print("✓ Created AnthropicClient with in-memory storage")
    print(f"✓ Session info: {client.memory_get_session_info()}")
    
    # Simulate some conversations (without actually calling Anthropic API)
    print("\n📝 Simulating conversation messages...")
    
    # Save some demo messages
    await client.memory_save_message("user", "What's the current market trend?")
    await client.memory_save_message("assistant", "The market is showing positive trends...")
    await client.memory_save_message("user", "Can you analyze Apple's stock?")
    await client.memory_save_message("assistant", "Apple's stock performance shows...")
    
    # Load conversation history
    history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Loaded {len(history)} messages from memory")
    
    for msg in history:
        print(f"  [{msg.role.value}] {str(msg.content)[:50]}...")
    
    # Search conversations
    search_results = await client.memory_search_conversations("Apple stock")
    print(f"\n🔍 Search for 'Apple stock' found {len(search_results)} results")
    
    # Get storage stats
    stats = memory_store.get_stats()
    print(f"\n📊 Storage stats: {stats}")


async def demo_file_storage():
    """Demonstrate file-based conversation storage."""
    print("\n" + "=" * 60)
    print("FILE-BASED STORAGE DEMO")
    print("=" * 60)
    
    # Create file store in a temporary directory
    storage_dir = Path("demo_conversations")
    memory_store = FileMemoryStore(storage_dir=str(storage_dir))
    
    # Sample configuration
    config = {
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "sample.jwt.token"
            }
        },
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-sonnet-4-20250514"
    }
    
    # Create client with file-based memory
    client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        memory_session_id="persistent_session_001",
        user_id="demo_user"
    )
    
    print(f"✓ Created AnthropicClient with file storage at: {storage_dir}")
    
    # Save some messages
    await client.memory_save_message("user", "Hello, can you help with portfolio analysis?")
    await client.memory_save_message("assistant", "Of course! I'd be happy to help analyze your portfolio.")
    await client.memory_save_message("user", "I have positions in AAPL, MSFT, and GOOGL")
    await client.memory_save_message("assistant", "Those are solid tech stocks. Let me analyze each...")
    
    print("✓ Saved conversation to files")
    
    # Show file structure
    if storage_dir.exists():
        print(f"\n📁 Files created:")
        for file_path in storage_dir.rglob("*"):
            if file_path.is_file():
                print(f"  {file_path}")
    
    # Load history
    history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"\n✓ Loaded {len(history)} messages from files")
    
    # Create a second client instance to demonstrate persistence
    client2 = AnthropicClient(
        config=config,
        memory_store=memory_store,
        memory_session_id="persistent_session_001",  # Same session ID
        user_id="demo_user"
    )
    
    # Load history with second client
    history2 = await client2.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Second client loaded {len(history2)} messages (persistence verified)")
    
    # Get storage stats
    stats = await memory_store.get_stats()
    print(f"\n📊 Storage stats: {stats}")


async def demo_session_management():
    """Demonstrate session management features."""
    print("\n" + "=" * 60)
    print("SESSION MANAGEMENT DEMO")
    print("=" * 60)
    
    memory_store = InMemoryStore()
    
    config = {
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com", 
                "server_port": 443,
                "software_statement": "sample.jwt.token"
            }
        },
        "LLM_API_KEY": "your-anthropic-api-key"
    }
    
    # Create client for user conversations
    client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="trader_123"
    )
    
    print(f"✓ Client session: {client.memory_session_id}")
    
    # Create multiple conversation sessions
    sessions = []
    for i in range(3):
        session_id = f"trading_session_{i+1}"
        await client.memory_switch_session(session_id)
        
        # Add some messages to each session
        await client.memory_save_message("user", f"Session {i+1}: Market analysis request")
        await client.memory_save_message("assistant", f"Session {i+1}: Analysis results...")
        
        sessions.append(session_id)
        print(f"  ✓ Created session: {session_id}")
    
    # Get all user sessions
    user_sessions = await client.memory_get_user_sessions()
    print(f"\n👤 User has {len(user_sessions)} sessions:")
    
    for session in user_sessions:
        print(f"  📝 {session.memory_session_id} - {session.message_count} messages")
    
    # Switch between sessions
    await client.memory_switch_session(sessions[0])
    history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"\n🔄 Switched to {sessions[0]}, loaded {len(history)} messages")
    
    # Search across all user sessions
    search_results = await client.memory_search_conversations(
        "Market analysis", 
        all_user_sessions=True
    )
    print(f"🔍 Search across all sessions found {len(search_results)} results")


async def main():
    """Run all memory demonstration examples."""
    print("🧠 viaNexus Agent SDK - Memory System Demonstration")
    print("=" * 60)
    print("This demo shows the client-agnostic memory system capabilities.")
    print("Note: Anthropic API calls are simulated in this demo.\n")
    
    try:
        await demo_in_memory_storage()
        await demo_file_storage()
        await demo_session_management()
        
        print("\n" + "=" * 60)
        print("✅ All memory demonstrations completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("Demo error")


if __name__ == "__main__":
    asyncio.run(main())
