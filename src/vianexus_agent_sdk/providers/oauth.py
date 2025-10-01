import asyncio
from typing import Any
import requests
import socket
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from vianexus_agent_sdk.servers.callback.callback_server import CallbackServer
from mcp import ClientSession
from urllib.parse import urljoin
import httpx

class ViaNexusOAuthClientProvider(OAuthClientProvider):
    """Manages Agent server connections and tool execution."""
    def __init__(self, server_url, client_metadata, storage, redirect_handler, callback_handler, software_statement) -> None:
        super().__init__(server_url, client_metadata, storage, redirect_handler, callback_handler)
        self.software_statement = software_statement

    async def _register_client(self):
        """Build registration request with software statement."""
        if self.context.client_info:
            return None

        if self.context.oauth_metadata and self.context.oauth_metadata.registration_endpoint:
            registration_url = str(self.context.oauth_metadata.registration_endpoint)
        else:
            auth_base_url = self.context.get_authorization_base_url(self.context.server_url)
            registration_url = urljoin(auth_base_url, "/register")

        registration_data = self.context.client_metadata.model_dump(by_alias=True, mode="json", exclude_none=True)
        # Add software statement
        registration_data["software_statement"] = self.software_statement

        return httpx.Request(
            "POST", registration_url, json=registration_data, headers={"Content-Type": "application/json"}
        )

def find_free_port(start_port=3030, max_attempts=100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")

class ViaNexusOAuthProvider:
    """Manages MCP server connections and tool execution."""

    def __init__(self, server_url: str, server_port: str, software_statement: str) -> None:
        self.name: str = "ViaNexus_OAuthProvider"
        self.server_url: str = server_url
        self.server_port: str = server_port if server_port else "443"
        self.software_statement: str = software_statement
        self.callback_server: CallbackServer | None = None

    async def initialize(self) -> ViaNexusOAuthClientProvider:
        """Initialize the server connection."""
        try:
            # Find a free port for the callback server
            callback_port = find_free_port()
            self.callback_server = CallbackServer(port=callback_port)
            self.callback_server.start()

            async def callback_handler() -> tuple[str, str | None]:
                """Wait for OAuth callback and return auth code and state."""
                try:
                    auth_code = self.callback_server.wait_for_callback(timeout=300)
                    return auth_code, self.callback_server.get_state()
                except Exception as e:
                    raise e

            client_metadata_dict = {
                "client_name": "ViaNexus Auth Client",
                "redirect_uris": [f"http://localhost:{callback_port}/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "client_secret_post",
            }

            async def _default_redirect_handler(authorization_url: str) -> None:
                """Default redirect handler that opens the URL in a browser."""
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, requests.get, authorization_url)
                try:
                    response.raise_for_status()
                except Exception as e:
                    raise e

            oauth_provider = ViaNexusOAuthClientProvider(
                server_url=f"{self.server_url}:{self.server_port}",
                client_metadata=OAuthClientMetadata.model_validate(
                    client_metadata_dict
                ),
                storage=InMemoryTokenStorage(),
                redirect_handler=_default_redirect_handler,
                callback_handler=callback_handler,
                software_statement=self.software_statement
            )
        except Exception as e:
            # Clean up callback server if initialization fails
            if self.callback_server:
                self.callback_server.stop()
                self.callback_server = None
            raise e

        return oauth_provider

    def cleanup(self):
        """Clean up the callback server."""
        if self.callback_server:
            self.callback_server.stop()
            self.callback_server = None

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


class InMemoryTokenStorage(TokenStorage):
    """Simple in-memory token storage implementation."""

    def __init__(self):
        self._tokens: OAuthToken | None = None
        self._client_info: OAuthClientInformationFull | None = None

    async def get_tokens(self) -> OAuthToken | None:
        return self._tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._client_info = client_info