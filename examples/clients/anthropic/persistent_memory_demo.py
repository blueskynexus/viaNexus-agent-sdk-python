#!/usr/bin/env python3
"""
PersistentAnthropicClient Memory Demonstration.
Shows how PersistentAnthropicClient now provides immediate memory session initialization.
"""

import asyncio
import logging
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient, PersistentAnthropicClient


async def demonstrate_persistent_memory():
    """Demonstrate PersistentAnthropicClient memory capabilities."""
    print("🔥 PersistentAnthropicClient Memory Features")
    print("=" * 50)
    
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
    
    # Demonstrate eager memory session initialization
    print("1️⃣ Eager Memory Session Initialization")
    print("-" * 40)
    
    client = PersistentAnthropicClient(
        config=config,
        user_id="financial_analyst"
    )
    
    print(f"✓ Memory session ID available immediately: {client.memory_session_id}")
    print(f"✓ Memory store type: {type(client.memory_store).__name__}")
    print(f"✓ Memory enabled: {client.memory_enabled}")
    
    # Demonstrate explicit initialization method
    print("\n2️⃣ Explicit Memory Session Initialization")
    print("-" * 40)
    
    client2 = PersistentAnthropicClient(
        config=config,
        user_id="portfolio_manager"
    )
    
    # Use the explicit initialization method
    memory_session_id = await client2.initialize_memory_session()
    print(f"✓ Explicit initialization returned: {memory_session_id}")
    print(f"✓ Session fully initialized: {client2._session_initialized}")
    
    # Demonstrate memory operations work immediately
    print("\n3️⃣ Immediate Memory Operations")
    print("-" * 40)
    
    # Add conversation history
    await client.memory_save_message("user", "What's the outlook for tech stocks?")
    await client.memory_save_message("assistant", "Tech stocks show strong fundamentals with AI driving growth...")
    await client.memory_save_message("user", "What about the risks?")
    await client.memory_save_message("assistant", "Key risks include regulatory changes and market volatility...")
    
    # Retrieve and display conversation
    history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Conversation history: {len(history)} messages")
    
    for i, msg in enumerate(history, 1):
        role = msg.role.value.upper()
        content = msg.content[:50] + "..." if len(str(msg.content)) > 50 else msg.content
        print(f"   {i}. [{role}] {content}")
    
    # Search the conversation
    search_results = await client.memory_search_conversations("tech stocks")
    print(f"✓ Search for 'tech stocks': {len(search_results)} results")
    
    # Show session statistics
    stats = await client.memory_get_session_statistics()
    print(f"✓ Session statistics: {stats['message_count']} messages, {stats['session_size_bytes']} bytes")


async def demonstrate_memory_persistence():
    """Show how memory persists across client instances."""
    print("\n4️⃣ Memory Persistence Across Client Instances")
    print("-" * 40)
    
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
    
    # Create first client instance with specific memory session
    print("Creating first client instance...")
    client1 = PersistentAnthropicClient(
        config=config,
        memory_session_id="trading_strategy_session",
        user_id="trader_alice"
    )
    
    # Add some conversation
    await client1.memory_save_message("user", "Analyze NVDA stock performance")
    await client1.memory_save_message("assistant", "NVDA has shown exceptional growth driven by AI demand...")
    
    history1 = await client1.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Client1 conversation: {len(history1)} messages")
    
    # Create second client instance with the SAME memory session ID
    print("\nCreating second client instance with same memory session...")
    client2 = PersistentAnthropicClient(
        config=config,
        memory_session_id="trading_strategy_session",  # Same session!
        user_id="trader_alice"
    )
    
    # Load conversation history
    history2 = await client2.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Client2 loaded conversation: {len(history2)} messages")
    
    # Continue the conversation from second client
    await client2.memory_save_message("user", "What about risk factors?")
    await client2.memory_save_message("assistant", "Key risks include semiconductor supply chain issues...")
    
    # Verify both clients see the updated conversation
    final_history1 = await client1.memory_load_history(convert_to_provider_format=False)
    final_history2 = await client2.memory_load_history(convert_to_provider_format=False)
    
    print(f"✓ Client1 sees {len(final_history1)} total messages")
    print(f"✓ Client2 sees {len(final_history2)} total messages")
    print(f"✓ Memory persistence verified: {len(final_history1) == len(final_history2)}")


async def compare_regular_vs_persistent():
    """Compare regular vs persistent client initialization."""
    print("\n5️⃣ Regular vs Persistent Client Comparison")
    print("-" * 40)
    
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
    
    # Regular client (lazy initialization)
    print("Regular AnthropicClient:")
    regular = AnthropicClient(config=config, user_id="regular_user")
    print(f"  Memory session ID (before use): {regular.memory_session_id}")
    
    # Force initialization by using memory
    await regular.memory_save_message("user", "Hello")
    print(f"  Memory session ID (after use): {regular.memory_session_id}")
    
    # Persistent client (eager initialization)
    print("\nPersistentAnthropicClient:")
    persistent = PersistentAnthropicClient(config=config, user_id="persistent_user")
    print(f"  Memory session ID (immediate): {persistent.memory_session_id}")
    
    print(f"\n✓ Regular: Lazy initialization (good for short operations)")
    print(f"✓ Persistent: Eager initialization (good for long sessions)")


async def main():
    """Run PersistentAnthropicClient memory demonstrations."""
    print("🔥 PersistentAnthropicClient Enhanced Memory System")
    print("=" * 60)
    print("Demonstrating immediate memory session availability and persistence\n")
    
    try:
        await demonstrate_persistent_memory()
        await demonstrate_memory_persistence()
        await compare_regular_vs_persistent()
        
        print("\n" + "=" * 60)
        print("✅ PERSISTENT MEMORY DEMONSTRATIONS COMPLETE!")
        print("=" * 60)
        print("\n🎯 Key Benefits:")
        print("  🚀 Immediate memory session ID availability")
        print("  💾 Automatic InMemoryStore setup")
        print("  🔄 Memory persistence across client instances")
        print("  ⚡ Optimized for long-running conversations")
        print("  📊 Rich session statistics and search")
        
        print(f"\n🎪 Perfect for:")
        print(f"  • Financial analysis sessions")
        print(f"  • Long-running trading conversations")
        print(f"  • Persistent research workflows")
        print(f"  • Multi-step investment planning")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("PersistentAnthropicClient demo error")


if __name__ == "__main__":
    asyncio.run(main())
