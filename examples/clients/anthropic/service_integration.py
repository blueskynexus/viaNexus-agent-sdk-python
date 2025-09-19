from fastapi import FastAPI
from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient
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
    
    client = PersistentAnthropicClient(config)
    # Establish persistent MCP connection that stays open for the service lifetime
    session_id = await client.establish_persistent_connection()
    print(f"Service ready with persistent MCP session: {session_id}")
    
    yield
    
    # Shutdown
    if client:
        await client.cleanup()

app = FastAPI(lifespan=lifespan)

@app.post("/ask")
async def ask_question(question: str):
    """API endpoint to ask financial questions."""
    try:
        # Use the persistent connection established at startup
        response = await client.ask_with_persistent_session(question)
        return {"response": response}
        
    except Exception as e:
        return {"error": str(e)}