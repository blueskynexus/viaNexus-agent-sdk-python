#!/usr/bin/env python3
"""
OpenAI Client Persistent Session Example

This example demonstrates how to use persistent sessions for
long-running conversations with maintained context and connection.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.openai_client import PersistentOpenAiClient

# Configure logging
logging.basicConfig(level=logging.INFO)

async def persistent_session_example():
    """Demonstrate persistent session usage"""
    
    # Configuration for persistent OpenAI client
    config = {
        "LLM_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"),
        "LLM_MODEL": "gpt-4o-mini",
        "max_tokens": 1500,
        "system_prompt": "You are a portfolio management AI assistant. Help users analyze their investments and provide strategic advice.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
            }
        }
    }
    
    # Create persistent client
    client = PersistentOpenAiClient(config)
    
    try:
        print("🔄 OpenAI Client Persistent Session Example")
        print("=" * 50)
        
        # Establish persistent connection
        session_id = await client.establish_persistent_connection()
        print(f"✅ Persistent connection established (Session: {session_id})")
        
        # Multiple questions in the same session
        print("\n💼 Portfolio Analysis Session:")
        
        # Question 1: Portfolio overview
        response1 = await client.ask_with_persistent_session(
            "I have a portfolio with 40% stocks, 30% bonds, 20% ETFs, and 10% cash. What's your assessment?"
        )
        print(f"\n👤 User: I have a portfolio with 40% stocks, 30% bonds, 20% ETFs, and 10% cash. What's your assessment?")
        print(f"🤖 Assistant: {response1}")
        
        # Question 2: Risk analysis (references previous context)
        response2 = await client.ask_with_persistent_session(
            "Given my current allocation, what are the main risks I should be concerned about?"
        )
        print(f"\n👤 User: Given my current allocation, what are the main risks I should be concerned about?")
        print(f"🤖 Assistant: {response2}")
        
        # Question 3: Rebalancing advice
        response3 = await client.ask_with_persistent_session(
            "Should I rebalance my portfolio? If so, what changes would you recommend?"
        )
        print(f"\n👤 User: Should I rebalance my portfolio? If so, what changes would you recommend?")
        print(f"🤖 Assistant: {response3}")
        
        # Question 4: Market timing
        response4 = await client.ask_with_persistent_session(
            "With the current market conditions, is this a good time to implement those changes?"
        )
        print(f"\n👤 User: With the current market conditions, is this a good time to implement those changes?")
        print(f"🤖 Assistant: {response4}")
        
        # Check connection health
        is_healthy = await client._verify_connection_health()
        print(f"\n🔍 Connection Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        
        print("\n✅ Persistent session example completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up persistent connection
        await client.close_persistent_connection()
        await client.cleanup()
        print("🧹 Persistent connection closed and client cleaned up")

if __name__ == "__main__":
    asyncio.run(persistent_session_example())
