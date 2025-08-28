import logging
import base64
from google import genai
from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient

'''
The text property is not a top-level property of the response object itself;
it's a shortcut property provided for convenience.

The long way: response.candidates[0].content.parts[0].text

By default, the candidate_count is set to 1, so the candidates list will 
usually contain a single item. However, you can configure the API to generate
multiple candidates for a single prompt, which can be useful for comparing 
different potential responses.
'''

class GeminiClient(EnhancedMCPClient):
    """
    A refactored client for interacting with the Gemini API, featuring robust
    handling of tool calls and conversation history.
    """
    def __init__(self, config):
        super().__init__(config)
        self.model = genai.Client()
        self.max_tokens = config.get("max_tokens", 1000)
        self.messages = []
        self.max_history_length = config.get("max_history_length", 50)
    
    async def get_tools(self):
        """
        TODO: fix me
        """
        formatted_tools = []
        tools = await self.session.list_tools()
        for tool in tools.tools:
            if tool.name == "search":
                t = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "default": ""
                            }
                        },
                        "required": ["query"]
                    }
                }
                formatted_tools.append(t)
            elif tool.name == "current_date":
                formatted_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                })
            else:
                formatted_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                })
        gemini_tools = genai.types.Tool(function_declarations=formatted_tools)
        return gemini_tools

    async def process_query(self, query: str) -> str:
        """
        Processes a user query, interacts with the Gemini model, and handles
        any necessary tool calls in a stateful loop.
        """
        if not self.session:
            return "Error: MCP session not initialized."

        gemini_tools = await self.get_tools()

        self.messages.append({"role": "user", "parts": [{"text": query}]})
        # --- Stateful Tool-Calling Loop ---
        # Append the new user query to the conversation history
        # The loop continues until the model returns a text response instead of a tool call.
        loop_count = 1
        while True:
            print(f"\n loop {loop_count}")
            response = await self.model.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=self.messages,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[gemini_tools]
                )
            )

            # Check for a text response first
            if response.text:
                print("text response detected")
                print(response.text)
                self.messages.append(genai.types.Content(role="model", parts=[{"text": response.text}]))
                break
    
            # Check if the response contains content, to prevent NoneType error
            if response.candidates and response.candidates[0].content:
                # Check if the model is calling a tool
                tool_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]
        
                if tool_calls:
                    # Add the model's tool-call response to the history
                    self.messages.append(response.candidates[0].content)

                    tool_results = []
                    for tool_call in tool_calls:
                        print("function call detected")
                        print(f"name: {tool_call.name} \n args: {tool_call.args}")

                        result = await self.session.call_tool(tool_call.name, tool_call.args)
                        if result.isError:
                            logging.error(f"Tool {tool_call.name} failed")
                            raise Exception(f"Tool {tool_call.name} failed")
                
                        tool_response_part = genai.types.Part.from_function_response(
                            name=tool_call.name,
                            response={"result": result.content[0].text}
                        )
                        tool_results.append(tool_response_part)

                    self.messages.append(genai.types.Content(role="user", parts=tool_results))
                    loop_count += 1
                else:
                    # Handle cases where there is content, but it's not a text or tool call (unlikely but good practice)
                    print("Warning: Unexpected content format.")
                    break
            else:
                # This is the key change: Handle the 'None' content case
                print(f"Warning: Model response has no content. Finish reason: {response.candidates[0].finish_reason}")
                print("Breaking loop.")
                break

    def _convert_schema_for_gemini(self, schema: dict) -> dict:
        """
        Recursively sanitizes an MCP tool schema to be compatible with Gemini's API
        by keeping only the supported fields.
        """
        if not isinstance(schema, dict):
            return {}
        
        # Supported fields in Gemini's function declaration schema
        supported_keys = {'type', 'description', 'required', 'properties', 'items'}
        gemini_schema = {}
        
        for key, value in schema.items():
            if key in supported_keys:
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
        """Keeps the conversation history from exceeding the maximum length."""
        if len(self.messages) > self.max_history_length:
            # Keep the last `max_history_length` messages
            self.messages = self.messages[-self.max_history_length:]