from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession


class BaseMCPClient(ABC):
    """
    Base client for MCP connections and an interactive chat loop.
    Subclasses implement `process_query`.
    """

    def __init__(self, readstream: Any, writestream: Any) -> None:
        self.session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()
        self.readstream = readstream
        self.writestream = writestream

    @property
    def is_connected(self) -> bool:
        return self.session is not None

    async def _ainput(self, prompt: str) -> str:
        # Non-blocking input so the loop plays nicely with asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: input(prompt))

    async def connect_to_server(self) -> bool:
        """
        Connect and initialize the MCP session. Logs tool names on success.
        """
        try:
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(self.readstream, self.writestream)
            )
            await self.session.initialize()

            # Optional: list available tools for visibility
            try:
                response = await self.session.list_tools()
                tools = getattr(response, "tools", []) or []
                logging.debug("Connected. Tools: %s", [t.name for t in tools])
            except Exception as tool_err:
                logging.debug("Tool discovery failed: %s", tool_err)

            return True
        except Exception as e:
            logging.error("Failed to connect to MCP server: %s", e)
            return False

    async def chat_loop(self) -> None:
        """
        Simple REPL loop. Type 'quit' to exit.
        """
        print("\nMCP Client Started")
        print("Type your queries or 'quit' to exit.")
        print("=" * 50)

        while True:
            try:
                query = (await self._ainput("\nQuery: ")).strip()
                if query.lower() == "quit":
                    print("\nGoodbye!")
                    break
                if not query:
                    print("Please enter a query.")
                    continue

                print("\nProcessing...")
                response = await self.process_query(query)
                if (response != "" and response is not None):
                    print("\n" + "=" * 50)
                    print("Response:")
                    print(response)
                print("\n" + "=" * 50)
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                logging.error("Chat loop error: %s", e)

    @abstractmethod
    async def process_query(self, query: str) -> str:
        """Implement model/tool-specific query handling."""
        raise NotImplementedError

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
