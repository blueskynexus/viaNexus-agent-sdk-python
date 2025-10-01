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

class OpenAiConfig(BaseConfig):
    """Configuration specific to OpenAI client"""
    llm_api_key: str
    llm_model: Optional[str] = "gpt-4o-mini"
    max_tokens: Optional[int] = 1000
    max_history_length: Optional[int] = 50
    system_prompt: Optional[str] = "You are a skilled Financial Analyst."
