#!/usr/bin/env python3
"""
Basic Gemini Client Setup Example

This example demonstrates the basic setup and usage of the Gemini client
with viaNexus integration and memory support.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)

async def basic_gemini_example():
    """Basic Gemini client usage example"""
    
    # Configuration for Gemini client
    config = {
        "LLM_API_KEY": os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here"),
        "LLM_MODEL": "gemini-2.5-flash",  # or "gemini-pro", "gemini-pro-vision"
        "max_tokens": 1000,
        "system_prompt": "You are a helpful financial AI assistant with access to real-time market data.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
            }
        }
    }
    
    # Create client without memory for simple usage
    client = GeminiClient.without_memory(config)
    
    try:
        print("🚀 Gemini Client Basic Setup Example")
        print("=" * 50)
        
        # Initialize the client
        await client.initialize()
        print("✅ Client initialized successfully")
        
        # Ask a single question (no conversation history)
        print("\n📝 Single Question Example:")
        question = "What is the current price of Apple stock?"
        response = await client.ask_single_question(question)
        print(f"Q: {question}")
        print(f"A: {response}")
        
        # Ask another independent question
        print("\n📝 Another Single Question:")
        question2 = "Explain the concept of market volatility"
        response2 = await client.ask_single_question(question2)
        print(f"Q: {question2}")
        print(f"A: {response2}")
        
        print("\n✅ Basic setup example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await client.cleanup()
        print("🧹 Client cleaned up")

if __name__ == "__main__":
    asyncio.run(basic_gemini_example())