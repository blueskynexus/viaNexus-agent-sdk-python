#!/usr/bin/env python3
"""
Cross-client conversation example demonstrating client-agnostic memory.
Shows how the same conversation can continue across different LLM providers.
"""

import asyncio
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)

from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient
from vianexus_agent_sdk.memory.stores.file_memory import FileMemoryStore


class MockGeminiClient:
    """
    Mock Gemini client demonstrating how any client can use the memory system.
    In a real implementation, this would be the actual GeminiClient.
    """
    
    def __init__(
        self, 
        config: Dict[str, Any],
        memory_store=None,
        memory_session_id=None,
        user_id=None
    ):
        # Import the memory mixin (in real implementation, this would inherit from it)
        from vianexus_agent_sdk.memory import ConversationMemoryMixin
        
        # Simulate the mixin initialization
        self.memory_store = memory_store
        self.memory_session_id = memory_session_id
        self.user_id = user_id
        self.provider_name = "gemini"
        self.memory_enabled = memory_store is not None
        
        # Initialize memory mixin manually for demo
        self.mixin = ConversationMemoryMixin(
            memory_store=memory_store,
            memory_session_id=memory_session_id,
            user_id=user_id,
            provider_name="gemini"
        )
    
    async def ask_question(self, question: str, use_memory: bool = True) -> str:
        """Mock Gemini question asking with memory integration."""
        
        # Load conversation history from memory
        if use_memory:
            history = await self.mixin.memory_load_history(convert_to_provider_format=False)
            print(f"[Gemini] Loaded {len(history)} messages from shared memory")
            
            # Save user question
            await self.mixin.memory_save_message("user", question)
        
        # Mock Gemini response (in reality, this would call Gemini API)
        mock_response = f"[Gemini Response] This is a simulated response to: {question}"
        
        # Save response to memory
        if use_memory:
            await self.mixin.memory_save_message("assistant", mock_response)
        
        return mock_response
    
    def memory_get_session_info(self):
        """Get session info from mixin."""
        return self.mixin.memory_get_session_info()


async def demonstrate_cross_client_conversation():
    """Demonstrate conversation continuity across different clients."""
    print("🔄 CROSS-CLIENT CONVERSATION DEMO")
    print("=" * 60)
    print("This demo shows how conversations can continue seamlessly")
    print("across different LLM providers using the same memory store.\n")
    
    # Shared memory store
    memory_store = FileMemoryStore("cross_client_conversations")
    
    # Shared session configuration
    session_id = "financial_analysis_session"
    user_id = "portfolio_manager_001"
    
    # Base configuration
    config = {
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "sample.jwt.token"
            }
        },
        "LLM_API_KEY": "your-anthropic-api-key",
        "system_prompt": "You are a financial analysis expert."
    }
    
    # Create Anthropic client
    anthropic_client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        memory_session_id=session_id,
        user_id=user_id
    )
    
    # Create mock Gemini client
    gemini_client = MockGeminiClient(
        config=config,
        memory_store=memory_store,
        memory_session_id=session_id,  # Same session!
        user_id=user_id
    )
    
    print(f"✓ Created clients sharing session: {session_id}")
    print(f"  Anthropic: {anthropic_client.memory_get_session_info()}")
    print(f"  Gemini: {gemini_client.memory_get_session_info()}\n")
    
    # Conversation flow: Start with Anthropic
    print("🤖 Starting conversation with Anthropic...")
    await anthropic_client.memory_save_message(
        "user", 
        "I need analysis of tech stocks for Q4 portfolio rebalancing"
    )
    await anthropic_client.memory_save_message(
        "assistant",
        "I'll help you analyze tech stocks for Q4. What specific companies are you considering?"
    )
    print("  ✓ Anthropic conversation started")
    
    # Continue with Gemini - it should see the previous context
    print("\n🔮 Switching to Gemini (same conversation)...")
    gemini_response = await gemini_client.ask_question(
        "Please focus on FAANG stocks specifically"
    )
    print(f"  ✓ Gemini response: {gemini_response}")
    
    # Switch back to Anthropic - it should see Gemini's contribution
    print("\n🤖 Back to Anthropic (conversation continues)...")
    await anthropic_client.memory_save_message(
        "user",
        "What's your take on Apple vs Microsoft for the next quarter?"
    )
    await anthropic_client.memory_save_message(
        "assistant", 
        "Based on our discussion about FAANG stocks, here's my Apple vs Microsoft analysis..."
    )
    print("  ✓ Anthropic continued the conversation with context")
    
    # Show complete conversation history
    print("\n📜 COMPLETE CONVERSATION HISTORY:")
    print("-" * 40)
    
    history = await anthropic_client.memory_load_history(convert_to_provider_format=False)
    
    for i, msg in enumerate(history, 1):
        provider_info = f"[{msg.provider or 'unknown'}]" if msg.provider else ""
        print(f"{i:2d}. {msg.role.value.upper()} {provider_info}: {str(msg.content)[:80]}...")
    
    print(f"\n✅ Total messages: {len(history)}")
    print("✅ Conversation maintained across both clients!")
    
    return len(history)


async def demonstrate_session_switching():
    """Demonstrate switching between different conversation topics."""
    print("\n" + "=" * 60)
    print("🔄 SESSION SWITCHING DEMO")
    print("=" * 60)
    
    memory_store = FileMemoryStore("multi_session_conversations")
    
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
    
    # Create client
    client = AnthropicClient(
        config=config,
        memory_store=memory_store,
        user_id="analyst_002"
    )
    
    # Session 1: Tech Analysis
    print("\n📊 Session 1: Tech Stock Analysis")
    await client.memory_switch_session("tech_analysis_session")
    await client.memory_save_message("user", "Analyze NVIDIA's recent performance")
    await client.memory_save_message("assistant", "NVIDIA shows strong growth due to AI demand...")
    print(f"  ✓ Session: {client.memory_session_id}")
    
    # Session 2: Risk Assessment
    print("\n⚠️  Session 2: Risk Assessment")
    await client.memory_switch_session("risk_assessment_session")
    await client.memory_save_message("user", "What are the key risks in current market?")
    await client.memory_save_message("assistant", "Current key risks include inflation concerns...")
    print(f"  ✓ Session: {client.memory_session_id}")
    
    # Session 3: Portfolio Review
    print("\n💼 Session 3: Portfolio Review")
    await client.memory_switch_session("portfolio_review_session")
    await client.memory_save_message("user", "Review my Q3 portfolio performance")
    await client.memory_save_message("assistant", "Your Q3 portfolio shows mixed results...")
    print(f"  ✓ Session: {client.memory_session_id}")
    
    # Show all user sessions
    user_sessions = await client.memory_get_user_sessions()
    print(f"\n👤 User has {len(user_sessions)} active sessions:")
    
    for session in user_sessions:
        print(f"  📝 {session.session_id}")
        print(f"     Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"     Messages: {session.message_count}")
        print(f"     Topic: {session.session_metadata}")
        print()
    
    # Demonstrate context isolation
    print("🔍 Demonstrating context isolation...")
    
    # Switch back to tech analysis
    await client.memory_switch_session("tech_analysis_session")
    tech_history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"  Tech session history: {len(tech_history)} messages")
    
    # Switch to risk assessment
    await client.memory_switch_session("risk_assessment_session")
    risk_history = await client.memory_load_history(convert_to_provider_format=False)
    print(f"  Risk session history: {len(risk_history)} messages")
    
    print("✅ Each session maintains isolated conversation context!")


async def main():
    """Run cross-client conversation demonstrations."""
    print("🌐 Cross-Client Memory System Demonstration")
    print("=" * 60)
    print("Showing how different LLM clients can share conversation memory")
    print("for seamless user experiences across providers.\n")
    
    try:
        message_count = await demonstrate_cross_client_conversation()
        await demonstrate_session_switching()
        
        print("\n" + "=" * 60)
        print("✅ Cross-client memory demonstrations completed!")
        print(f"✅ Processed {message_count} messages across multiple providers")
        print("✅ Demonstrated session isolation and switching")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logging.exception("Cross-client demo error")


if __name__ == "__main__":
    asyncio.run(main())
