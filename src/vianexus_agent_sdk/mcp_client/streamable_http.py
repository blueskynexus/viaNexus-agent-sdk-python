from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from mcp.client.streamable_http import streamablehttp_client
from vianexus_agent_sdk.providers.oauth import (
    ViaNexusOAuthClientProvider,
    ViaNexusOAuthProvider,
)
from vianexus_agent_sdk.types.config import BaseConfig


def _normalize_server(server: str) -> str:
    # Ensure a scheme for URL composition
    if server.startswith("http://") or server.startswith("https://"):
        return server.rstrip("/")
    return f"https://{server.rstrip('/')}"


@dataclass
class StreamableHttpSetup:
    """
    Handles OAuth setup and yields a transport context for the MCP server.
    """

    server_url: str
    server_port: int
    software_statement: str
    auth_layer: Optional[ViaNexusOAuthClientProvider] = None
    client_context: Optional[Dict[str, Any]] = None

    @classmethod
    def from_config(cls, config, client_context: Optional[Dict[str, Any]] = None) -> "StreamableHttpSetup":
        # Defensive lookups. Fail early with KeyError if missing.
        return cls(
            server_url=_normalize_server(config["server_url"]),
            server_port=int(config["server_port"]),
            software_statement=config["software_statement"],
            client_context=client_context,
        )

    async def create_auth_layer(self) -> ViaNexusOAuthClientProvider:
        """
        Initialize the OAuth client and start the local callback server.
        """
        provider = ViaNexusOAuthProvider(
            server_url=self.server_url,
            server_port=self.server_port,
            software_statement=self.software_statement,
        )
        self.auth_layer = await provider.initialize()
        return self.auth_layer

    def _get_tool_categories_header(self) -> Dict[str, str]:
        """
        Build X-Tool-Categories header based on client context.
        Returns headers dict with tool category filtering.
        """
        headers = {}

        # Default to "financial" category
        categories = ["financial"]

        # If client context indicates OpenBB, add openbb category
        if self.client_context and self.client_context.get("type") == "openbb":
            categories.append("openbb")

        headers["X-Tool-Categories"] = ",".join(categories)
        return headers

    def connection_context(self):
        """
        Return the streamable HTTP transport context manager.
        Requires `create_auth_layer()` to have succeeded.
        """
        if not self.auth_layer:
            raise RuntimeError("Auth not initialized. Call create_auth_layer() first.")
        url = f"{self.server_url}:{self.server_port}/mcp"

        # Include tool category headers based on client context
        headers = self._get_tool_categories_header()

        return streamablehttp_client(url=url, auth=self.auth_layer, headers=headers)
