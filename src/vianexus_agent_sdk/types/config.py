from typing import TypedDict, Optional

class BaseConfig(TypedDict):
    """Base configuration for all clients"""
    server_url: str
    server_port: int
    software_statement: str

class AnthropicConfig(BaseConfig):
    """Configuration specific to Anthropic client"""
    llm_api_key: str
    llm_model: Optional[str] = "claude-3-5-sonnet-20241022"
    max_tokens: Optional[int] = 1000
