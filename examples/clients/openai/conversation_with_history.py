#!/usr/bin/env python3
"""
OpenAI Client Conversation with History Example

This example demonstrates how to maintain conversation history
using the OpenAI responses API with memory integration.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.openai_client import OpenAiClient

# Configure logging
logging.basicConfig(level=logging.INFO)

async def conversation_history_example():
    """Demonstrate conversation with maintained history"""
    
    # Configuration for OpenAI client
    config = {
        "LLM_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"),
        "LLM_MODEL": "gpt-4o-mini",
        "max_tokens": 1500,
        "max_history_length": 20,  # Keep last 20 messages
        "system_prompt": "You are a financial advisor AI. Maintain context across the conversation and refer to previous topics when relevant.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
            }
        }
    }
    
    # Create client with in-memory conversation history
    client = OpenAiClient.with_in_memory_store(config)
    
    try:
        print("💬 OpenAI Client Conversation History Example")
        print("=" * 55)
        
        # Initialize the client
        await client.initialize()
        print("✅ Client initialized with memory store")
        
        # Start a conversation with context
        print("\n🗣️ Starting conversation with history...")
        
        # First question
        response1 = await client.ask_question(
            "I'm interested in investing in technology stocks. Can you help me understand the current market?",
            maintain_history=True
        )
        print(f"\n👤 User: I'm interested in investing in technology stocks. Can you help me understand the current market?")
        print(f"🤖 Assistant: {response1}")
        
        # Follow-up question that references previous context
        response2 = await client.ask_question(
            "Which specific tech companies would you recommend for a long-term investment?",
            maintain_history=True
        )
        print(f"\n👤 User: Which specific tech companies would you recommend for a long-term investment?")
        print(f"🤖 Assistant: {response2}")
        
        # Another follow-up
        response3 = await client.ask_question(
            "What about the risks associated with the companies you mentioned?",
            maintain_history=True
        )
        print(f"\n👤 User: What about the risks associated with the companies you mentioned?")
        print(f"🤖 Assistant: {response3}")
        
        # Show conversation history
        print(f"\n📊 Conversation History ({len(client.messages)} messages):")
        for i, msg in enumerate(client.messages, 1):
            role = "👤" if msg["role"] == "user" else "🤖"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"  {i}. {role} {msg['role']}: {content}")
        
        print("\n✅ Conversation history example completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await client.cleanup()
        print("🧹 Client cleaned up")

if __name__ == "__main__":
    asyncio.run(conversation_history_example())
