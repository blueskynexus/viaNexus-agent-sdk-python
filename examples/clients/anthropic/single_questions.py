import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def single_question_mode():
    """Use the client for single questions with string responses."""
    config = {
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        # Optional: customize the system prompt 
        # Priority: config > JWT software_statement > default financial analyst
        # "system_prompt": "You are a helpful assistant specializing in financial analysis.",
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
        # Setup connection using inheritance model
        if not await client.setup_connection():
            print("Failed to setup connection")
            return
        
        # Now you can ask single questions directly
        response = await client.ask_single_question("What is the current price of AAPL?")
        print(f"Response: {response}")
        
        response = await client.ask_single_question("Show me the 52-week high and low for TSLA")
        print(f"Response: {response}")
        
        # Demonstrate conversation with history
        print("\n=== Conversational Questions ===")
        response = await client.ask_question("What is Microsoft's current stock price?", maintain_history=True)
        print(f"Q: What is Microsoft's current stock price?")
        print(f"A: {response}\n")
        
        response = await client.ask_question("How does that compare to last month?", maintain_history=True)
        print(f"Q: How does that compare to last month? (uses context)")
        print(f"A: {response}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(single_question_mode())