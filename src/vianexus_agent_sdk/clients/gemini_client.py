import google.generativeai as genai
import logging
import json
from vianexus_agent_sdk.mcp_client.enhanced_mcp_client import EnhancedMCPClient

class GeminiClient(EnhancedMCPClient):
    """
    A refactored client for interacting with the Gemini API, featuring robust
    handling of tool calls and conversation history.
    """
    def __init__(self, config):
        super().__init__(config)
        genai.configure(api_key=config.get("llm_api_key"))
        self.model = genai.GenerativeModel(config.get("llm_model", "gemini-2.0-flash"))
        self.max_tokens = config.get("max_tokens", 1000)
        self.messages = []
        self.max_history_length = config.get("max_history_length", 50)

    async def process_query(self, query: str) -> str:
        """
        Processes a user query, interacts with the Gemini model, and handles
        any necessary tool calls in a stateful loop.
        """
        if not self.session:
            return "Error: MCP session not initialized."

        # Append the new user query to the conversation history in the correct format
        self.messages.append({"role": "user", "parts": [{"text": query}]})

        try:
            tools = [{
                "function_declarations": [
                    {
                        "name": "search",
                        "description": (
                            "Search for datasets from viaNexus financial data API."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "query": {
                                    "type": "STRING",
                                    "description": "Dataset name. Empty for all."
                                }
                            }
                        }
                    },
                    {
                        "name": "fetch",
                        "description": (
                            "Retrieve a dataset by endpoint, product, dataset name, and symbol."
                        ),
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "endpoint": {"type": "STRING"},
                                "product": {"type": "STRING"},
                                "dataset_name": {"type": "STRING"},
                                "symbols": {"type": "STRING"},
                                "subkey": {"type": "STRING"},
                                "last": {"type": "NUMBER"},
                                "region": {"type": "STRING"},
                                "on_date": {"type": "STRING"},
                                "from_date": {"type": "STRING"},
                                "to_date": {"type": "STRING"},
                                "filter": {"type": "STRING"}
                            },
                            "required": ["endpoint", "product", "dataset_name"]
                        }
                    },
                    {
                        "name": "current_date",
                        "description": "Provides the current date.",
                        "parameters": { "type": "OBJECT" }
                    }
                ]
            }]
        except Exception as e:
            logging.error("Error listing tools: %s", e)
            tools = []

        # --- Stateful Tool-Calling Loop ---
        # The loop continues until the model returns a text response instead of a tool call.
        while True:
            try:
                pass
            except Exception as e:
                print(e)
                logging.error(f"Error generating response from Gemini: {e}")
                error_msg = f"An error occurred while processing your request: {e}"
                self.messages.append({"role": "model", "parts": [{"text": error_msg}]})
                return error_msg

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