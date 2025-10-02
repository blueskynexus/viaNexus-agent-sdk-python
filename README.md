# viaNexus AI Agent SDK for Python

The viaNexus AI Agent SDK for Python provides a convenient way to create a financial data agent with access to reliable financial data through viaNexus.
This SDK allows you to build a powerful financial Agent or digital employee/assitant that will have access to the viaNexus Data Platform financial dataset catalog.

## Installation

To install the SDK, you can use uv:

```bash
    uv add git+https://github.com/blueskynexus/viaNexus-agent-sdk-python --tag v0.2.0-pre
```
### Dependencies
- None required
- vianexus_agent_sdk will pull in all of the required dependencies.

## Usage
## LLM Support

Currently, the viaNexus AI Agent SDK for Python supports Google's Gemini, Anthropic Claude, and OpenAI GPT family of models. As the SDK matures, we plan to extend support to other Large Language Models (LLMs) to provide a wider range of options for your conversational AI applications.

## 🏭 Unified Client Factory

The SDK provides a **unified factory pattern** that automatically detects and creates the appropriate LLM client based on your configuration. This eliminates the need to manually choose between different client implementations.

### ✨ Key Features

- **🔍 Automatic Provider Detection**: Detects LLM provider from model names, API keys, or explicit configuration
- **🔄 Consistent Interface**: All clients implement the same interface regardless of provider
- **🧠 Universal Memory**: Seamless memory management across all providers
- **⚡ Easy Switching**: Change providers without code changes, just configuration
- **🛡️ Failover Support**: Built-in patterns for provider failover and redundancy

### 🚀 Quick Start with Factory

```python
import asyncio
from vianexus_agent_sdk.clients.llm_client_factory import LLMClientFactory

async def main():
    # Configuration - provider auto-detected from model name
    config = {
        "LLM_MODEL": "gpt-4o-mini",  # Auto-detects OpenAI
        "LLM_API_KEY": "sk-your-api-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client automatically
    client = LLMClientFactory.create_client(config)
    await client.initialize()
    
    # Use the client (same interface for all providers)
    response = await client.ask_question("What are the key financial metrics for evaluating a company?")
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

### 🎯 Provider Detection

The factory automatically detects providers using these patterns:

| Provider | Model Patterns | API Key Patterns |
|----------|----------------|------------------|
| **OpenAI** | `gpt-*`, `o1-*` | `sk-*` |
| **Anthropic** | `claude-*` | `sk-ant-*` |
| **Gemini** | `gemini-*` | Contains `AI` |

### 🔧 Factory Methods

```python
# Standard client with auto-detection
client = LLMClientFactory.create_client(config)
await client.initialize()

# Persistent client for long-running sessions
persistent_client = LLMClientFactory.create_persistent_client(config)
await persistent_client.initialize()

# Client with specific memory configuration
memory_client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="file",
    storage_path="./conversations"
)
await memory_client.initialize()

# Explicit provider (overrides auto-detection)
anthropic_client = LLMClientFactory.create_client(config, provider="anthropic")
await anthropic_client.initialize()

# Don't forget to cleanup when done
await client.cleanup()
await persistent_client.cleanup()
await memory_client.cleanup()
await anthropic_client.cleanup()
```

### 🧠 Memory Integration Options

```python
# 1. In-Memory Store (fast, session-only)
client = LLMClientFactory.create_client_with_memory(config, memory_type="in_memory", user_id="user_123")
await client.initialize()

# 2. File-Based Storage (persistent across restarts)
client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="file",
    storage_path="./conversations",
    user_id="user_123"
)
await client.initialize()

# 3. Stateless Mode (no memory, each query independent)
client = LLMClientFactory.create_client_with_memory(config, memory_type="none")
await client.initialize()

# Always cleanup when done
await client.cleanup()
```

### 🔄 Persistent Sessions

```python
async def portfolio_analysis_session():
    # Create persistent client (works with any provider)
    persistent_client = LLMClientFactory.create_persistent_client(config)
    await persistent_client.initialize()
    
    # Establish persistent connection
    session_id = await persistent_client.establish_persistent_connection()
    
    # Long-running conversation with maintained context
    response1 = await persistent_client.ask_with_persistent_session("Analyze AAPL's recent performance")
    response2 = await persistent_client.ask_with_persistent_session("Compare it with MSFT")
    response3 = await persistent_client.ask_with_persistent_session("What's your investment recommendation?")
    
    # Connection automatically maintained across calls
    print(f"Session: {session_id}")
    print(response1, response2, response3)
    
    # Cleanup
    await persistent_client.close_persistent_connection()
    await persistent_client.cleanup()
```

### 🛠️ Tool Integration & Real-Time Data

All clients automatically integrate with viaNexus MCP tools:

```python
# Create and initialize client
client = LLMClientFactory.create_client(config)
await client.initialize()

# Tools are automatically available - no additional setup needed
response = await client.ask_question(
    "Get me the latest earnings data for Tesla and analyze the key metrics"
)
# The client will automatically:
# 1. Use MCP tools to fetch Tesla's earnings data
# 2. Analyze the data using the selected LLM
# 3. Provide comprehensive insights

print(response)
await client.cleanup()
```

### 📚 Examples

Comprehensive examples are available in the `examples/unified_client/` directory:

- **`basic_factory_usage.py`** - Auto-detection and basic usage patterns
- **`config_based_selection.py`** - YAML configs and environment variables
- **`real_world_usage.py`** - Production-ready service patterns with error handling

Provider-specific examples are also available in `examples/clients/` for advanced use cases.

### OAuth
**Note:** OAuth is handled by the viaNexus_agent_sdk in the HTTP transport, you do not need to setup any authentication or authorization mechanisms

### Create a configuration file `config.yaml`

**Unified Configuration (Recommended)** - Works with factory pattern:
```yaml
development:
  # Provider auto-detected from model name
  LLM_API_KEY: "<LLM API Key>" # Supports GEMINI, Anthropic (Claude), and OpenAI (GPT) API keys
  LLM_MODEL: "<Model Name>" # Examples: gemini-2.5-flash, claude-3-5-sonnet-20241022, gpt-4o-mini
  LOG_LEVEL: "<LOGGING LEVEL>"
  max_tokens: 1000 # Optional: Maximum tokens for responses
  user_id: "<UUID for the Agent Session>"
  app_name: "viaNexus_Agent"
  
  # Optional: Explicit provider (overrides auto-detection)
  # provider: "openai"  # or "anthropic", "gemini"
  
  agentServers:
    viaNexus:
      server_url: "<viaNexus Agent Server HTTP URL>"
      server_port: <viaNexus Agent Port>
      software_statement: "<SOFTWARE STATEMENT>"
```

**Note:** Generate a software statement from the viaNexus api endpoint `v1/agents/register`

#### System Prompt Priority

All clients automatically determine the system prompt using this priority order:

1. **Config Parameter** `system_prompt` (highest priority)
2. **JWT Software Statement** `system_prompt` or `systemPrompt` field (automatic extraction)
3. **Default Financial Analyst** prompt (fallback)

The software statement JWT (provided by viaNexus API) may contain a `system_prompt` field that will be automatically extracted and used if no explicit system prompt is configured.

### ⚙️ Configuration Options

```python
config = {
    # LLM Settings (works with any provider)
    "LLM_API_KEY": "your-api-key",
    "LLM_MODEL": "your-model-name",     # Provider auto-detected from this
    "max_tokens": 2000,                 # Response length limit
    "temperature": 0.7,                 # Creativity (0.0-1.0)
    "system_prompt": "Custom prompt...", # Override default financial prompt
    
    # Optional: Explicit provider (overrides auto-detection)
    "provider": "openai",               # or "anthropic", "gemini"
    
    # Memory & Session Management
    "max_history_length": 50,           # Conversation history limit
    "user_id": "unique_user_id",        # For session isolation
    
    # viaNexus Integration
    "agentServers": {
        "viaNexus": {
            "server_url": "https://api.vianexus.com",
            "server_port": 443,
            "software_statement": "your-jwt-token"
        }
    }
}
```

### 📋 Available Methods

All clients provide the same interface:

| Method | Description | Use Case |
|--------|-------------|----------|
| `ask_single_question(question)` | Single query, no history | Quick lookups |
| `ask_question(question, maintain_history=False, use_memory=True)` | Flexible query with optional history/memory | Most common use case |
| `process_query(query)` | Streaming output with history | Real-time interactions |

For persistent clients:

| Method | Description | Use Case |
|--------|-------------|----------|
| `establish_persistent_connection()` | Create long-running connection | Session setup |
| `ask_with_persistent_session(question)` | Query with persistent context | Long conversations |
| `close_persistent_connection()` | Clean up connection | Session teardown |

## Contributing

We welcome contributions to the viaNexus AI Agent SDK for Python. If you would like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a clear and descriptive message.
4.  Push your changes to your fork.
5.  Create a pull request to the main repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
