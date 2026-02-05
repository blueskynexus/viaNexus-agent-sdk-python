"""
FastAPI app demonstrating streaming responses via Server-Sent Events (SSE).

Run with:
    uvicorn examples.clients.anthropic.streaming_fastapi_sse:app --reload
"""
import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient

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
    session_id = await client.establish_persistent_connection()
    print(f"Service ready with persistent MCP session: {session_id}")

    yield

    # Shutdown
    if client:
        await client.cleanup()


app = FastAPI(lifespan=lifespan)


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask(request: AskRequest):
    """Non-streaming endpoint for comparison."""
    try:
        response = await client.ask_with_persistent_session(request.question)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}


@app.post("/ask/stream")
async def ask_stream(request: AskRequest):
    """
    Streaming endpoint that returns an SSE stream.

    Events:
        event: delta  — {"text": "chunk"}   (incremental token)
        event: done   — {}                  (stream finished)
    """
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    # on_delta must be a sync callable (Callable[[str], None])
    # Use queue.put_nowait since we're already on the event loop
    def on_delta(chunk: str):
        queue.put_nowait(chunk)

    async def run_query():
        try:
            await client.ask_with_persistent_session(
                request.question,
                on_delta=on_delta
            )
        except Exception as e:
            queue.put_nowait(f"__error__:{e}")
        finally:
            queue.put_nowait(None)  # sentinel

    asyncio.create_task(run_query())

    async def event_generator():
        while True:
            chunk = await queue.get()
            if chunk is None:
                yield f"event: done\ndata: {{}}\n\n"
                break
            if isinstance(chunk, str) and chunk.startswith("__error__:"):
                error_msg = chunk[len("__error__:"):]
                yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"
                break
            yield f"event: delta\ndata: {json.dumps({'text': chunk})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
