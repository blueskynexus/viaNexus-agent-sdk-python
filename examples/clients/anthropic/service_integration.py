from fastapi import FastAPI
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient
import asyncio
from contextlib import asynccontextmanager

client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client
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
    await client.setup_connection()
    
    yield
    
    # Shutdown
    if client:
        await client.cleanup()

app = FastAPI(lifespan=lifespan)

@app.post("/ask")
async def ask_question(question: str):
    """API endpoint to ask financial questions."""
    try:
        async with client.connection_manager.connection_context() as (readstream, writestream, get_session_id):
            client.readstream = readstream
            client.writestream = writestream
            
            if not await client.connect_to_server():
                return {"error": "Failed to connect to MCP server"}
                
            response = await client.ask_single_question(question)
            return {"response": response}
            
    except Exception as e:
        return {"error": str(e)}