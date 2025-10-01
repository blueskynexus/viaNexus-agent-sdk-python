import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def interactive_mode():
    """Run the client in interactive REPL mode."""
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
    
    try:
        client = AnthropicClient(config)
        await client.run()  # Starts interactive chat loop
    except Exception as e:
        print(f"Connection setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_mode())