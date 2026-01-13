from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from vianexus_agent_sdk.types.config import BaseConfig

from .base_mcp_client import BaseMCPClient
from .streamable_http import StreamableHttpSetup


class EnhancedMCPClient(BaseMCPClient):
    """
    High-level client that owns auth + transport setup.
    Subclasses still implement `process_query`.
    """

    def __init__(
        self,
        config: BaseConfig,
        connection_manager: Optional[StreamableHttpSetup] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.config = config
        self.client_context = client_context
        self.connection_manager = (
            connection_manager or StreamableHttpSetup.from_config(config, client_context=client_context)
        )
        self.auth_layer = None
        super().__init__(readstream=None, writestream=None)

    async def setup_connection(self) -> bool:
        try:
            self.auth_layer = await self.connection_manager.create_auth_layer()
            return True
        except (ConnectionError, TimeoutError, OSError) as e:
            logging.error("Network error during connection setup: %s", e)
            return False
        except Exception as e:
            logging.error("Unexpected error during connection setup: %s", e)
            return False

    async def run(self) -> bool:
        if not await self.setup_connection():
            return False

        try:
            async with self.connection_manager.connection_context() as (
                readstream,
                writestream,
                get_session_id,
            ):
                logging.debug("HTTP transport established")
                self.readstream = readstream
                self.writestream = writestream

                if not await self.connect_to_server():
                    logging.error("Failed to initialize MCP session")
                    return False

                # Optional: log session id if available
                try:
                    sid = get_session_id() if get_session_id else None
                    if sid:
                        logging.debug("Session ID: %s", sid)
                except Exception as _:
                    pass

                await self.chat_loop()
        except (ConnectionError, TimeoutError, OSError) as e:
            logging.error("Network error during MCP connection: %s", e)
            return False
        except Exception as e:
            logging.error("Unexpected error during MCP connection: %s", e)
            return False

        return True

    async def cleanup(self) -> None:
        await super().cleanup()
