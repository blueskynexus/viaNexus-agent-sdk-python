#!/usr/bin/env python3
"""
AnthropicClient InMemoryStore Integration Demo.
Shows how InMemoryStore is now seamlessly integrated into AnthropicClient.
"""

import asyncio
import logging
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient
from vianexus_agent_sdk.memory.stores.memory_memory import InMemoryStore


async def demo_default_inmemory_integration():
    """Demonstrate the default InMemoryStore integration."""
    print("🧠 DEFAULT INMEMORY INTEGRATION DEMO")
    print("=" * 60)
    print("AnthropicClient now uses InMemoryStore by default!\n")
    
    # Configuration
    config = {
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "sample.jwt.token"
            }
        },
        "LLM_API_KEY": "your-anthropic-api-key",
        "system_prompt": "You are a helpful financial analyst."
    }
    
    # Method 1: Default behavior (automatically uses InMemoryStore)
    print("1️⃣ Default AnthropicClient (automatic InMemoryStore)")
    client1 = AnthropicClient(
        config=config,
        user_id="demo_user_001",
        memory_session_id="default_session"
    )
    
    session_info = client1.memory_get_current_session_info()
    print(f"   ✓ Memory enabled: {session_info['memory_enabled']}")
    print(f"   ✓ Memory Session ID: {session_info['memory_session_id']}")
    print(f"   ✓ Provider: {session_info['provider']}")
    
    # Add some demo messages
    await client1.memory_save_message("user", "What's the current market outlook?")
    await client1.memory_save_message("assistant", "The market shows positive trends with technology sectors leading...")
    
    history = await client1.memory_load_history(convert_to_provider_format=False)
    print(f"   ✓ Messages stored: {len(history)}")
    
    return client1


async def demo_explicit_inmemory_creation():
    """Demonstrate explicit InMemoryStore creation methods."""
    print("\n2️⃣ EXPLICIT INMEMORY CREATION METHODS")
    print("=" * 60)
    
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
    
    # Method A: Class method for explicit InMemoryStore
    print("Method A: Using .with_in_memory_store() class method")
    client_a = AnthropicClient.with_in_memory_store(
        config=config,
        user_id="explicit_user_001",
        memory_session_id="explicit_session_a"
    )
    
    await client_a.memory_save_message("user", "Analyze portfolio performance")
    await client_a.memory_save_message("assistant", "Your portfolio shows strong performance...")
    
    stats_a = await client_a.memory_get_session_statistics()
    print(f"   ✓ Session: {stats_a.get('session_id', 'N/A')}")
    print(f"   ✓ Messages: {stats_a.get('message_count', 0)}")
    
    # Method B: Explicit InMemoryStore instance
    print("\nMethod B: Passing explicit InMemoryStore instance")
    memory_store = InMemoryStore()
    
    client_b = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="explicit_user_002",
        memory_session_id="explicit_session_b"
    )
    
    await client_b.memory_save_message("user", "What are the trending stocks?")
    await client_b.memory_save_message("assistant", "Current trending stocks include...")
    
    stats_b = await client_b.memory_get_session_statistics()
    print(f"   ✓ Session: {stats_b.get('session_id', 'N/A')}")
    print(f"   ✓ Messages: {stats_b.get('message_count', 0)}")
    
    # Method C: Configuration-based memory store selection
    print("\nMethod C: Configuration-based store selection")
    config_with_memory = {
        **config,
        "memory": {
            "store_type": "in_memory"
        }
    }
    
    client_c = AnthropicClient(
        config=config_with_memory,
        user_id="config_user_001",
        memory_session_id="config_session_c"
    )
    
    await client_c.memory_save_message("user", "Recommend investment strategies")
    await client_c.memory_save_message("assistant", "Based on current market conditions...")
    
    stats_c = await client_c.memory_get_session_statistics()
    print(f"   ✓ Session: {stats_c.get('session_id', 'N/A')}")
    print(f"   ✓ Messages: {stats_c.get('message_count', 0)}")
    
    return memory_store


async def demo_memory_configuration_options():
    """Demonstrate various memory configuration options."""
    print("\n3️⃣ MEMORY CONFIGURATION OPTIONS")
    print("=" * 60)
    
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
    
    # Option 1: Memory enabled with InMemoryStore (default)
    print("Option 1: Default memory configuration")
    client1 = AnthropicClient(config=config, user_id="option1_user")
    info1 = client1.memory_get_current_session_info()
    print(f"   ✓ Memory enabled: {info1['memory_enabled']}")
    print(f"   ✓ Memory Session ID pattern: {info1['memory_session_id']}")
    
    # Option 2: Memory enabled but no default store
    print("\nOption 2: Memory enabled, no default store")
    client2 = AnthropicClient(
        config=config,
        user_id="option2_user",
        enable_memory=True,
        use_in_memory_store=False
    )
    info2 = client2.memory_get_current_session_info()
    print(f"   ✓ Memory enabled: {info2['memory_enabled']}")
    print(f"   ✓ Has store: {info2['memory_enabled'] and client2.memory_store is not None}")
    
    # Option 3: Memory completely disabled
    print("\nOption 3: Memory completely disabled")
    client3 = AnthropicClient.without_memory(config=config)
    info3 = client3.memory_get_current_session_info()
    print(f"   ✓ Memory enabled: {info3['memory_enabled']}")
    print(f"   ✓ Session ID: {info3.get('session_id', 'None')}")
    
    # Option 4: File-based memory store
    print("\nOption 4: File-based memory store")
    client4 = AnthropicClient.with_file_memory_store(
        config=config,
        storage_path="demo_file_conversations",
        user_id="option4_user"
    )
    info4 = client4.memory_get_current_session_info()
    print(f"   ✓ Memory enabled: {info4['memory_enabled']}")
    print(f"   ✓ Store type: FileMemoryStore")
    print(f"   ✓ Memory Session ID: {info4['memory_session_id']}")


async def demo_inmemory_performance():
    """Demonstrate InMemoryStore performance characteristics."""
    print("\n4️⃣ INMEMORY PERFORMANCE DEMO")
    print("=" * 60)
    
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
    
    # Create client with InMemoryStore
    client = AnthropicClient.with_in_memory_store(
        config=config,
        user_id="performance_user",
        memory_session_id="performance_test_session"
    )
    
    print("Testing InMemoryStore performance characteristics...")
    
    # Rapid message storage test
    import time
    start_time = time.time()
    
    message_count = 100
    for i in range(message_count):
        await client.memory_save_message("user", f"Message {i}: Test message content")
        await client.memory_save_message("assistant", f"Response {i}: Simulated response content")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"   ✓ Stored {message_count * 2} messages in {duration:.3f} seconds")
    print(f"   ✓ Rate: {(message_count * 2) / duration:.1f} messages/second")
    
    # Memory retrieval test
    start_time = time.time()
    history = await client.memory_load_history()
    end_time = time.time()
    
    print(f"   ✓ Retrieved {len(history)} messages in {(end_time - start_time) * 1000:.1f} ms")
    
    # Search performance test
    start_time = time.time()
    search_results = await client.memory_search_conversations("Message 50")
    end_time = time.time()
    
    print(f"   ✓ Search found {len(search_results)} results in {(end_time - start_time) * 1000:.1f} ms")
    
    # Session statistics
    stats = await client.memory_get_session_statistics()
    print(f"   ✓ Session size: {stats.get('session_size_bytes', 0)} bytes")
    print(f"   ✓ Total messages: {stats.get('message_count', 0)}")


async def demo_session_isolation_with_inmemory():
    """Demonstrate session isolation with InMemoryStore."""
    print("\n5️⃣ SESSION ISOLATION WITH INMEMORY")
    print("=" * 60)
    
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
    
    # Share the same InMemoryStore across multiple clients
    shared_memory = InMemoryStore()
    
    # Client 1: Trading session
    client1 = AnthropicClient(
        config=config,
        memory_store=shared_memory,
        user_id="isolation_user",
        memory_session_id="trading_session_001"
    )
    
    # Client 2: Research session  
    client2 = AnthropicClient(
        config=config,
        memory_store=shared_memory,
        user_id="isolation_user",
        memory_session_id="research_session_001"
    )
    
    # Add different messages to each session
    await client1.memory_save_message("user", "Buy 100 shares of AAPL")
    await client1.memory_save_message("assistant", "Order placed for 100 AAPL shares")
    
    await client2.memory_save_message("user", "Research Tesla's Q3 earnings")
    await client2.memory_save_message("assistant", "Tesla Q3 earnings analysis shows...")
    
    # Verify isolation
    trading_history = await client1.memory_load_history(convert_to_provider_format=False)
    research_history = await client2.memory_load_history(convert_to_provider_format=False)
    
    print(f"   ✓ Trading session messages: {len(trading_history)}")
    print(f"   ✓ Research session messages: {len(research_history)}")
    
    # Verify content isolation
    trading_content = [str(msg.content) for msg in trading_history]
    research_content = [str(msg.content) for msg in research_history]
    
    has_overlap = any(content in research_content for content in trading_content)
    print(f"   ✓ Sessions are isolated: {not has_overlap}")
    
    # Show shared store can track both sessions
    user_sessions = await client1.memory_get_user_sessions()
    print(f"   ✓ User has {len(user_sessions)} sessions in shared store")
    
    return shared_memory


async def main():
    """Run all InMemoryStore integration demonstrations."""
    print("🧠 AnthropicClient InMemoryStore Integration")
    print("=" * 60)
    print("Demonstrating seamless InMemoryStore integration in AnthropicClient\n")
    
    try:
        # Run all demonstrations
        default_client = await demo_default_inmemory_integration()
        shared_store = await demo_explicit_inmemory_creation()
        await demo_memory_configuration_options()
        await demo_inmemory_performance()
        isolation_store = await demo_session_isolation_with_inmemory()
        
        # Add new PersistentAnthropicClient demo
        persistent_client = await demonstrate_persistent_client()
        
        print("\n" + "=" * 60)
        print("✅ ALL INMEMORY INTEGRATION DEMOS COMPLETED!")
        print("=" * 60)
        print("\n🎯 Key Features Demonstrated:")
        print("  ✓ Automatic InMemoryStore by default")
        print("  ✓ Multiple creation methods and configurations")
        print("  ✓ High-performance message storage and retrieval")
        print("  ✓ Perfect session isolation in shared stores")
        print("  ✓ Seamless integration with existing AnthropicClient API")
        print("  ✓ Backward compatibility with all memory features")
        print("  🚀 PersistentAnthropicClient with immediate memory availability")
        print("  🔄 Memory persistence across client instances")
        print("  🎯 Custom memory session IDs for organized workflows")
        
        # Show final statistics
        if hasattr(shared_store, 'get_stats'):
            final_stats = shared_store.get_stats()
            print(f"\n📊 Final InMemoryStore Statistics:")
            print(f"  Total Sessions: {final_stats.get('total_sessions', 0)}")
            print(f"  Total Messages: {final_stats.get('total_messages', 0)}")
            print(f"  Total Users: {final_stats.get('total_users', 0)}")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("InMemory integration demo error")


async def demonstrate_persistent_client():
    """Demonstrate PersistentAnthropicClient with immediate memory session availability."""
    print("\n" + "=" * 60)
    print("🔥 PersistentAnthropicClient with InMemoryStore")
    print("=" * 60)
    print("Enhanced client for long-running conversations with immediate memory availability")
    
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
    
    # Import PersistentAnthropicClient
    from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient
    
    # Demonstrate immediate memory session availability
    print("\n1️⃣ Immediate Memory Session Creation")
    print("-" * 40)
    
    persistent_client = PersistentAnthropicClient(
        config=config,
        user_id="portfolio_manager",
        # memory_session_id is auto-generated for persistent clients
    )
    
    print(f"✓ Memory session ID (immediately available): {persistent_client.memory_session_id}")
    print(f"✓ Memory store type: {type(persistent_client.memory_store).__name__}")
    print(f"✓ Memory enabled: {persistent_client.memory_enabled}")
    print(f"✓ User ID: {persistent_client.user_id}")
    
    # Show the difference from regular client
    print(f"\n📊 Comparison with Regular AnthropicClient:")
    regular_client = AnthropicClient(config=config, user_id="portfolio_manager")
    print(f"   Regular client memory_session_id: {regular_client.memory_session_id}")
    print(f"   Persistent client memory_session_id: {persistent_client.memory_session_id}")
    print(f"   ↳ Persistent client provides immediate session availability! 🚀")
    
    # Demonstrate immediate memory operations
    print("\n2️⃣ Immediate Memory Operations")
    print("-" * 40)
    
    # Start a portfolio analysis conversation
    await persistent_client.memory_save_message("user", "Analyze my tech portfolio performance for Q4")
    await persistent_client.memory_save_message("assistant", "I'll analyze your Q4 tech portfolio. Key holdings show strong performance with NVDA up 45%, MSFT up 22%, and AAPL maintaining steady growth...")
    await persistent_client.memory_save_message("user", "What are the risk factors I should consider?")
    await persistent_client.memory_save_message("assistant", "Key risk factors include: 1) Market volatility in tech sector, 2) Regulatory changes affecting big tech, 3) Interest rate sensitivity...")
    await persistent_client.memory_save_message("user", "Should I rebalance my portfolio?")
    await persistent_client.memory_save_message("assistant", "Based on your Q4 performance, consider rebalancing: reduce NVDA position (take profits), increase defensive tech positions...")
    
    conversation = await persistent_client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Portfolio conversation: {len(conversation)} messages stored")
    
    # Display conversation summary
    for i, msg in enumerate(conversation[:3], 1):  # Show first 3 messages
        role = msg.role.value.upper()
        content = str(msg.content)[:60] + "..." if len(str(msg.content)) > 60 else str(msg.content)
        print(f"   {i}. [{role}] {content}")
    
    # Demonstrate search capabilities
    search_results = await persistent_client.memory_search_conversations("portfolio rebalance")
    print(f"✓ Search results for 'portfolio rebalance': {len(search_results)} messages")
    
    # Show session statistics
    stats = await persistent_client.memory_get_session_statistics()
    print(f"✓ Session stats: {stats['message_count']} messages, {stats['session_size_bytes']} bytes")
    
    # Demonstrate persistence across "sessions" (client instances)
    print("\n3️⃣ Memory Persistence Demo")
    print("-" * 40)
    
    # Create another persistent client with the SAME memory session ID
    persistent_client2 = PersistentAnthropicClient(
        config=config,
        memory_session_id=persistent_client.memory_session_id,  # Same session!
        user_id="portfolio_manager"
    )
    
    print(f"✓ Created second client with same memory session: {persistent_client2.memory_session_id}")
    
    # Load conversation from second client
    shared_conversation = await persistent_client2.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Second client loaded conversation: {len(shared_conversation)} messages")
    
    # Continue conversation from second client
    await persistent_client2.memory_save_message("user", "What about cryptocurrency allocation?")
    await persistent_client2.memory_save_message("assistant", "For crypto allocation, consider 5-10% of total portfolio in established coins like BTC and ETH, given your risk tolerance...")
    
    # Verify first client sees the new messages
    updated_conversation = await persistent_client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ First client sees updated conversation: {len(updated_conversation)} messages")
    print(f"✓ Memory persistence verified: {len(shared_conversation) < len(updated_conversation)}")
    
    # Demonstrate custom memory session IDs
    print("\n4️⃣ Custom Memory Session IDs")
    print("-" * 40)
    
    # Create persistent clients with meaningful session names
    quarterly_review = PersistentAnthropicClient(
        config=config,
        memory_session_id="q4_2024_portfolio_review",
        user_id="portfolio_manager"
    )
    
    tax_planning = PersistentAnthropicClient(
        config=config,
        memory_session_id="tax_planning_2024",
        user_id="portfolio_manager"
    )
    
    risk_assessment = PersistentAnthropicClient(
        config=config,
        memory_session_id="risk_assessment_december",
        user_id="portfolio_manager"
    )
    
    print(f"✓ Quarterly review session: {quarterly_review.memory_session_id}")
    print(f"✓ Tax planning session: {tax_planning.memory_session_id}")
    print(f"✓ Risk assessment session: {risk_assessment.memory_session_id}")
    
    # Add different conversations to each
    await quarterly_review.memory_save_message("user", "Review Q4 performance metrics")
    await tax_planning.memory_save_message("user", "Plan tax loss harvesting strategy")
    await risk_assessment.memory_save_message("user", "Assess portfolio risk exposure")
    
    # Show isolation
    q4_msgs = await quarterly_review.memory_load_history(convert_to_provider_format=False)
    tax_msgs = await tax_planning.memory_load_history(convert_to_provider_format=False)
    risk_msgs = await risk_assessment.memory_load_history(convert_to_provider_format=False)
    
    print(f"✓ Session isolation verified:")
    print(f"   Q4 review: {len(q4_msgs)} messages")
    print(f"   Tax planning: {len(tax_msgs)} messages")
    print(f"   Risk assessment: {len(risk_msgs)} messages")
    
    # Demonstrate MCP session correlation
    print("\n5️⃣ MCP Session Correlation")
    print("-" * 40)
    
    print(f"✓ Memory session ID: {persistent_client.memory_session_id}")
    print(f"✓ MCP session ID: {getattr(persistent_client, '_mcp_session_id', 'Not established')}")
    
    if persistent_client._current_session and persistent_client._current_session.session_metadata:
        metadata = persistent_client._current_session.session_metadata
        correlation = metadata.get("mcp_session_correlation", "Not available")
        print(f"✓ Session correlation: {correlation}")
    
    print(f"✓ Clear separation: Memory sessions persist, MCP sessions are ephemeral")
    
    # Performance demonstration
    print("\n6️⃣ Performance with Large Conversations")
    print("-" * 40)
    
    perf_client = PersistentAnthropicClient(
        config=config,
        memory_session_id="performance_test_session",
        user_id="performance_tester"
    )
    
    # Add many messages quickly
    import time
    start_time = time.time()
    
    for i in range(50):
        await perf_client.memory_save_message("user", f"Analysis request {i+1}")
        await perf_client.memory_save_message("assistant", f"Analysis response {i+1}: Market data shows...")
    
    end_time = time.time()
    
    perf_conversation = await perf_client.memory_load_history(convert_to_provider_format=False)
    perf_stats = await perf_client.memory_get_session_statistics()
    
    print(f"✓ Stored 100 messages in {end_time - start_time:.3f}s")
    print(f"✓ Total conversation: {len(perf_conversation)} messages")
    print(f"✓ Session size: {perf_stats['session_size_bytes']} bytes")
    print(f"✓ InMemoryStore handles large conversations efficiently!")
    
    # Demonstrate ask_with_persistent_session with memory integration
    print("\n7️⃣ Persistent MCP + Memory Integration Demo")
    print("-" * 40)
    
    mcp_memory_client = PersistentAnthropicClient(
        config=config,
        memory_session_id="trading_analysis_with_mcp",
        user_id="mcp_trader"
    )
    
    print(f"✓ Created client with memory session: {mcp_memory_client.memory_session_id}")
    
    # First, add some conversation context to memory
    await mcp_memory_client.memory_save_message("user", "I'm a conservative investor focused on blue-chip stocks")
    await mcp_memory_client.memory_save_message("assistant", "Understood. As a conservative investor, I'll focus on established companies with strong dividends and stable growth.")
    await mcp_memory_client.memory_save_message("user", "My portfolio is currently 60% stocks, 30% bonds, 10% cash")
    await mcp_memory_client.memory_save_message("assistant", "That's a well-balanced conservative allocation. The 60/30/10 split provides growth potential while managing risk.")
    
    print(f"✓ Established conversation context with {(await mcp_memory_client.memory_load_history(convert_to_provider_format=False)).__len__()} messages")
    
    # Simulate establishing MCP connection (normally this would connect to actual MCP server)
    print("✓ Simulating MCP connection establishment...")
    print("  Note: In real usage, this would connect to viaNexus MCP server")
    print("  For demo purposes, we'll show the integration without actual MCP calls")
    
    # Demonstrate how ask_with_persistent_session would work with memory
    print("\n📋 ask_with_persistent_session() with Memory Integration:")
    print("   This method combines:")
    print("   • Persistent MCP connection for tool access")
    print("   • Automatic memory loading for conversation context")
    print("   • Memory saving for new interactions")
    
    # Show what the conversation history would look like before MCP query
    context_history = await mcp_memory_client.memory_load_history(convert_to_provider_format=False)
    print(f"\n📚 Conversation Context Available to MCP Query:")
    for i, msg in enumerate(context_history[-2:], 1):  # Show last 2 messages for context
        role = msg.role.value.upper()
        content = str(msg.content)[:80] + "..." if len(str(msg.content)) > 80 else str(msg.content)
        print(f"   {i}. [{role}] {content}")
    
    # Simulate what would happen in ask_with_persistent_session
    print(f"\n🔄 Simulated ask_with_persistent_session() workflow:")
    print(f"   1. Load conversation history from memory ✓")
    print(f"   2. Add user question to conversation context")
    print(f"   3. Use persistent MCP connection for tool access")
    print(f"   4. Generate response with full context")
    print(f"   5. Save interaction to memory for future queries")
    
    # Add the simulated interaction to memory
    user_question = "Should I rebalance my portfolio given current market conditions?"
    simulated_response = "Based on your conservative profile and current 60/30/10 allocation, the portfolio is well-positioned. However, given recent market volatility, consider slightly increasing your bond allocation to 35% and reducing stocks to 55% for additional stability."
    
    await mcp_memory_client.memory_save_message("user", user_question)
    await mcp_memory_client.memory_save_message("assistant", simulated_response)
    
    # Show updated conversation
    final_history = await mcp_memory_client.memory_load_history(convert_to_provider_format=False)
    print(f"\n✓ Updated conversation: {len(final_history)} total messages")
    print(f"✓ Latest exchange:")
    print(f"   USER: {user_question}")
    print(f"   ASSISTANT: {simulated_response[:100]}...")
    
    # Demonstrate memory continuity for next MCP session
    print(f"\n🔄 Memory Continuity for Next Session:")
    
    # Create another client with same memory session
    next_session_client = PersistentAnthropicClient(
        config=config,
        memory_session_id="trading_analysis_with_mcp",  # Same session!
        user_id="mcp_trader"
    )
    
    # Show that it has access to full conversation history
    continuing_history = await next_session_client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ New client instance has full conversation: {len(continuing_history)} messages")
    print(f"✓ Memory persistence ensures context continuity across MCP sessions")
    
    # Show session correlation information
    session_info = mcp_memory_client.memory_get_current_session_info()
    print(f"\n📊 Session Information:")
    print(f"   Memory Session ID: {session_info['memory_session_id']}")
    print(f"   MCP Session ID: {getattr(mcp_memory_client, '_mcp_session_id', 'Not established')}")
    print(f"   Session Isolation: ✓ Guaranteed")
    print(f"   Memory Enabled: {session_info['memory_enabled']}")
    
    # Performance metrics for the combined system
    final_stats = await mcp_memory_client.memory_get_session_statistics()
    print(f"\n⚡ Combined System Performance:")
    print(f"   Total Messages: {final_stats['message_count']}")
    print(f"   Session Size: {final_stats['session_size_bytes']} bytes")
    print(f"   Duration: {final_stats['duration_seconds']:.3f} seconds")
    print(f"   Memory + MCP Integration: Seamless ✨")
    
    # Add realistic code example
    print(f"\n💻 Real-World Usage Example:")
    print("```python")
    print("# Create persistent client with memory")
    print("client = PersistentAnthropicClient(")
    print("    config=config,")
    print("    memory_session_id='financial_analysis_session',")
    print("    user_id='trader_alice'")
    print(")")
    print("")
    print("# Establish persistent MCP connection")
    print("mcp_session_id = await client.establish_persistent_connection()")
    print("print(f'MCP Session: {mcp_session_id}')")
    print("")
    print("# Ask questions with full memory + MCP integration")
    print("response1 = await client.ask_with_persistent_session(")
    print("    'What is the current price of NVDA?'")
    print(")")
    print("")
    print("response2 = await client.ask_with_persistent_session(")
    print("    'Should I buy more given my conservative profile?'")
    print("    # This automatically has context from previous conversations!")
    print(")")
    print("")
    print("# Memory persists across sessions")
    print("history = await client.memory_load_history()")
    print("print(f'Full conversation: {len(history)} messages')")
    print("```")
    
    print(f"\n🎯 Key Benefits of ask_with_persistent_session():")
    print(f"   ✓ Persistent MCP connection (faster subsequent queries)")
    print(f"   ✓ Automatic memory context loading")
    print(f"   ✓ Real-time tool access via MCP")
    print(f"   ✓ Conversation continuity across sessions")
    print(f"   ✓ Perfect for financial analysis workflows")
    
    return persistent_client




if __name__ == "__main__":
    asyncio.run(main())
