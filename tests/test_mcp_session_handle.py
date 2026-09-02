"""A stateless MCP server issues no Mcp-Session-Id; the clients must not require one.

Requiring it made every persistent client unusable against a stateless server: the
initialize response carries no header, so get_session_id() returns None and
establish_persistent_connection used to raise "Failed to get MCP session ID". The
2026-07-28 spec revision retires the header outright, so this is permanent.

Run: uv run python tests/test_mcp_session_handle.py
"""

import inspect
from types import SimpleNamespace

from vianexus_agent_sdk.clients.base_llm_client import BasePersistentLLMClient

resolve = BasePersistentLLMClient._resolve_mcp_session_id


def test_prefers_the_server_id_when_one_is_issued():
    """Stateful servers must behave exactly as before."""
    assert resolve(SimpleNamespace(), lambda: "server-abc") == "server-abc"


def test_mints_a_handle_when_the_server_issues_none():
    client = SimpleNamespace()
    assert resolve(client, lambda: None).startswith("local-")


def test_mints_a_handle_when_there_is_no_getter_at_all():
    assert resolve(SimpleNamespace(), None).startswith("local-")


def test_the_local_handle_is_stable_across_reconnects():
    """The id is a conversation key, so re-establishing must not change it.

    A server-issued id does change on reconnect, which is why a caller's stored id
    could stop matching after the server restarted.
    """
    client = SimpleNamespace()
    assert resolve(client, lambda: None) == resolve(client, lambda: None)


def test_no_client_requires_a_server_issued_session_id():
    """Guard the regression in all three clients, not just the one we test through."""
    from vianexus_agent_sdk.clients import anthropic_client, gemini_client, openai_client

    for module in (anthropic_client, openai_client, gemini_client):
        source = inspect.getsource(module)
        assert "Failed to get MCP session ID" not in source, (
            f"{module.__name__} requires a server-issued session id again; "
            "it cannot talk to a stateless MCP server"
        )


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nall checks passed")
