import asyncio
import json
import logging
from openai import AsyncOpenAI
from typing import Any, Dict, List
from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient

class OpenAiClient(EnhancedMCPClient):
    def __init__(self, config):
        super().__init__(config)
        self.openai = AsyncOpenAI(api_key=config.get("llm_api_key"))
        self.model = config.get("llm_model", "gpt-4o-mini")
        self.max_tokens = int(config.get("max_tokens", 1000))

    @staticmethod
    def _map_tool(t):
        schema = getattr(t, "inputSchema", None)
        if not isinstance(schema, dict) or schema.get("type") != "object":
            schema = {"type": "object", "properties": {}}

        return {
            "type": "function",
            "function": {
                "name": t.name,
                "description": (t.description or "").strip(),
                "parameters": schema,  # leave as-is; not strict
            },
        }

    async def _list_tools_for_openai(self):
        try:
            tl = await self.session.list_tools()
            return [self._map_tool(t) for t in (tl.tools or [])]
        except Exception as e:
            logging.warning("list_tools failed: %s", e)
            return []

    async def _stream_assistant(self, messages, tools, timeout=60):
        text_out = []
        # index -> {"id": str|None, "name": str|None, "arguments": str}
        pending = {}

        stream = await self.openai.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
            stream=True,
            max_tokens=self.max_tokens,
            timeout=timeout,
            tool_choice="auto",
        )

        async for chunk in stream:
            c = chunk.choices[0]
            d = getattr(c, "delta", None)
            if not d:
                continue

            # Stream text
            if getattr(d, "content", None):
                print(d.content, end="", flush=True)
                text_out.append(d.content)

            # Merge tool_call deltas by index
            if getattr(d, "tool_calls", None):
                for tc in d.tool_calls:
                    idx = getattr(tc, "index", None)
                    if idx is None:
                        continue  # ignore until index arrives
                    slot = pending.setdefault(idx, {"id": None, "name": None, "arguments": ""})

                    if getattr(tc, "id", None):
                        slot["id"] = tc.id

                    fn = getattr(tc, "function", None)
                    if fn:
                        if getattr(fn, "name", None):
                            slot["name"] = fn.name
                        if getattr(fn, "arguments", None):
                            slot["arguments"] += fn.arguments

        # Finalize tool_calls: only keep complete ones
        complete_calls = []
        for idx in sorted(pending.keys()):
            call = pending[idx]
            if call["id"] and call["name"]:
                complete_calls.append({
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": call["arguments"] or "{}",
                    },
                })

        assistant_msg = {"role": "assistant", "content": "".join(text_out)}
        if complete_calls:
            assistant_msg["tool_calls"] = complete_calls
            # Return tool_calls keyed by id for execution
            tool_calls_by_id = {c["id"]: c for c in complete_calls}
            return assistant_msg["content"], tool_calls_by_id, assistant_msg
        
        return assistant_msg["content"], {}, assistant_msg

 
    async def _exec_tool(self, call):
        name = call["function"]["name"]
        arg_str = call["function"]["arguments"] or "{}"
        try:
            args = json.loads(arg_str) if arg_str.strip() else {}
        except json.JSONDecodeError:
            args = {"_raw": arg_str}

        try:
            result = await self.session.call_tool(name, args)
            payload = getattr(result, "content", result)
            if not isinstance(payload, str):
                text = [item.text for item in payload]
                payload = "\n".join(text) + "\n"

        except Exception as e:
            logging.error("Tool %s failed: %s", name, e)
            payload = f"Error calling tool '{name}': {e}"

        return {
            "role": "tool",
            "tool_call_id": call["id"],
            "name": name,
            "content": str(payload)[:100_000],
        }

    async def process_query(self, query: str) -> str:
        if not self.session:
            return "Error: MCP session not initialized."

        tools = await self._list_tools_for_openai()
        messages: List[Dict[str, Any]] = [{"role": "user", "content": query}]
        printed_any = False

        for _ in range(6):  # safety cap on tool iterations
            text, tool_calls, assistant_msg = await self._stream_assistant(messages, tools)
            messages.append(assistant_msg)

            if not tool_calls:
                if text:
                    printed_any = True
                return "" if printed_any else text

            tool_results_msgs = await asyncio.gather(
                *(self._exec_tool(call) for call in tool_calls.values())
            )
            messages.extend(tool_results_msgs)

        return "Error: tool-call loop exceeded max iterations."
