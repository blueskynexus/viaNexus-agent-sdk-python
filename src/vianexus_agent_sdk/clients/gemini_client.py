import google.generativeai as genai
import logging
import json
from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient

class GeminiClient(EnhancedMCPClient):
    def __init__(self, config):
        super().__init__(config)
        genai.configure(api_key=config.get("llm_api_key"))
        self.model = genai.GenerativeModel(config.get("llm_model", "gemini-2.0-flash"))
        self.max_tokens = config.get("max_tokens", 1000)
        self.messages = []
        self.max_history_length = config.get("max_history_length", 50)

    async def process_query(self, query: str) -> str:
        if not self.session:
            return "Error: MCP session not initialized."

        try:
            tool_list = await self.session.list_tools()
            tools = []
            for t in (tool_list.tools or []):
                # Convert MCP schema to Gemini-compatible schema
                input_schema = getattr(t, "inputSchema", {}) or {}
                gemini_schema = self._convert_schema_for_gemini(input_schema)
                
                tools.append({
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": gemini_schema,
                })
        except Exception as e:
            logging.error("Error listing tools: %s", e)
            tools = []

        self.messages.append({"role": "user", "content": query})

        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_to_gemini_format(self.messages)
            
            # Generate response from Gemini
            response = await self.model.generate_content_async(
                gemini_messages,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                ),
                tools=tools if tools else None
            )

            # Handle tool calls if present
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    
                    # Check for tool calls
                    tool_calls = []
                    for part in content.parts:
                        if hasattr(part, 'function_call'):
                            tool_calls.append(part.function_call)
                    
                    if tool_calls:
                        result_blocks = []
                        for tool_call in tool_calls:
                            name = tool_call.name
                            args = tool_call.args if hasattr(tool_call, 'args') else {}
                            try:
                                result = await self.session.call_tool(name, args)
                                payload = result.content
                                if isinstance(payload, (dict, list)):
                                    text_payload = payload[0].text
                                else:
                                    text_payload = str(payload)
                                result_blocks.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.name,  # Gemini doesn't have tool_use_id like Anthropic
                                    "content": [{"type": "text", "text": text_payload}],
                                })
                            except Exception as e:
                                logging.error("Tool '%s' failed: %s", name, e)
                                result_blocks.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.name,
                                    "content": [{"type": "text", "text": f"Error: {e}"}],
                                })
                        
                        # Add tool results to conversation
                        self.messages.append({"role": "assistant", "content": response.text})
                        self.messages.append({"role": "user", "content": result_blocks})
                        
                        # Continue conversation with tool results
                        return await self.process_query("Please continue with the tool results.")
                    else:
                        # No tool calls, just add response to conversation
                        self.messages.append({"role": "assistant", "content": response.text})
                        print(response.text)
                        self._trim_history()
                        return ""
                else:
                    # Handle case where response doesn't have expected structure
                    response_text = str(response)
                    self.messages.append({"role": "assistant", "content": response_text})
                    print(response_text)
                    self._trim_history()
                    return ""
            else:
                # Handle case where response doesn't have candidates
                response_text = str(response)
                self.messages.append({"role": "assistant", "content": response_text})
                print(response_text)
                self._trim_history()
                return ""

        except Exception as e:
            logging.error("Error generating response from Gemini: %s", e)
            error_msg = f"Error: {e}"
            self.messages.append({"role": "assistant", "content": error_msg})
            return error_msg

    def _convert_to_gemini_format(self, messages):
        """Convert conversation messages to Gemini format"""
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
        return gemini_messages

    def _convert_schema_for_gemini(self, schema):
        """Convert MCP schema to Gemini-compatible schema by removing unsupported fields"""
        if not isinstance(schema, dict):
            return {}
        
        # Create a copy to avoid modifying the original
        gemini_schema = {}
        
        # Copy supported fields
        for key, value in schema.items():
            if key in ['type', 'description', 'required', 'properties', 'items']:
                if key == 'properties' and isinstance(value, dict):
                    # Recursively convert nested properties
                    gemini_schema[key] = {
                        prop_name: self._convert_schema_for_gemini(prop_schema)
                        for prop_name, prop_schema in value.items()
                    }
                elif key == 'items' and isinstance(value, dict):
                    # Recursively convert array items schema
                    gemini_schema[key] = self._convert_schema_for_gemini(value)
                else:
                    gemini_schema[key] = value
        
        return gemini_schema

    def _trim_history(self):
        """Keep conversation history within reasonable bounds"""
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length:]
