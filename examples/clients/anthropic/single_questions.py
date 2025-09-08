import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def single_question_mode():
    """Use the client for single questions with string responses."""
    config = {
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
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
    client = AnthropicClient(config)
    
    try:
        # Setup connection
        if not await client.setup_connection():
            print("Failed to setup connection")
            return
            
        # Establish MCP session
        async with client.connection_manager.connection_context() as (readstream, writestream, get_session_id):
            client.readstream = readstream
            client.writestream = writestream
            
            if not await client.connect_to_server():
                print("Failed to connect to MCP server")
                return
                
            # Now you can ask single questions
            response = await client.ask_single_question("What is the current price of AAPL?")
            print(f"Response: {response}")
            
            response = await client.ask_single_question("Show me the 52-week high and low for TSLA")
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(single_question_mode())