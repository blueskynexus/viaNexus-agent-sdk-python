"""Streaming tool loop + prompt-cache breakpoints for AnthropicClient.

Run: uv run python tests/test_anthropic_streaming.py
"""

import asyncio
from types import SimpleNamespace

from anthropic.types import TextBlock, ToolUseBlock

from vianexus_agent_sdk.clients.anthropic_client import REFUSAL_MESSAGE, AnthropicClient

CACHE = {"type": "ephemeral"}


def make_client(responses):
    """An AnthropicClient with no __init__ side effects: a fake MCP session and a fake
    messages.stream that replays `responses` (one list of content blocks per call)."""
    client = AnthropicClient.__new__(AnthropicClient)
    client.model, client.max_tokens, client.system_prompt, client.effort = "m", 4096, "sys", None
    client.messages, client._tools_cache, client._last_response = [], None, ""
    client._last_artifacts, client.max_history_length = [], 50
    client.requests = []

    tool = SimpleNamespace(name="search", description="d", inputSchema={"type": "object"})

    async def call_tool(name, args):
        return SimpleNamespace(content=[SimpleNamespace(text="result")])

    async def list_tools():
        client.list_calls = getattr(client, "list_calls", 0) + 1
        return SimpleNamespace(tools=[tool])

    client.session = SimpleNamespace(list_tools=list_tools, call_tool=call_tool)

    class Stream:
        def __init__(self, blocks):
            self.blocks = blocks

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def __aiter__(self):
            for b in self.blocks:
                if b.type == "text":
                    yield SimpleNamespace(type="content_block_delta", delta=SimpleNamespace(type="text_delta", text=b.text))

        async def get_final_message(self):
            return SimpleNamespace(content=self.blocks)

    def stream(**kwargs):
        client.requests.append(kwargs)
        return Stream(responses.pop(0))

    client.anthropic = SimpleNamespace(messages=SimpleNamespace(stream=stream))
    return client


def test_build_request_marks_tools_system_and_tail_without_mutating_history():
    client = make_client([])
    client.messages = [{"role": "user", "content": "hi"}]
    req = client._build_request([{"name": "a"}, {"name": "b"}])

    assert req["tools"] == [{"name": "a"}, {"name": "b", "cache_control": CACHE}]
    assert req["system"] == [{"type": "text", "text": "sys", "cache_control": CACHE}]
    assert req["messages"][-1]["content"] == [{"type": "text", "text": "hi", "cache_control": CACHE}]
    assert client.messages == [{"role": "user", "content": "hi"}]


def test_stream_runs_the_tool_loop_and_yields_every_delta():
    client = make_client([
        [TextBlock(type="text", text="Looking. "),
         ToolUseBlock(type="tool_use", id="t1", name="search", input={"q": ""})],
        [TextBlock(type="text", text="Done.")],
    ])

    async def run():
        return [d async for d in client.ask_question_stream("datasets?")]

    assert asyncio.run(run()) == ["Looking. ", "Done."]
    assert client._last_response == "Looking. Done."
    assert [m["role"] for m in client.messages] == ["user", "assistant", "user", "assistant"]
    # Second iteration's cache breakpoint sits on the tool_result, the conversation tail.
    assert client.requests[1]["messages"][-1]["content"][-1]["cache_control"] == CACHE
    # Tools listed once, then served from the cache.
    asyncio.run(client._get_available_tools())
    assert client.list_calls == 1


def test_effort_thinking_and_refusal():
    from anthropic.types import ThinkingBlock

    thinking = ThinkingBlock(type="thinking", thinking="", signature="sig")
    client = make_client([
        [thinking, ToolUseBlock(type="tool_use", id="t1", name="search", input={})],
        [],
    ])
    client.effort = "low"
    saved = []

    async def save(role, content, *a):
        saved.append(content)

    client.memory_save_message = save
    stream = client.anthropic.messages.stream

    def refusing(**kw):  # second call: a decline with no content
        s = stream(**kw)
        if len(client.requests) == 2:
            s.get_final_message = lambda: asyncio.sleep(0, SimpleNamespace(content=[], stop_reason="refusal"))
        return s

    client.anthropic.messages.stream = refusing

    async def run():
        return [d async for d in client.ask_question_stream("q", use_memory=True, load_from_memory=False)]

    assert asyncio.run(run()) == [REFUSAL_MESSAGE]
    assert client.requests[0]["extra_body"] == {"output_config": {"effort": "low"}}
    # Thinking replays to the API unchanged, but stays out of memory.
    assert client.messages[1]["content"][0] is thinking
    assert all(getattr(b, "type", None) != "thinking" for b in saved[1])
    assert client.messages[-1]["content"] == [{"type": "text", "text": REFUSAL_MESSAGE}]


def test_truncation_is_logged():
    import logging
    client = make_client([[TextBlock(type="text", text="cut")]])
    stream = client.anthropic.messages.stream

    def truncated(**kw):
        s = stream(**kw)
        s.get_final_message = lambda: asyncio.sleep(0, SimpleNamespace(content=s.blocks, stop_reason="max_tokens"))
        return s

    client.anthropic.messages.stream = truncated
    records = []
    handler = logging.Handler()
    handler.emit = records.append
    logging.getLogger().addHandler(handler)
    try:
        asyncio.run(client.ask_question("hi", maintain_history=True))
    finally:
        logging.getLogger().removeHandler(handler)
    assert any("max_tokens (4096)" in r.getMessage() for r in records), records


def test_ask_question_returns_the_streamed_text():
    client = make_client([[TextBlock(type="text", text=" hello ")]])
    assert asyncio.run(client.ask_question("hi", maintain_history=True)) == "hello"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
