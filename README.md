# viaNexus AI Agent SDK for Python

The viaNexus AI Agent SDK for Python provides a convenient way to create a financial data agent with access to reliable financial data through viaNexus.
This SDK allows you to build a powerful financial Agent or digital employee/assistant that will have access to the viaNexus Data Platform financial dataset catalog.

## Installation

To install the SDK, you can use `uv`:

```bash
uv add git+https://github.com/blueskynexus/viaNexus-agent-sdk-python --tag v1.0.0-pre12
```

Or with `pip`:

```bash
pip install git+https://github.com/blueskynexus/viaNexus-agent-sdk-python@v1.0.0-pre12
```

### Dependencies
- None required - the SDK will automatically install all necessary dependencies
- Supports Python 3.8+

## Usage

## LLM Support

The viaNexus AI Agent SDK for Python supports **three major LLM providers**:

- **🤖 OpenAI** - GPT-4, GPT-4o, GPT-3.5 Turbo, and o1 models
- **🧠 Anthropic** - Claude 3.5 Sonnet, Claude 3 Opus, and Claude 3 Haiku
- **✨ Google Gemini** - Gemini 2.5 Flash, Gemini Pro, and other Gemini models

All clients share a **unified interface** with consistent methods and behavior across providers.

## 📌 Quick Reference

### Memory Options Summary

| Memory Type | Method | Persistence | Use Case |
|-------------|--------|-------------|----------|
| **In-Memory** | `with_in_memory_store()` or `create_client_with_memory(memory_type="in_memory")` | Session only | Fast, temporary conversations |
| **File-Based** | `with_file_memory_store()` or `create_client_with_memory(memory_type="file")` | Survives restarts | Persistent local storage |
| **Stateless** | `without_memory()` or `create_client_with_memory(memory_type="none")` | None | Independent queries |

### Client Types Summary

| Client Type | Factory Method | Direct Class | Use Case |
|-------------|---------------|--------------|----------|
| **Standard** | `LLMClientFactory.create_client()` | `OpenAiClient`, `AnthropicClient`, `GeminiClient` | Per-request connections |
| **Persistent** | `LLMClientFactory.create_persistent_client()` | `PersistentOpenAiClient`, `PersistentAnthropicClient`, `PersistentGeminiClient` | Long-running sessions |

### Quick Start Comparison

```python
# Factory Pattern (Recommended) - Auto-detects provider
client = LLMClientFactory.create_client(config)

# Direct Instantiation - Explicit provider
client = OpenAiClient.with_in_memory_store(config)
client = AnthropicClient.without_memory(config)
client = GeminiClient.with_file_memory_store(config, storage_path="./conversations")
```

---

## 🏭 Unified Client Factory (Recommended)

The SDK provides a **unified factory pattern** that automatically detects and creates the appropriate LLM client based on your configuration. This is the **recommended approach** for most use cases.

### ✨ Key Features

- **🔍 Automatic Provider Detection**: Detects LLM provider from model names, API keys, or explicit configuration
- **🔄 Consistent Interface**: All clients implement the same interface regardless of provider
- **🧠 Universal Memory**: Seamless memory management across all providers (in-memory, file-based, or disabled)
- **⚡ Easy Switching**: Change providers without code changes, just update configuration
- **🛡️ Type Safety**: Full type hints for IDE support and error detection

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
    
    # Create client automatically (with default InMemoryStore)
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
| **OpenAI** | `gpt-*`, `o1-*` | `sk-*`, `sk_*` |
| **Anthropic** | `claude-*` | `sk-ant-*` |
| **Gemini** | `gemini-*` | Contains `AI` |

### 🔧 Factory Methods

The factory provides several methods for creating clients with different configurations:

```python
# 1. Standard client with auto-detection (includes InMemoryStore by default)
client = LLMClientFactory.create_client(config)
await client.initialize()

# 2. Explicit provider (overrides auto-detection)
anthropic_client = LLMClientFactory.create_client(config, provider="anthropic")
await anthropic_client.initialize()

# 3. Client with specific memory configuration
memory_client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="file",  # Options: "in_memory", "file", "none"
    storage_path="./conversations"
)
await memory_client.initialize()

# 4. Client without memory (stateless mode)
stateless_client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="none"
)
await stateless_client.initialize()

# 5. Persistent client for long-running sessions
persistent_client = LLMClientFactory.create_persistent_client(config)
await persistent_client.initialize()

# Always cleanup when done
await client.cleanup()
```

### 🧠 Memory Integration Options

The SDK supports three memory modes:

```python
# 1. In-Memory Store (default) - fast, session-only, lost on restart
client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="in_memory",
    user_id="user_123"
)

# 2. File-Based Storage - persistent across restarts
client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="file",
    storage_path="./conversations",
    user_id="user_123"
)

# 3. Stateless Mode - no memory, each query is independent
client = LLMClientFactory.create_client_with_memory(
    config, 
    memory_type="none"
)

await client.initialize()
# ... use the client ...
await client.cleanup()
```

### 🔄 Persistent Sessions

For long-running conversations with maintained MCP connections:

```python
async def portfolio_analysis_session():
    # Create persistent client (works with any provider)
    persistent_client = LLMClientFactory.create_persistent_client(config)
    await persistent_client.initialize()
    
    # Establish persistent connection
    session_id = await persistent_client.establish_persistent_connection()
    
    # Long-running conversation with maintained context
    response1 = await persistent_client.ask_with_persistent_session(
        "Analyze AAPL's recent performance",
        maintain_history=True,
        use_memory=True
    )
    response2 = await persistent_client.ask_with_persistent_session(
        "Compare it with MSFT",
        maintain_history=True,
        use_memory=True
    )
    
    print(f"Session: {session_id}")
    print(response1, response2)
    
    # Cleanup
    await persistent_client.close_persistent_connection()
    await persistent_client.cleanup()
```

---

## 📖 Provider-Specific Usage

While the **factory pattern is recommended**, you can also instantiate clients directly for fine-grained control.

### 1️⃣ OpenAI Client

#### Without Memory (Stateless)

```python
import asyncio
from vianexus_agent_sdk.clients.openai_client import OpenAiClient

async def main():
    config = {
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_API_KEY": "sk-your-openai-key",
        "max_tokens": 2000,
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client without memory
    client = OpenAiClient.without_memory(config)
    await client.initialize()
    
    # Ask questions (no history maintained)
    response = await client.ask_question("What is Tesla's current stock price?")
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### With In-Memory Store (Fast, Temporary)

```python
import asyncio
from vianexus_agent_sdk.clients.openai_client import OpenAiClient

async def main():
    config = {
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_API_KEY": "sk-your-openai-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with in-memory store
    client = OpenAiClient.with_in_memory_store(
        config,
        user_id="user_123",
        memory_session_id="session_abc"
    )
    await client.initialize()
    
    # Ask questions with conversation history
    response1 = await client.ask_question(
        "What is Apple's market cap?",
        maintain_history=True,
        use_memory=True
    )
    response2 = await client.ask_question(
        "Compare that to Microsoft",
        maintain_history=True,
        use_memory=True
    )
    
    print(response1)
    print(response2)
    
    await client.cleanup()

asyncio.run(main())
```

#### With File-Based Memory (Persistent)

```python
import asyncio
from vianexus_agent_sdk.clients.openai_client import OpenAiClient

async def main():
    config = {
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_API_KEY": "sk-your-openai-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with file-based memory
    client = OpenAiClient.with_file_memory_store(
        config,
        storage_path="./conversations",
        user_id="user_123"
    )
    await client.initialize()
    
    # Ask questions - conversation persists across restarts
    response = await client.ask_question(
        "Summarize Apple's latest earnings report",
        maintain_history=True,
        use_memory=True
    )
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### Persistent Connection (Long-Running Sessions)

```python
import asyncio
from vianexus_agent_sdk.clients.openai_client import PersistentOpenAiClient

async def main():
    config = {
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_API_KEY": "sk-your-openai-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create persistent client
    client = PersistentOpenAiClient.with_in_memory_store(config)
    await client.initialize()
    
    # Establish persistent connection
    mcp_session_id = await client.establish_persistent_connection()
    print(f"Connected with session: {mcp_session_id}")
    
    # Use persistent session for multiple queries
    response1 = await client.ask_with_persistent_session(
        "Analyze Tesla's financial health",
        maintain_history=True,
        use_memory=True
    )
    response2 = await client.ask_with_persistent_session(
        "What are the key risks?",
        maintain_history=True,
        use_memory=True
    )
    
    print(response1)
    print(response2)
    
    # Cleanup
    await client.close_persistent_connection()
    await client.cleanup()

asyncio.run(main())
```

---

### 2️⃣ Anthropic Client

#### Without Memory (Stateless)

```python
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def main():
    config = {
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "LLM_API_KEY": "sk-ant-your-anthropic-key",
        "max_tokens": 2000,
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client without memory
    client = AnthropicClient.without_memory(config)
    await client.initialize()
    
    # Ask questions (no history maintained)
    response = await client.ask_question("What is Amazon's PE ratio?")
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### With In-Memory Store (Fast, Temporary)

```python
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def main():
    config = {
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "LLM_API_KEY": "sk-ant-your-anthropic-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with in-memory store
    client = AnthropicClient.with_in_memory_store(
        config,
        user_id="analyst_001"
    )
    await client.initialize()
    
    # Ask questions with conversation history
    response1 = await client.ask_question(
        "What is Google's revenue growth?",
        maintain_history=True,
        use_memory=True
    )
    response2 = await client.ask_question(
        "How does that compare to Meta?",
        maintain_history=True,
        use_memory=True
    )
    
    print(response1)
    print(response2)
    
    await client.cleanup()

asyncio.run(main())
```

#### With File-Based Memory (Persistent)

```python
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def main():
    config = {
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "LLM_API_KEY": "sk-ant-your-anthropic-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with file-based memory
    client = AnthropicClient.with_file_memory_store(
        config,
        storage_path="./analyst_conversations",
        user_id="analyst_001"
    )
    await client.initialize()
    
    # Conversation persists across restarts
    response = await client.ask_question(
        "Analyze Nvidia's AI chip market position",
        maintain_history=True,
        use_memory=True
    )
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### Persistent Connection (Long-Running Sessions)

```python
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient

async def main():
    config = {
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "LLM_API_KEY": "sk-ant-your-anthropic-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create persistent client
    client = PersistentAnthropicClient.with_file_memory_store(
        config,
        storage_path="./conversations"
    )
    await client.initialize()
    
    # Establish persistent connection
    mcp_session_id = await client.establish_persistent_connection()
    print(f"Connected: {mcp_session_id}")
    
    # Long-running analysis session
    response1 = await client.ask_with_persistent_session(
        "Compare tech giants' cloud revenue",
        maintain_history=True,
        use_memory=True
    )
    response2 = await client.ask_with_persistent_session(
        "Which has the best growth trajectory?",
        maintain_history=True,
        use_memory=True
    )
    
    print(response1)
    print(response2)
    
    # Cleanup
    await client.close_persistent_connection()
    await client.cleanup()

asyncio.run(main())
```

---

### 3️⃣ Gemini Client

#### Without Memory (Stateless)

```python
import asyncio
from vianexus_agent_sdk.clients.gemini_client import GeminiClient

async def main():
    config = {
        "LLM_MODEL": "gemini-2.5-flash",
        "LLM_API_KEY": "your-gemini-api-key",
        "max_tokens": 2000,
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client without memory
    client = GeminiClient.without_memory(config)
    await client.initialize()
    
    # Ask questions (no history maintained)
    response = await client.ask_question("What is Intel's market share in CPUs?")
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### With In-Memory Store (Fast, Temporary)

```python
import asyncio
from vianexus_agent_sdk.clients.gemini_client import GeminiClient

async def main():
    config = {
        "LLM_MODEL": "gemini-2.5-flash",
        "LLM_API_KEY": "your-gemini-api-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with in-memory store
    client = GeminiClient.with_in_memory_store(
        config,
        user_id="trader_001"
    )
    await client.initialize()
    
    # Ask questions with conversation history
    response1 = await client.ask_question(
        "What is AMD's competitive advantage?",
        maintain_history=True,
        use_memory=True
    )
    response2 = await client.ask_question(
        "How does it compare to Intel?",
        maintain_history=True,
        use_memory=True
    )
    
    print(response1)
    print(response2)
    
    await client.cleanup()

asyncio.run(main())
```

#### With File-Based Memory (Persistent)

```python
import asyncio
from vianexus_agent_sdk.clients.gemini_client import GeminiClient

async def main():
    config = {
        "LLM_MODEL": "gemini-2.5-flash",
        "LLM_API_KEY": "your-gemini-api-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with file-based memory
    client = GeminiClient.with_file_memory_store(
        config,
        storage_path="./gemini_conversations",
        user_id="trader_001"
    )
    await client.initialize()
    
    # Conversation persists across restarts
    response = await client.ask_question(
        "Analyze semiconductor industry trends",
        maintain_history=True,
        use_memory=True
    )
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### Persistent Connection (Long-Running Sessions)

```python
import asyncio
from vianexus_agent_sdk.clients.gemini_client import PersistentGeminiClient

async def main():
    config = {
        "LLM_MODEL": "gemini-2.5-flash",
        "LLM_API_KEY": "your-gemini-api-key",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create persistent client
    client = PersistentGeminiClient.with_in_memory_store(config)
    await client.initialize()
    
    # Establish persistent connection
    mcp_session_id = await client.establish_persistent_connection()
    print(f"Connected: {mcp_session_id}")
    
    # Long-running analysis session
    response1 = await client.ask_with_persistent_session(
        "Compare EV manufacturers' production capacity",
        maintain_history=True,
        use_memory=True
    )
    response2 = await client.ask_with_persistent_session(
        "Which is best positioned for 2025?",
        maintain_history=True,
        use_memory=True
    )
    
    print(response1)
    print(response2)
    
    # Cleanup
    await client.close_persistent_connection()
    await client.cleanup()

asyncio.run(main())
```

---

## 🛠️ MCP Tools Integration

All clients automatically integrate with viaNexus MCP tools for real-time financial data:

```python
# No special setup needed - tools are automatically available
client = LLMClientFactory.create_client(config)
await client.initialize()

# The LLM will automatically use MCP tools when needed
response = await client.ask_question(
    "Get Tesla's latest earnings and calculate key financial ratios"
)
# The client automatically:
# 1. Uses the 'search' tool to find the appropriate dataset
# 2. Uses the 'fetch' tool to retrieve earnings data
# 3. Analyzes the data and calculates ratios
# 4. Returns a comprehensive response

print(response)
await client.cleanup()
```

---

## 📚 Examples

Comprehensive examples are available in the repository:

### Factory Pattern Examples (`examples/unified_client/`)
- **`basic_factory_usage.py`** - Auto-detection and basic usage patterns
- **`config_based_selection.py`** - YAML configs and environment variables
- **`real_world_usage.py`** - Production-ready service patterns with error handling

### Provider-Specific Examples
- **`examples/clients/openai/`** - OpenAI-specific examples
- **`examples/clients/anthropic/`** - Anthropic-specific examples
- **`examples/clients/gemini/`** - Gemini-specific examples

### Memory Management Examples (`examples/memory/`)
- **`basic_memory_example.py`** - Simple memory integration
- **`cross_client_conversation.py`** - Share conversations across providers
- **`session_isolation_demo.py`** - Isolate conversations by user/session

---

## ⚙️ Configuration

### Basic Configuration Dictionary

All clients require a configuration dictionary with the following structure:

```python
config = {
    # Required: LLM Configuration
    "LLM_MODEL": "gpt-4o-mini",           # Model name (auto-detects provider)
    "LLM_API_KEY": "sk-your-api-key",     # Your LLM provider API key
    
    # Required: viaNexus Integration
    "agentServers": {
        "viaNexus": {
            "server_url": "https://api.vianexus.com",
            "server_port": 443,
            "software_statement": "your-jwt-token"  # Get from viaNexus API
        }
    },
    
    # Optional: Behavior Configuration
    "max_tokens": 2000,                    # Response length limit (default: 1000)
    "max_history_length": 50,              # Conversation history limit (default: 50)
    "system_prompt": "Custom prompt...",   # Override default prompt
    "user_id": "unique_user_id",           # For session isolation
    "temperature": 0.7,                    # Creativity (0.0-1.0, provider-specific)
    
    # Optional: Explicit provider (if auto-detection doesn't work)
    "provider": "openai"                   # Options: "openai", "anthropic", "gemini"
}
```

### YAML Configuration File

You can also use a YAML configuration file:

```yaml
# config.yaml
development:
  # LLM Configuration
  LLM_API_KEY: "sk-your-api-key"
  LLM_MODEL: "gpt-4o-mini"
  
  # Optional Settings
  max_tokens: 2000
  user_id: "analyst_001"
  system_prompt: "You are a financial analyst specializing in tech stocks."
  
  # viaNexus Integration
  agentServers:
    viaNexus:
      server_url: "https://api.vianexus.com"
      server_port: 443
      software_statement: "your-jwt-token-here"
```

Load the YAML config in your code:

```python
import yaml

with open("config.yaml", "r") as f:
    config_data = yaml.safe_load(f)
    config = config_data["development"]

client = LLMClientFactory.create_client(config)
```

### Getting a Software Statement

The `software_statement` is a JWT token that authenticates your application with viaNexus:

1. Register your agent at: `https://api.vianexus.com/v1/agents/register`
2. Receive a JWT token (software statement)
3. Use this token in your configuration

**Note:** OAuth is handled automatically by the SDK - no additional authentication setup required.

### System Prompt Priority

All clients automatically determine the system prompt using this priority order:

1. **Config Parameter** `system_prompt` (highest priority)
2. **JWT Software Statement** `system_prompt` or `systemPrompt` field (automatic extraction)
3. **Default Financial Analyst** prompt (fallback)

The software statement JWT may contain a `system_prompt` field that will be automatically extracted and used if no explicit system prompt is configured.

```python
# Example: Custom system prompt
config = {
    "system_prompt": "You are a quantitative analyst specializing in algorithmic trading.",
    "LLM_MODEL": "claude-3-5-sonnet-20241022",
    "LLM_API_KEY": "sk-ant-...",
    "agentServers": {"viaNexus": {...}}
}
```

---

## 📋 Available Methods

All clients provide the same unified interface:

### Standard Methods

| Method | Description | Parameters | Use Case |
|--------|-------------|------------|----------|
| `initialize()` | Initialize client and setup connections | None | Required before use |
| `ask_single_question(question)` | Single query, no history | `question: str` | Quick lookups |
| `ask_question(question, ...)` | Flexible query with options | `question: str`<br>`maintain_history: bool = False`<br>`use_memory: bool = False`<br>`load_from_memory: bool = True` | Most common use case |
| `process_query(query)` | Streaming output with history | `query: str` | Real-time interactions |
| `cleanup()` | Clean up resources | None | Required after use |

### Persistent Client Methods

Additional methods for `PersistentAnthropicClient`, `PersistentOpenAiClient`, and `PersistentGeminiClient`:

| Method | Description | Returns | Use Case |
|--------|-------------|---------|----------|
| `establish_persistent_connection()` | Create long-running MCP connection | `str` (session ID) | Session setup |
| `ask_with_persistent_session(question, ...)` | Query with persistent context | `str` (response) | Long conversations |
| `close_persistent_connection()` | Clean up persistent connection | None | Session teardown |
| `is_connected` (property) | Check connection status | `bool` | Health check |
| `mcp_session_id` (property) | Get current session ID | `str | None` | Session tracking |

### Method Parameters

#### `ask_question()` Parameters:

```python
response = await client.ask_question(
    question="Your question here",
    maintain_history=False,      # Keep conversation context in memory
    use_memory=False,             # Save to/load from memory store
    load_from_memory=True         # Load previous conversation from memory
)
```

#### `ask_with_persistent_session()` Parameters:

```python
response = await persistent_client.ask_with_persistent_session(
    question="Your question here",
    maintain_history=True,        # Keep conversation context
    use_memory=True,              # Save to/load from memory store
    auto_establish_connection=True # Auto-connect if not connected
)
```

## Contributing

We welcome contributions to the viaNexus AI Agent SDK for Python. If you would like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a clear and descriptive message.
4.  Push your changes to your fork.
5.  Create a pull request to the main repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
