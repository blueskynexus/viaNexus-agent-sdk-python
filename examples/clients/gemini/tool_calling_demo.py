#!/usr/bin/env python3
"""
Gemini Client Tool Calling Demo

This example demonstrates how the Gemini client integrates with
MCP tools for function calling and real-time data access.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.gemini_client import GeminiClient

# Configure logging to see tool execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def tool_calling_demo():
    """Demonstrate Gemini client with MCP tool integration"""
    
    # Configuration for Gemini client with tool calling
    config = {
        "LLM_API_KEY": os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here"),
        "LLM_MODEL": "gemini-2.5-flash",  # Good for tool calling
        "max_tokens": 2000,
        "system_prompt": """You are a financial AI assistant with access to real-time market data and analysis tools. 
        When users ask about stocks, market data, or financial analysis, use the available tools to provide accurate, 
        up-to-date information. Always explain what tools you're using and why.""",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
            }
        }
    }
    
    # Create client with memory to track tool usage
    client = GeminiClient.with_in_memory_store(config, user_id="tool_demo_user")
    
    try:
        print("🔧 Gemini Client Tool Calling Demo")
        print("=" * 40)
        
        # Initialize the client
        await client.initialize()
        print("✅ Client initialized successfully")
        
        # Check available tools
        tools = await client._get_available_tools()
        if tools and hasattr(tools, 'function_declarations'):
            print(f"\n🛠️ Available Tools ({len(tools.function_declarations)}):")
            for i, tool in enumerate(tools.function_declarations, 1):
                print(f"  {i}. {tool['name']}: {tool['description']}")
        else:
            print("⚠️ No tools available. Make sure viaNexus MCP server is running.")
            return
        
        # Example 1: Stock price query (likely to use tools)
        print("\n1️⃣ Stock Price Query with Tool Calling:")
        response1 = await client.ask_question(
            "What's the current stock price of Apple (AAPL) and how has it performed over the last month?",
            maintain_history=True
        )
        print(f"👤 User: What's the current stock price of Apple (AAPL) and how has it performed over the last month?")
        print(f"🤖 Assistant: {response1}")
        
        # Example 2: Market analysis (may use multiple tools)
        print("\n2️⃣ Market Analysis with Multiple Tools:")
        response2 = await client.ask_question(
            "Can you compare the P/E ratios of Apple, Microsoft, and Google? Which one looks most attractive right now?",
            maintain_history=True
        )
        print(f"👤 User: Can you compare the P/E ratios of Apple, Microsoft, and Google? Which one looks most attractive right now?")
        print(f"🤖 Assistant: {response2}")
        
        # Example 3: Portfolio analysis
        print("\n3️⃣ Portfolio Analysis:")
        response3 = await client.ask_question(
            "I own 100 shares of AAPL bought at $150. What's my current gain/loss and what's the latest news affecting the stock?",
            maintain_history=True
        )
        print(f"👤 User: I own 100 shares of AAPL bought at $150. What's my current gain/loss and what's the latest news affecting the stock?")
        print(f"🤖 Assistant: {response3}")
        
        # Example 4: Sector analysis
        print("\n4️⃣ Sector Analysis:")
        response4 = await client.ask_question(
            "How is the technology sector performing today? Show me the top gainers and losers.",
            maintain_history=True
        )
        print(f"👤 User: How is the technology sector performing today? Show me the top gainers and losers.")
        print(f"🤖 Assistant: {response4}")
        
        # Show conversation summary
        print(f"\n📊 Conversation Summary:")
        print(f"  • Total messages: {len(client.messages)}")
        print(f"  • Tools were automatically called when needed")
        print(f"  • Responses integrated tool results seamlessly")
        
        print("\n✅ Tool calling demo completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await client.cleanup()
        print("🧹 Client cleaned up")

async def streaming_with_tools_demo():
    """Demonstrate streaming responses with tool calling"""
    
    config = {
        "LLM_API_KEY": os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here"),
        "LLM_MODEL": "gemini-2.5-flash",
        "max_tokens": 1500,
        "system_prompt": "You are a real-time financial assistant. Use tools to get current data and provide analysis.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
            }
        }
    }
    
    client = GeminiClient.without_memory(config)
    
    try:
        print("\n🌊 Streaming with Tools Demo")
        print("=" * 35)
        
        await client.initialize()
        
        print("👤 User: Give me a real-time analysis of Tesla's stock performance today")
        print("🤖 Assistant: ", end="", flush=True)
        
        # This will stream the response while calling tools
        await client.process_query("Give me a real-time analysis of Tesla's stock performance today")
        
        print("\n✅ Streaming with tools demo completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(tool_calling_demo())
    asyncio.run(streaming_with_tools_demo())
