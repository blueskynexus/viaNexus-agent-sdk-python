#!/usr/bin/env python3
"""
Simple InMemoryStore usage example.
Shows the easiest way to use AnthropicClient with automatic memory.
"""

import asyncio
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient


async def simple_conversation_with_memory():
    """Demonstrate the simplest possible conversation with automatic memory."""
    print("💬 Simple Conversation with Automatic Memory")
    print("=" * 50)
    
    # Basic configuration
    config = {
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "sample.jwt.token"
            }
        },
        "LLM_API_KEY": "your-anthropic-api-key",
        "system_prompt": "You are a helpful financial assistant."
    }
    
    # Create client - InMemoryStore is automatic!
    print("Creating AnthropicClient (InMemoryStore automatic)...")
    client = AnthropicClient(
        config=config,
        user_id="simple_user",
        memory_session_id="simple_conversation"
    )
    
    print(f"✓ Client created with memory: {client.memory_enabled}")
    print(f"✓ Memory Session ID: {client.memory_session_id}")
    
    # Simulate a conversation (normally you'd call actual LLM)
    print("\n📝 Simulating conversation messages...")
    
    # Add messages to memory
    await client.memory_save_message("user", "What's the best investment strategy for 2024?")
    await client.memory_save_message("assistant", "For 2024, consider a diversified portfolio with focus on technology and sustainable energy sectors...")
    
    await client.memory_save_message("user", "What about risk management?")
    await client.memory_save_message("assistant", "Risk management is crucial. I recommend allocating no more than 20% to high-risk investments...")
    
    await client.memory_save_message("user", "Can you summarize our discussion?")
    await client.memory_save_message("assistant", "We discussed investment strategies for 2024 and risk management principles...")
    
    # Retrieve conversation history
    print("📚 Retrieving conversation history...")
    history = await client.memory_load_history(convert_to_provider_format=False)
    
    print(f"✓ Conversation has {len(history)} messages:")
    for i, msg in enumerate(history, 1):
        role = msg.role.value.upper()
        content = str(msg.content)[:60] + "..." if len(str(msg.content)) > 60 else str(msg.content)
        print(f"   {i}. [{role}] {content}")
    
    # Search conversation
    print("\n🔍 Searching conversation...")
    search_results = await client.memory_search_conversations("investment strategy")
    print(f"✓ Found {len(search_results)} messages about 'investment strategy'")
    
    # Session statistics
    print("\n📊 Session Statistics:")
    stats = await client.memory_get_session_statistics()
    print(f"   Messages: {stats.get('message_count', 0)}")
    print(f"   Duration: {stats.get('duration_seconds', 0):.1f} seconds")
    print(f"   Size: {stats.get('session_size_bytes', 0)} bytes")
    
    return client


async def demonstrate_multiple_sessions():
    """Show how easy it is to work with multiple sessions."""
    print("\n" + "=" * 50)
    print("🔄 Multiple Sessions Demo")
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
    
    # Create client and multiple sessions
    client = AnthropicClient(config=config, user_id="multi_user")
    
    # Session 1: Investment advice
    investment_session = await client.memory_create_isolated_session(
        session_context="investment_advice",
        context_tags=["investment", "advice"]
    )
    await client.memory_switch_session(investment_session)
    await client.memory_save_message("user", "How should I invest $10,000?")
    await client.memory_save_message("assistant", "With $10,000, consider a mix of index funds and individual stocks...")
    
    # Session 2: Tax planning
    tax_session = await client.memory_create_isolated_session(
        session_context="tax_planning",
        context_tags=["tax", "planning"]
    )
    await client.memory_switch_session(tax_session)
    await client.memory_save_message("user", "What are the best tax-saving strategies?")
    await client.memory_save_message("assistant", "Key tax-saving strategies include maximizing retirement contributions...")
    
    # Session 3: Budget planning
    budget_session = await client.memory_create_isolated_session(
        session_context="budget_planning",
        context_tags=["budget", "planning"]
    )
    await client.memory_switch_session(budget_session)
    await client.memory_save_message("user", "Help me create a monthly budget")
    await client.memory_save_message("assistant", "Let's start by categorizing your income and expenses...")
    
    # Show session isolation
    print("✓ Created 3 isolated sessions:")
    print(f"   1. Investment advice: {investment_session}")
    print(f"   2. Tax planning: {tax_session}")
    print(f"   3. Budget planning: {budget_session}")
    
    # Verify each session has its own messages
    for i, session_id in enumerate([investment_session, tax_session, budget_session], 1):
        await client.memory_switch_session(session_id)
        history = await client.memory_load_history()
        stats = await client.memory_get_session_statistics()
        print(f"   Session {i}: {stats.get('message_count', 0)} messages")
    
    # List all user sessions
    user_sessions = await client.memory_list_user_sessions_with_stats()
    print(f"\n✓ User has {len(user_sessions)} total sessions")


async def demonstrate_performance():
    """Show InMemoryStore performance."""
    print("\n" + "=" * 50)
    print("⚡ Performance Demo")
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
    
    # Create high-performance client
    client = AnthropicClient.with_in_memory_store(
        config=config,
        user_id="perf_user",
        memory_session_id="performance_test"
    )
    
    # Performance test
    import time
    
    print("Testing message storage performance...")
    start = time.time()
    
    for i in range(50):
        await client.memory_save_message("user", f"Performance test message {i}")
        await client.memory_save_message("assistant", f"Response to message {i}")
    
    storage_time = time.time() - start
    
    start = time.time()
    history = await client.memory_load_history()
    retrieval_time = time.time() - start
    
    start = time.time()
    search_results = await client.memory_search_conversations("Performance test")
    search_time = time.time() - start
    
    print(f"✓ Stored 100 messages in {storage_time:.3f}s ({100/storage_time:.0f} msg/s)")
    print(f"✓ Retrieved {len(history)} messages in {retrieval_time*1000:.1f}ms")
    print(f"✓ Search found {len(search_results)} results in {search_time*1000:.1f}ms")
    print("✓ InMemoryStore is extremely fast for development and testing!")


async def main():
    """Run simple usage demonstrations."""
    print("🚀 AnthropicClient with InMemoryStore - Simple Usage")
    print("=" * 60)
    print("The easiest way to get conversation memory in your application!")
    print()
    
    try:
        # Run demonstrations
        simple_client = await simple_conversation_with_memory()
        await demonstrate_multiple_sessions()
        await demonstrate_performance()
        
        print("\n" + "=" * 60)
        print("✅ SIMPLE USAGE DEMOS COMPLETED!")
        print("=" * 60)
        print("\n💡 Key Takeaways:")
        print("  🧠 InMemoryStore is now the default - just create AnthropicClient!")
        print("  ⚡ Ultra-fast performance for development and testing")
        print("  🔒 Perfect session isolation out of the box")
        print("  📊 Rich statistics and search capabilities")
        print("  🎯 Zero configuration needed - it just works!")
        
        print(f"\n🎉 Your conversations are automatically remembered!")
        print(f"📝 Session: {simple_client.memory_session_id}")
        print(f"👤 User: {simple_client.user_id}")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
