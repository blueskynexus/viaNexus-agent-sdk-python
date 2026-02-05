import asyncio
from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient

config = {
    "LLM_API_KEY": "your-anthropic-api-key",
    "LLM_MODEL": "claude-3-5-sonnet-20241022",
    "max_tokens": 1000,
    "max_history_length": 20,
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


async def basic_streaming_example():
    """
    Basic streaming with ask_question().
    The on_delta callback prints each text chunk as it arrives,
    giving the user a real-time typewriter effect.
    """
    client = PersistentAnthropicClient(config)

    try:
        await client.establish_persistent_connection()

        print("=== Basic Streaming ===")

        # on_delta is called with each text chunk as it arrives
        response = await client.ask_question(
            "What is the current stock price of AAPL?",
            on_delta=lambda chunk: print(chunk, end="", flush=True)
        )

        # A newline after streaming finishes
        print()
        # The full response is still returned as the function's return value
        print(f"\nFull response length: {len(response)} chars")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()


async def persistent_session_streaming_example():
    """
    Streaming with a persistent session for multi-turn conversations.
    Each call to ask_with_persistent_session streams tokens via on_delta
    while maintaining conversation history across turns.
    """
    client = PersistentAnthropicClient(config)

    try:
        session_id = await client.establish_persistent_connection()
        print(f"Session: {session_id}\n")

        questions = [
            "What is the current stock price of AAPL?",
            "How does that compare to its 52-week high?",
        ]

        for i, question in enumerate(questions, 1):
            print(f"=== Turn {i}: {question} ===")
            response = await client.ask_with_persistent_session(
                question,
                maintain_history=True,
                on_delta=lambda chunk: print(chunk, end="", flush=True)
            )
            print("\n")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()


async def collecting_chunks_example():
    """
    Collecting streamed chunks programmatically instead of printing them.
    Useful when you need to forward chunks to a WebSocket, write to a file,
    or do any custom processing with the incremental text.
    """
    client = PersistentAnthropicClient(config)
    chunks: list[str] = []

    try:
        await client.establish_persistent_connection()

        print("=== Collecting Chunks ===")

        response = await client.ask_question(
            "Give me a brief summary of Tesla's recent performance.",
            on_delta=lambda chunk: chunks.append(chunk)
        )

        print(f"Received {len(chunks)} chunks")
        print(f"Reconstructed response matches return value: {response == ''.join(chunks)}")
        print(f"First 3 chunks: {chunks[:3]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()


if __name__ == "__main__":
    print("=== Basic Streaming Example ===")
    asyncio.run(basic_streaming_example())

    print("\n" + "=" * 50)
    print("=== Persistent Session Streaming Example ===")
    asyncio.run(persistent_session_streaming_example())

    print("\n" + "=" * 50)
    print("=== Collecting Chunks Example ===")
    asyncio.run(collecting_chunks_example())
