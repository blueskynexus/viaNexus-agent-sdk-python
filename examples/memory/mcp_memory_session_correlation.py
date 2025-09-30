#!/usr/bin/env python3
"""
MCP and Memory Session Correlation Demo.
Shows how MCP session IDs relate to (but don't replace) memory session IDs.
"""

import asyncio
import logging
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient, PersistentAnthropicClient


async def demonstrate_session_id_separation():
    """Demonstrate why MCP and memory session IDs serve different purposes."""
    print("🔗 MCP vs Memory Session ID Separation Demo")
    print("=" * 60)
    print("Showing why we keep MCP and memory session IDs separate\n")
    
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
    
    # Create regular AnthropicClient
    print("1️⃣ Regular AnthropicClient (no persistent MCP connection)")
    client1 = AnthropicClient(
        config=config,
        user_id="demo_user",
        memory_session_id="logical_conversation_001"
    )
    
    # Add some messages to memory
    await client1.memory_save_message("user", "What's the weather like?")
    await client1.memory_save_message("assistant", "I'll help you check the weather...")
    
    session_info1 = client1.memory_get_current_session_info()
    print(f"   Memory Session ID: {session_info1['session_id']}")
    print(f"   Memory Enabled: {session_info1['memory_enabled']}")
    
    # Check if MCP session correlation exists
    if client1._current_session and client1._current_session.session_metadata:
        metadata = client1._current_session.session_metadata
        mcp_correlation = metadata.get("mcp_session_correlation", "Not available")
        print(f"   MCP Correlation: {mcp_correlation}")
    
    # Create PersistentAnthropicClient
    print("\n2️⃣ PersistentAnthropicClient (with persistent MCP connection)")
    persistent_client = PersistentAnthropicClient(
        config=config,
        user_id="demo_user",
        memory_session_id="logical_conversation_002"
    )
    
    # Add messages to persistent client
    await persistent_client.memory_save_message("user", "Analyze my portfolio")
    await persistent_client.memory_save_message("assistant", "I'll analyze your portfolio holdings...")
    
    session_info2 = persistent_client.memory_get_current_session_info()
    print(f"   Memory Session ID: {session_info2['session_id']}")
    print(f"   MCP Session ID: {getattr(persistent_client, '_mcp_session_id', 'Not established')}")
    
    # Check correlation in persistent client
    if persistent_client._current_session and persistent_client._current_session.session_metadata:
        metadata = persistent_client._current_session.session_metadata
        mcp_correlation = metadata.get("mcp_session_correlation", "Not available")
        print(f"   MCP Correlation: {mcp_correlation}")


async def demonstrate_memory_persistence_vs_mcp_lifecycle():
    """Show how memory persists while MCP sessions are ephemeral."""
    print("\n" + "=" * 60)
    print("🔄 Memory Persistence vs MCP Lifecycle Demo")
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
    
    # Scenario: User has a long-running conversation that spans multiple connections
    print("Scenario: Long conversation spanning multiple MCP connections\n")
    
    # Phase 1: Start conversation
    print("Phase 1: Start conversation with first client")
    client_phase1 = AnthropicClient(
        config=config,
        user_id="analyst_alice",
        memory_session_id="quarterly_analysis_q3_2024"  # Logical, persistent ID
    )
    
    await client_phase1.memory_save_message("user", "Let's analyze Q3 earnings")
    await client_phase1.memory_save_message("assistant", "I'll help you analyze Q3 earnings. Which sector interests you?")
    await client_phase1.memory_save_message("user", "Focus on technology companies")
    await client_phase1.memory_save_message("assistant", "Technology companies in Q3 showed strong performance...")
    
    phase1_info = client_phase1.memory_get_current_session_info()
    print(f"   Memory Session: {phase1_info['session_id']}")
    
    history_phase1 = await client_phase1.memory_load_history(convert_to_provider_format=False)
    print(f"   Messages after Phase 1: {len(history_phase1)}")
    
    # Phase 2: Simulate connection loss and reconnection (new client instance)
    print("\nPhase 2: Connection lost, user reconnects later (new client instance)")
    client_phase2 = AnthropicClient(
        config=config,
        user_id="analyst_alice",
        memory_session_id="quarterly_analysis_q3_2024"  # SAME logical session ID
    )
    
    # Load previous conversation
    history_phase2 = await client_phase2.memory_load_history(convert_to_provider_format=False)
    print(f"   Loaded conversation history: {len(history_phase2)} messages")
    print("   ✓ Previous conversation context restored!")
    
    # Continue conversation
    await client_phase2.memory_save_message("user", "What about Apple specifically?")
    await client_phase2.memory_save_message("assistant", "Apple's Q3 results exceeded expectations...")
    
    final_history = await client_phase2.memory_load_history(convert_to_provider_format=False)
    print(f"   Final conversation length: {len(final_history)} messages")
    
    # Show session correlation differences
    phase1_metadata = client_phase1._current_session.session_metadata if client_phase1._current_session else {}
    phase2_metadata = client_phase2._current_session.session_metadata if client_phase2._current_session else {}
    
    print(f"\n   Phase 1 MCP correlation: {phase1_metadata.get('mcp_session_correlation', 'None')}")
    print(f"   Phase 2 MCP correlation: {phase2_metadata.get('mcp_session_correlation', 'None')}")
    print("   ↳ Different MCP sessions, SAME memory session = conversation continuity!")


async def demonstrate_multiple_contexts_single_mcp():
    """Show multiple memory contexts can share one MCP session."""
    print("\n" + "=" * 60)
    print("🎯 Multiple Memory Contexts, Single MCP Session")
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
    
    # Create multiple clients for different conversation contexts
    # but they might share the same underlying MCP connection
    
    trading_client = AnthropicClient(
        config=config,
        user_id="trader_bob",
        memory_session_id="trading_session_morning"
    )
    
    research_client = AnthropicClient(
        config=config,
        user_id="trader_bob", 
        memory_session_id="research_session_morning"
    )
    
    risk_client = AnthropicClient(
        config=config,
        user_id="trader_bob",
        memory_session_id="risk_analysis_session"
    )
    
    # Add different conversations to each context
    print("Creating separate conversation contexts:")
    
    # Trading context
    await trading_client.memory_save_message("user", "Buy 100 shares of NVDA")
    await trading_client.memory_save_message("assistant", "Order placed for 100 NVDA shares at market price")
    print("   ✓ Trading context: Order management")
    
    # Research context  
    await research_client.memory_save_message("user", "Research semiconductor industry trends")
    await research_client.memory_save_message("assistant", "Semiconductor industry analysis shows strong AI demand...")
    print("   ✓ Research context: Industry analysis")
    
    # Risk context
    await risk_client.memory_save_message("user", "Calculate portfolio VaR")
    await risk_client.memory_save_message("assistant", "Portfolio Value at Risk calculation shows...")
    print("   ✓ Risk context: Risk assessment")
    
    # Show session isolation
    print(f"\nSession Isolation Verification:")
    
    trading_history = await trading_client.memory_load_history(convert_to_provider_format=False)
    research_history = await research_client.memory_load_history(convert_to_provider_format=False)
    risk_history = await risk_client.memory_load_history(convert_to_provider_format=False)
    
    print(f"   Trading context: {len(trading_history)} messages")
    print(f"   Research context: {len(research_history)} messages")
    print(f"   Risk context: {len(risk_history)} messages")
    
    # Verify no cross-contamination
    trading_content = [str(msg.content) for msg in trading_history]
    research_content = [str(msg.content) for msg in research_history]
    
    has_contamination = any("NVDA" in content for content in research_content)
    print(f"   Cross-contamination check: {'❌ Found' if has_contamination else '✅ None'}")
    
    # Show all sessions belong to same user
    all_sessions = await trading_client.memory_get_user_sessions()
    print(f"   Total user sessions: {len(all_sessions)}")


async def demonstrate_best_practices():
    """Show best practices for session ID management."""
    print("\n" + "=" * 60)
    print("💡 Session ID Best Practices")
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
    
    print("✅ GOOD: Descriptive, user-meaningful memory session IDs")
    
    # Good examples
    good_examples = [
        ("portfolio_review_2024_q3", "Portfolio review for Q3 2024"),
        ("tax_planning_strategy_2024", "Tax planning discussion"),
        ("market_analysis_tech_sector", "Technology sector analysis"),
        ("risk_assessment_crypto", "Cryptocurrency risk evaluation")
    ]
    
    for session_id, description in good_examples:
        client = AnthropicClient(
            config=config,
            user_id="best_practices_user",
            memory_session_id=session_id
        )
        
        await client.memory_save_message("user", f"Starting {description}")
        session_info = client.memory_get_current_session_info()
        print(f"   ✓ {session_id}")
        print(f"     Purpose: {description}")
        print(f"     Generated ID: {session_info['session_id']}")
    
    print(f"\n❌ AVOID: Using MCP session IDs as memory session IDs")
    print(f"   Problems:")
    print(f"   • Connection-dependent (lost on reconnect)")
    print(f"   • Server-generated (not user-meaningful)")
    print(f"   • Protocol-specific (not conversation-logical)")
    print(f"   • Short-lived (tied to network session)")
    
    print(f"\n🎯 RECOMMENDED: Correlation approach (what we implemented)")
    print(f"   Benefits:")
    print(f"   • Memory sessions: User-controlled, persistent, meaningful")
    print(f"   • MCP sessions: Protocol-level, connection-scoped")
    print(f"   • Correlation metadata: Debugging and traceability")
    print(f"   • Best of both: Logical persistence + protocol efficiency")


async def main():
    """Run MCP and memory session correlation demonstrations."""
    print("🔗 MCP and Memory Session Correlation Analysis")
    print("=" * 60)
    print("Understanding the relationship between MCP and memory sessions\n")
    
    try:
        await demonstrate_session_id_separation()
        await demonstrate_memory_persistence_vs_mcp_lifecycle()
        await demonstrate_multiple_contexts_single_mcp()
        await demonstrate_best_practices()
        
        print("\n" + "=" * 60)
        print("✅ SESSION CORRELATION ANALYSIS COMPLETE!")
        print("=" * 60)
        print("\n🎯 Key Conclusions:")
        print("  🔗 MCP sessions: Protocol-level, connection-scoped, ephemeral")
        print("  🧠 Memory sessions: Application-level, user-scoped, persistent")
        print("  📊 Correlation: Track relationship without merging purposes")
        print("  ✅ Separation: Maintains flexibility and proper abstractions")
        print("  🎪 Best practice: Let each serve its intended purpose")
        
        print(f"\n💡 Decision: Keep MCP and memory session IDs separate!")
        print(f"🔗 Use correlation metadata for debugging and traceability")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("Session correlation demo error")


if __name__ == "__main__":
    asyncio.run(main())
