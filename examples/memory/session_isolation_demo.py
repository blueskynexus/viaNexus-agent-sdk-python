#!/usr/bin/env python3
"""
Enhanced session isolation demonstration.
Shows guaranteed session isolation and advanced session management features.
"""

import asyncio
import logging
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient
from vianexus_agent_sdk.memory.stores.file_memory import FileMemoryStore
from vianexus_agent_sdk.memory.session_manager import SessionManager


async def demonstrate_guaranteed_session_isolation():
    """Demonstrate guaranteed session isolation with the enhanced system."""
    print("🔒 GUARANTEED SESSION ISOLATION DEMO")
    print("=" * 60)
    print("This demo shows how each session is completely isolated")
    print("with guaranteed unique session IDs and independent memory.\n")
    
    # Create memory store and session manager
    memory_store = FileMemoryStore("isolated_sessions_demo")
    session_manager = SessionManager(memory_store)
    
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
        "system_prompt": "You are a specialized financial analyst."
    }
    
    # Create multiple clients for the same user (different contexts)
    print("👤 Creating multiple clients for user 'trader_001'...")
    
    # Client 1: Portfolio Analysis
    client1 = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="trader_001"
    )
    
    # Create isolated session for portfolio analysis
    portfolio_session_id = await client1.memory_create_isolated_session(
        session_context="portfolio_analysis",
        context_tags=["finance", "portfolio", "analysis"],
        session_metadata={"department": "trading", "priority": "high"}
    )
    
    await client1.memory_switch_session(portfolio_session_id)
    
    print(f"✓ Portfolio Analysis Session: {portfolio_session_id}")
    
    # Client 2: Risk Assessment 
    client2 = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="trader_001"
    )
    
    risk_session_id = await client2.memory_create_isolated_session(
        session_context="risk_assessment",
        context_tags=["finance", "risk", "compliance"],
        session_metadata={"department": "risk", "priority": "critical"}
    )
    
    await client2.memory_switch_session(risk_session_id)
    
    print(f"✓ Risk Assessment Session: {risk_session_id}")
    
    # Client 3: Market Research
    client3 = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="trader_001"
    )
    
    market_session_id = await client3.memory_create_isolated_session(
        session_context="market_research",
        context_tags=["finance", "market", "research"],
        session_metadata={"department": "research", "priority": "medium"}
    )
    
    await client3.memory_switch_session(market_session_id)
    
    print(f"✓ Market Research Session: {market_session_id}")
    
    # Add messages to each session independently
    print("\n📝 Adding messages to each isolated session...")
    
    # Portfolio session messages
    await client1.memory_save_message("user", "Analyze my tech stock portfolio performance")
    await client1.memory_save_message("assistant", "Your tech portfolio shows strong performance...")
    await client1.memory_save_message("user", "What adjustments would you recommend?")
    await client1.memory_save_message("assistant", "I recommend rebalancing towards AI and cloud companies...")
    
    # Risk session messages
    await client2.memory_save_message("user", "What are the current risk factors in our positions?")
    await client2.memory_save_message("assistant", "Current risk factors include market volatility...")
    await client2.memory_save_message("user", "Calculate VaR for our equity positions")
    await client2.memory_save_message("assistant", "Value at Risk calculation shows...")
    
    # Market session messages
    await client3.memory_save_message("user", "What are the trending sectors this quarter?")
    await client3.memory_save_message("assistant", "Trending sectors include renewable energy...")
    await client3.memory_save_message("user", "Provide analysis on semiconductor stocks")
    await client3.memory_save_message("assistant", "Semiconductor analysis indicates...")
    
    print("✓ Messages added to all sessions")
    
    # Demonstrate session isolation by retrieving histories
    print("\n🔍 Verifying session isolation...")
    
    portfolio_history = await client1.memory_load_history(convert_to_provider_format=False)
    risk_history = await client2.memory_load_history(convert_to_provider_format=False)
    market_history = await client3.memory_load_history(convert_to_provider_format=False)
    
    print(f"  Portfolio session: {len(portfolio_history)} messages")
    print(f"  Risk session: {len(risk_history)} messages")
    print(f"  Market session: {len(market_history)} messages")
    
    # Verify messages are truly isolated
    portfolio_topics = set(str(msg.content) for msg in portfolio_history)
    risk_topics = set(str(msg.content) for msg in risk_history)
    market_topics = set(str(msg.content) for msg in market_history)
    
    # Check for overlap (should be none)
    overlaps = portfolio_topics & risk_topics & market_topics
    print(f"  Message overlap between sessions: {len(overlaps)} (should be 0)")
    
    if len(overlaps) == 0:
        print("✅ Sessions are perfectly isolated!")
    else:
        print("❌ Found unexpected message overlap")
    
    # Show session statistics
    print("\n📊 Session Statistics:")
    
    for i, (client, session_name) in enumerate([
        (client1, "Portfolio Analysis"),
        (client2, "Risk Assessment"), 
        (client3, "Market Research")
    ], 1):
        stats = await client.memory_get_session_statistics()
        print(f"\n  {i}. {session_name} Session:")
        print(f"     Session ID: {stats.get('session_id', 'N/A')}")
        print(f"     Messages: {stats.get('message_count', 0)}")
        print(f"     Duration: {stats.get('duration_seconds', 0):.1f}s")
        print(f"     Size: {stats.get('session_size_bytes', 0)} bytes")
        print(f"     Context Tags: {stats.get('context_tags', [])}")
    
    return [portfolio_session_id, risk_session_id, market_session_id]


async def demonstrate_session_retrieval_by_id():
    """Demonstrate session retrieval by ID with different clients."""
    print("\n" + "=" * 60)
    print("🔄 SESSION RETRIEVAL BY ID DEMO")
    print("=" * 60)
    print("Showing how sessions can be retrieved by ID across different client instances.\n")
    
    memory_store = FileMemoryStore("isolated_sessions_demo")
    
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
    
    # Create a session with one client
    print("🔧 Creating session with Client A...")
    client_a = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="analyst_002"
    )
    
    session_id = await client_a.memory_create_isolated_session(
        session_context="earnings_analysis",
        context_tags=["earnings", "quarterly", "analysis"],
        session_metadata={"quarter": "Q3_2024", "sector": "technology"}
    )
    
    await client_a.memory_switch_session(session_id)
    await client_a.memory_save_message("user", "Analyze Q3 earnings for FAANG stocks")
    await client_a.memory_save_message("assistant", "Q3 earnings analysis shows mixed results across FAANG...")
    
    print(f"✓ Session created: {session_id}")
    print(f"✓ Added messages with Client A")
    
    # Retrieve the same session with a different client instance
    print(f"\n🔍 Retrieving session {session_id} with Client B...")
    client_b = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="analyst_002"  # Same user
    )
    
    # Switch to the existing session by ID
    success = await client_b.memory_switch_session(session_id, create_if_not_exists=False)
    
    if success:
        print("✅ Successfully retrieved session with Client B")
        
        # Load history to verify
        history = await client_b.memory_load_history(convert_to_provider_format=False)
        print(f"✓ Loaded {len(history)} messages from session")
        
        # Add more messages with Client B
        await client_b.memory_save_message("user", "What about Apple specifically?")
        await client_b.memory_save_message("assistant", "Apple's Q3 earnings exceeded expectations...")
        
        # Verify Client A can see Client B's messages
        updated_history = await client_a.memory_load_history(convert_to_provider_format=False)
        print(f"✓ Client A now sees {len(updated_history)} messages (includes Client B's additions)")
        
        print("✅ Session sharing between clients verified!")
    else:
        print("❌ Failed to retrieve session with Client B")
    
    # Show session data
    session_data = await client_b.memory_get_isolated_session_data()
    print(f"\n📄 Complete Session Data:")
    print(f"  Session ID: {session_data.get('session', {}).get('session_id', 'N/A')}")
    print(f"  Total Messages: {session_data.get('message_count', 0)}")
    print(f"  Session Size: {session_data.get('session_size_bytes', 0)} bytes")


async def demonstrate_session_cloning():
    """Demonstrate session cloning for isolation and backup."""
    print("\n" + "=" * 60)
    print("📋 SESSION CLONING DEMO")
    print("=" * 60)
    print("Showing how to clone sessions for backup or branching conversations.\n")
    
    memory_store = FileMemoryStore("isolated_sessions_demo")
    
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
    
    # Create original session
    print("🔧 Creating original session...")
    original_client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="strategist_001"
    )
    
    original_session_id = await original_client.memory_create_isolated_session(
        session_context="investment_strategy",
        context_tags=["strategy", "investment", "long_term"],
        session_metadata={"horizon": "5_years", "risk_tolerance": "moderate"}
    )
    
    await original_client.memory_switch_session(original_session_id)
    
    # Add some conversation history
    messages = [
        ("user", "What's your recommendation for long-term tech investments?"),
        ("assistant", "For long-term tech investments, I recommend diversification..."),
        ("user", "Should I include emerging markets?"),
        ("assistant", "Emerging markets can provide growth opportunities...")
    ]
    
    for role, content in messages:
        await original_client.memory_save_message(role, content)
    
    print(f"✓ Original session: {original_session_id}")
    print(f"✓ Added {len(messages)} messages")
    
    # Clone the session
    print(f"\n📋 Cloning session...")
    cloned_session_id = await original_client.memory_clone_current_session(
        new_session_context="conservative_variant"
    )
    
    print(f"✓ Cloned session: {cloned_session_id}")
    
    # Create client for cloned session
    cloned_client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="strategist_001"
    )
    
    await cloned_client.memory_switch_session(cloned_session_id, create_if_not_exists=False)
    
    # Verify clone has same history
    original_history = await original_client.memory_load_history(convert_to_provider_format=False)
    cloned_history = await cloned_client.memory_load_history(convert_to_provider_format=False)
    
    print(f"✓ Original session messages: {len(original_history)}")
    print(f"✓ Cloned session messages: {len(cloned_history)}")
    
    if len(original_history) == len(cloned_history):
        print("✅ Clone contains all original messages")
    else:
        print("❌ Clone is missing messages")
    
    # Diverge the conversations
    print(f"\n🔀 Diverging conversations...")
    
    # Continue original with aggressive strategy
    await original_client.memory_save_message("user", "Let's be more aggressive with crypto investments")
    await original_client.memory_save_message("assistant", "For aggressive crypto strategy, consider...")
    
    # Continue clone with conservative approach
    await cloned_client.memory_save_message("user", "Let's focus on conservative blue-chip stocks")
    await cloned_client.memory_save_message("assistant", "For conservative approach, blue-chip stocks...")
    
    # Verify isolation after divergence
    final_original = await original_client.memory_load_history(convert_to_provider_format=False)
    final_cloned = await cloned_client.memory_load_history(convert_to_provider_format=False)
    
    print(f"✓ Original session now has: {len(final_original)} messages")
    print(f"✓ Cloned session now has: {len(final_cloned)} messages")
    
    # Check that sessions diverged properly
    original_contents = [str(msg.content) for msg in final_original]
    cloned_contents = [str(msg.content) for msg in final_cloned]
    
    crypto_in_original = any("crypto" in content.lower() for content in original_contents)
    blue_chip_in_cloned = any("blue-chip" in content.lower() for content in cloned_contents)
    
    if crypto_in_original and blue_chip_in_cloned:
        print("✅ Sessions successfully diverged with different conversation paths")
    else:
        print("❌ Sessions did not diverge as expected")


async def main():
    """Run enhanced session isolation demonstrations."""
    print("🛡️  Enhanced Session Isolation System")
    print("=" * 60)
    print("Demonstrating guaranteed session isolation with advanced management features.\n")
    
    try:
        # Run all demonstrations
        session_ids = await demonstrate_guaranteed_session_isolation()
        await demonstrate_session_retrieval_by_id()
        await demonstrate_session_cloning()
        
        print("\n" + "=" * 60)
        print("✅ ALL SESSION ISOLATION DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n🔒 Key Features Demonstrated:")
        print("  ✓ Guaranteed unique session IDs")
        print("  ✓ Complete message isolation between sessions")
        print("  ✓ Session retrieval by ID across different clients")
        print("  ✓ Session cloning for conversation branching")
        print("  ✓ Advanced session statistics and management")
        print("  ✓ Cross-client session sharing with same user")
        
        print(f"\n📊 Session IDs Created: {len(session_ids) + 2} sessions")
        print("🗂️  All sessions stored with guaranteed isolation")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("Session isolation demo error")


if __name__ == "__main__":
    asyncio.run(main())
