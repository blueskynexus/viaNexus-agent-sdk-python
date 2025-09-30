import asyncio
from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient

async def persistent_session_example():
    """
    Example showing how to use PersistentAnthropicClient for maintaining 
    long-running conversations with persistent MCP connections.
    """
    config = {
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "max_history_length": 20,  # Keep conversation history manageable
        "user_id": "your-user-id",
        "app_name": "your-app-name",
        "agentServers": {
            "viaNexus": {
                "server_url": "your-vianexus-server-url",
                "server_port": 443,
                "software_statement": "your-software-statement-jwt"
            }
        },
    }
    
    # Create persistent client
    client = PersistentAnthropicClient(config)
    
    try:
        # Establish persistent connection once
        session_id = await client.establish_persistent_connection()
        print(f"Established persistent session: {session_id}")
        
        # Now you can ask multiple questions using the same session
        # This maintains conversation context and keeps the MCP connection open
        
        print("\n=== Question 1 ===")
        response1 = await client.ask_with_persistent_session(
            "What is the current stock price of AAPL?"
        )
        print(f"Response: {response1}")
        
        print("\n=== Question 2 ===")
        response2 = await client.ask_with_persistent_session(
            "How does that compare to its 52-week high?"
        )
        print(f"Response: {response2}")
        
        print("\n=== Question 3 ===")
        response3 = await client.ask_with_persistent_session(
            "What about TSLA? Show me its current price and recent performance."
        )
        print(f"Response: {response3}")
        
        print("\n=== Question 4 ===")
        response4 = await client.ask_with_persistent_session(
            "Can you compare AAPL and TSLA's performance this quarter?"
        )
        print(f"Response: {response4}")
        
        # Check connection status
        print(f"\nConnection still active: {client.is_connected}")
        print(f"Session ID: {client.mcp_session_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        await client.cleanup()
        print("Session closed and resources cleaned up")

async def service_integration_example():
    """
    Example showing how to integrate PersistentAnthropicClient into a service
    that needs to handle multiple requests efficiently.
    """
    config = {
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "max_history_length": 50,
        "user_id": "service-user",
        "app_name": "financial-service",
        "agentServers": {
            "viaNexus": {
                "server_url": "your-vianexus-server-url",
                "server_port": 443,
                "software_statement": "your-software-statement-jwt"
            }
        },
    }
    
    client = PersistentAnthropicClient(config)
    
    try:
        # Establish connection once at service startup
        await client.establish_persistent_connection()
        print("Service ready with persistent MCP connection")
        
        # Simulate multiple requests from different users/sessions
        user_questions = [
            "What's the current market cap of Microsoft?",
            "Show me Tesla's quarterly earnings trend",
            "Compare Apple and Google's revenue growth",
            "What are the top performing tech stocks today?",
        ]
        
        for i, question in enumerate(user_questions, 1):
            print(f"\n=== Processing Request {i} ===")
            print(f"Question: {question}")
            
            # Each request reuses the same persistent connection
            response = await client.ask_with_persistent_session(question)
            print(f"Response: {response[:200]}...")  # Truncate for demo
            
            # Connection remains active between requests
            assert client.is_connected, "Connection should remain active"
        
        print(f"\nProcessed {len(user_questions)} requests with single persistent connection")
        
    except Exception as e:
        print(f"Service error: {e}")
    finally:
        await client.cleanup()
        print("Service shutdown complete")

if __name__ == "__main__":
    print("=== Persistent Session Example ===")
    asyncio.run(persistent_session_example())
    
    print("\n" + "="*50)
    print("=== Service Integration Example ===")
    asyncio.run(service_integration_example())
