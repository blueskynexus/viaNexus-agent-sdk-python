#!/usr/bin/env python3
"""
OpenAI Client Memory Integration Example

This example demonstrates different memory storage options
and how to persist conversations across sessions.
"""

import asyncio
import logging
import sys
import os
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.openai_client import OpenAiClient

# Configure logging
logging.basicConfig(level=logging.INFO)

async def memory_integration_example():
    """Demonstrate different memory integration options"""
    
    # Configuration for OpenAI client
    config = {
        "LLM_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"),
        "LLM_MODEL": "gpt-4o-mini",
        "max_tokens": 1200,
        "system_prompt": "You are a financial research assistant. Remember previous conversations and build upon them.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
            }
        }
    }
    
    # Create temporary directory for file storage
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Using temporary storage directory: {temp_dir}")
    
    try:
        print("🧠 OpenAI Client Memory Integration Example")
        print("=" * 50)
        
        # Example 1: In-Memory Storage (default)
        print("\n1️⃣ In-Memory Storage Example:")
        client_memory = OpenAiClient.with_in_memory_store(config, user_id="user_123")
        await client_memory.initialize()
        
        # Start a conversation
        response1 = await client_memory.ask_question(
            "I'm researching renewable energy stocks. Can you help me identify the top 3 companies?",
            maintain_history=True
        )
        print(f"👤 User: I'm researching renewable energy stocks. Can you help me identify the top 3 companies?")
        print(f"🤖 Assistant: {response1[:200]}...")
        
        # Follow up
        response2 = await client_memory.ask_question(
            "What are the financial metrics I should look at for these companies?",
            maintain_history=True
        )
        print(f"👤 User: What are the financial metrics I should look at for these companies?")
        print(f"🤖 Assistant: {response2[:200]}...")
        
        print(f"📊 In-memory conversation has {len(client_memory.messages)} messages")
        await client_memory.cleanup()
        
        # Example 2: File-Based Persistent Storage
        print("\n2️⃣ File-Based Persistent Storage Example:")
        client_file = OpenAiClient.with_file_memory_store(
            config, 
            storage_path=temp_dir,
            user_id="user_123",
            memory_session_id="research_session_001"
        )
        await client_file.initialize()
        
        # Continue the conversation (will be saved to file)
        response3 = await client_file.ask_question(
            "Based on our previous discussion about renewable energy stocks, which one would you recommend for a 5-year investment?",
            maintain_history=True,
            load_from_memory=True  # Try to load previous conversation
        )
        print(f"👤 User: Based on our previous discussion about renewable energy stocks, which one would you recommend for a 5-year investment?")
        print(f"🤖 Assistant: {response3[:200]}...")
        
        # Add more to the conversation
        response4 = await client_file.ask_question(
            "What would be a good entry point for this investment?",
            maintain_history=True
        )
        print(f"👤 User: What would be a good entry point for this investment?")
        print(f"🤖 Assistant: {response4[:200]}...")
        
        print(f"📊 File-based conversation has {len(client_file.messages)} messages")
        await client_file.cleanup()
        
        # Example 3: Load Previous Session
        print("\n3️⃣ Loading Previous Session Example:")
        client_reload = OpenAiClient.with_file_memory_store(
            config,
            storage_path=temp_dir,
            user_id="user_123",
            memory_session_id="research_session_001"  # Same session ID
        )
        await client_reload.initialize()
        
        # This should load the previous conversation
        response5 = await client_reload.ask_question(
            "Can you summarize our entire conversation about renewable energy investments?",
            maintain_history=True,
            load_from_memory=True
        )
        print(f"👤 User: Can you summarize our entire conversation about renewable energy investments?")
        print(f"🤖 Assistant: {response5[:300]}...")
        
        print(f"📊 Reloaded conversation has {len(client_reload.messages)} messages")
        await client_reload.cleanup()
        
        # Example 4: Stateless Mode (No Memory)
        print("\n4️⃣ Stateless Mode (No Memory) Example:")
        client_stateless = OpenAiClient.without_memory(config)
        await client_stateless.initialize()
        
        # Each question is independent
        response6 = await client_stateless.ask_single_question(
            "What's the difference between growth and value investing?"
        )
        print(f"👤 User: What's the difference between growth and value investing?")
        print(f"🤖 Assistant: {response6[:200]}...")
        
        response7 = await client_stateless.ask_single_question(
            "Which approach did we discuss earlier?"  # This won't have context
        )
        print(f"👤 User: Which approach did we discuss earlier?")
        print(f"🤖 Assistant: {response7[:200]}...")
        
        await client_stateless.cleanup()
        
        print("\n✅ Memory integration examples completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"🧹 Cleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    asyncio.run(memory_integration_example())
