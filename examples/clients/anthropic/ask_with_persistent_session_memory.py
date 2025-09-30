#!/usr/bin/env python3
"""
PersistentAnthropicClient ask_with_persistent_session() Memory Integration Example.
Demonstrates how to use persistent MCP connections with automatic memory integration.
"""

import asyncio
import logging
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient


async def demonstrate_ask_with_persistent_session():
    """Demonstrate ask_with_persistent_session() with memory integration."""
    print("🔥 ask_with_persistent_session() + Memory Integration")
    print("=" * 55)
    print("Complete workflow for persistent MCP + memory management\n")
    
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
    
    # Step 1: Create PersistentAnthropicClient with memory
    print("1️⃣ Creating PersistentAnthropicClient with Memory")
    print("-" * 45)
    
    client = PersistentAnthropicClient(
        config=config,
        memory_session_id="financial_advisor_session",
        user_id="wealth_manager"
    )
    
    print(f"✓ Client created")
    print(f"  Memory Session ID: {client.memory_session_id}")
    print(f"  Memory Store: {type(client.memory_store).__name__}")
    print(f"  Memory Enabled: {client.memory_enabled}")
    
    # Step 2: Establish conversation context in memory
    print(f"\n2️⃣ Building Conversation Context")
    print("-" * 35)
    
    # Add client background to memory
    await client.memory_save_message("user", "I'm a high-net-worth client looking for investment advice")
    await client.memory_save_message("assistant", "I understand you're seeking investment guidance. I'll provide personalized advice based on your profile and goals.")
    await client.memory_save_message("user", "My risk tolerance is moderate and I prefer diversified portfolios")
    await client.memory_save_message("assistant", "Perfect. A moderate risk tolerance suggests a balanced approach with 60-70% stocks and 30-40% bonds, diversified across sectors and geographies.")
    
    context_history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Established conversation context: {len(context_history)} messages")
    
    for i, msg in enumerate(context_history, 1):
        role = msg.role.value.upper()
        content = str(msg.content)[:60] + "..." if len(str(msg.content)) > 60 else str(msg.content)
        print(f"   {i}. [{role}] {content}")
    
    # Step 3: Simulate establishing MCP connection
    print(f"\n3️⃣ Establishing Persistent MCP Connection")
    print("-" * 40)
    
    print("✓ Simulating MCP connection establishment...")
    print("  (In real usage, this would connect to viaNexus MCP server)")
    print("  Note: This example focuses on the memory integration aspect")
    
    # For demo purposes, we'll simulate the connection without actually connecting
    # In real usage, you would call:
    # mcp_session_id = await client.establish_persistent_connection()
    
    print("✓ MCP connection ready (simulated)")
    print(f"  Memory Session: {client.memory_session_id}")
    print(f"  MCP Session: (would be generated on real connection)")
    
    # Step 4: Use ask_with_persistent_session with memory integration
    print(f"\n4️⃣ Using ask_with_persistent_session() with Memory")
    print("-" * 48)
    
    # This is where the magic happens - the method automatically:
    # 1. Loads conversation history from memory
    # 2. Uses persistent MCP connection for tools
    # 3. Saves the interaction back to memory
    
    questions = [
        "What are some good technology stocks for my moderate risk portfolio?",
        "How should I allocate between domestic and international stocks?",
        "What about adding some REITs for diversification?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuery {i}: {question}")
        print("-" * 50)
        
        # Simulate the ask_with_persistent_session call
        # In real usage with MCP server, this would:
        # response = await client.ask_with_persistent_session(question)
        
        # For demo, we'll show what happens step by step
        print("🔄 ask_with_persistent_session() workflow:")
        print("   1. Loading conversation history from memory...")
        
        # Show current context that would be loaded
        current_history = await client.memory_load_history(convert_to_provider_format=False)
        print(f"      ✓ Loaded {len(current_history)} messages for context")
        
        print("   2. Sending query with context to MCP server...")
        print("   3. Processing response with available tools...")
        print("   4. Generating contextualized response...")
        
        # Simulate a response based on the conversation context
        simulated_responses = [
            "Based on your moderate risk tolerance, consider large-cap tech stocks like Microsoft (MSFT), Apple (AAPL), and Alphabet (GOOGL). These provide growth potential with relatively stable business models.",
            "For your diversified approach, I recommend 70% domestic stocks and 30% international. This gives you exposure to global growth while maintaining a US equity core that aligns with your risk profile.",
            "REITs are an excellent addition for diversification. Consider allocating 5-10% of your portfolio to REITs, which can provide steady income and inflation protection while being uncorrelated to traditional stocks and bonds."
        ]
        
        response = simulated_responses[i-1]
        
        print("   5. Saving interaction to memory...")
        
        # Save the interaction to memory
        await client.memory_save_message("user", question)
        await client.memory_save_message("assistant", response)
        
        print(f"      ✓ Saved question and response to memory")
        print(f"\n💬 Response: {response}")
    
    # Step 5: Show memory continuity
    print(f"\n5️⃣ Memory Continuity Demonstration")
    print("-" * 35)
    
    # Show complete conversation history
    final_history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ Complete conversation: {len(final_history)} messages")
    
    # Show session statistics
    stats = await client.memory_get_session_statistics()
    print(f"✓ Session stats:")
    print(f"  Messages: {stats['message_count']}")
    print(f"  Size: {stats['session_size_bytes']} bytes")
    print(f"  Duration: {stats['duration_seconds']:.3f} seconds")
    
    # Step 6: Demonstrate session persistence
    print(f"\n6️⃣ Session Persistence Across Client Instances")
    print("-" * 45)
    
    # Create a new client instance with the same memory session
    new_client = PersistentAnthropicClient(
        config=config,
        memory_session_id="financial_advisor_session",  # Same session ID!
        user_id="wealth_manager"
    )
    
    # Load conversation history in new client
    persistent_history = await new_client.memory_load_history(convert_to_provider_format=False)
    print(f"✓ New client loaded conversation: {len(persistent_history)} messages")
    
    # Continue conversation from new client
    followup_question = "Given our discussion, what's your overall portfolio recommendation?"
    followup_response = "Based on our conversation about your moderate risk tolerance and diversification preferences, I recommend: 65% stocks (45% domestic large-cap including the tech stocks we discussed, 20% international), 25% bonds (mix of government and corporate), 10% alternatives (REITs as discussed). This provides balanced growth with appropriate risk management."
    
    await new_client.memory_save_message("user", followup_question)
    await new_client.memory_save_message("assistant", followup_response)
    
    print(f"✓ Continued conversation seamlessly")
    print(f"💬 Follow-up Q: {followup_question}")
    print(f"💬 Follow-up A: {followup_response[:100]}...")
    
    # Verify both clients see the complete conversation
    client1_final = await client.memory_load_history(convert_to_provider_format=False)
    client2_final = await new_client.memory_load_history(convert_to_provider_format=False)
    
    print(f"✓ Memory persistence verified:")
    print(f"  Original client sees: {len(client1_final)} messages")
    print(f"  New client sees: {len(client2_final)} messages")
    print(f"  Conversations match: {len(client1_final) == len(client2_final)}")


async def demonstrate_advanced_features():
    """Show advanced features of ask_with_persistent_session()."""
    print(f"\n" + "=" * 55)
    print("🚀 Advanced ask_with_persistent_session() Features")
    print("=" * 55)
    
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
    
    client = PersistentAnthropicClient(
        config=config,
        memory_session_id="advanced_features_demo",
        user_id="power_user"
    )
    
    print("💡 Method Signature and Options:")
    print("```python")
    print("await client.ask_with_persistent_session(")
    print("    question='Your question here',")
    print("    maintain_history=True,    # Keep conversation context")
    print("    use_memory=True          # Save to/load from memory")
    print(")")
    print("```")
    
    print(f"\n🎯 Key Features:")
    print(f"✓ Automatic memory integration (no manual save/load needed)")
    print(f"✓ Persistent MCP connection (faster tool access)")
    print(f"✓ Conversation context preservation")
    print(f"✓ Cross-session memory continuity")
    print(f"✓ Real-time tool access via MCP protocol")
    
    print(f"\n🔧 Configuration Options:")
    print(f"• maintain_history=True: Maintains conversation flow")
    print(f"• maintain_history=False: Treats each query independently")
    print(f"• use_memory=True: Saves interactions to memory store")
    print(f"• use_memory=False: Temporary interactions only")
    
    print(f"\n📊 Performance Benefits:")
    print(f"• Persistent MCP: No connection overhead per query")
    print(f"• InMemoryStore: Ultra-fast context loading")
    print(f"• Session reuse: Efficient resource utilization")
    print(f"• Tool caching: MCP tools remain accessible")
    
    print(f"\n🎪 Perfect Use Cases:")
    print(f"• Financial advisory sessions")
    print(f"• Long-running research projects")
    print(f"• Trading strategy development")
    print(f"• Multi-step analysis workflows")
    print(f"• Interactive data exploration")


async def main():
    """Run the complete ask_with_persistent_session() demonstration."""
    print("🔥 Complete ask_with_persistent_session() + Memory Demo")
    print("=" * 60)
    print("Comprehensive guide to persistent MCP connections with memory\n")
    
    try:
        await demonstrate_ask_with_persistent_session()
        await demonstrate_advanced_features()
        
        print("\n" + "=" * 60)
        print("✅ ask_with_persistent_session() DEMO COMPLETE!")
        print("=" * 60)
        print("\n🎉 Summary:")
        print("  🔗 Persistent MCP connections for efficient tool access")
        print("  🧠 Automatic memory management for conversation continuity")
        print("  ⚡ Seamless integration between MCP protocol and memory")
        print("  🔄 Cross-session persistence for long-term workflows")
        print("  🎯 Perfect for financial analysis and advisory use cases")
        
        print(f"\n💻 Ready to use in your application!")
        print(f"Just call: await client.ask_with_persistent_session(question)")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("ask_with_persistent_session demo error")


if __name__ == "__main__":
    asyncio.run(main())
