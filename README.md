# viaNexus AI Agent SDK for Python

The viaNexus AI Agent SDK for Python provides a convenient way to create a financial data agent with access to reliable financial data through viaNexus.
This SDK allows you to build a powerful financial Agent or digital employee/assitant that will have access to the viaNexus Data Platform financial dataset catalog.

## Installation

To install the SDK, you can use uv:

```bash
    uv add git+https://github.com/blueskynexus/viaNexus-agent-sdk-python --tag v0.1.19-pre
```
### Dependencies
- None required
- vianexus_agent_sdk will pull in all of the required dependencies.
- **Note:** _Do not install the google-adk module from google, use the one provided by the vianexus_agent_sdk it has been patched to follow OAuth authentication protocol in the HTTP transport_

## Usage
## LLM Support

Currently, the viaNexus AI Agent SDK for Python supports Google's Gemini, Anthropic Claude, and OpenAI GPT family of models. As the SDK matures, we plan to extend support to other Large Language Models (LLMs) to provide a wider range of options for your conversational AI applications.


### OAuth
**Note:** OAuth is handled by the viaNexus_agent_sdk in the HTTP transport, you do not need to setup any authentication or authorization mechanisms
### Create a configuration file `config.yaml`
```yaml
development:
  LLM_API_KEY: "<LLM API Key>" # Supports GEMINI, Anthropic (Claude), and OpenAI (GPT) API keys
  LLM_MODEL: "<Model Name>" # Examples: gemini-2.5-flash, claude-3-5-sonnet-20241022, gpt-4o-mini
  LOG_LEVEL: "<LOGGING LEVEL>"
  max_tokens: 1000 # Optional: Maximum tokens for responses
  user_id: "<UUID for the Agent Session>"
  app_name: "viaNexus_Agent"
  agentServers:
    viaNexus:
      server_url: "<viaNexus Agent Server HTTP URL>"
      server_port: <viaNexus Agent Port>
      software_statement: "<SOFTWARE STATEMENT>"
```

**Note:** Generate a software statement from the viaNexus api endpoint `v1/agents/register`

#### System Prompt Priority

The AnthropicClient automatically determines the system prompt using this priority order:

1. **Config Parameter** `system_prompt` (highest priority)
2. **JWT Software Statement** `system_prompt` or `systemPrompt` field (automatic extraction)
3. **Default Financial Analyst** prompt (fallback)

The software statement JWT (provided by viaNexus API) may contain a `system_prompt` field that will be automatically extracted and used if no explicit system prompt is configured.

### Anthropic Client Setup

The `AnthropicClient` provides flexible usage modes for different integration scenarios:

#### Basic Usage

```python
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def main():
    config = {
        "LLM_API_KEY": "your-anthropic-api-key",
        "LLM_MODEL": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        # Optional: Override system prompt (otherwise uses JWT or default)
        # "system_prompt": "You are a specialized trading advisor...",
        "agentServers": {
            "viaNexus": {
                "server_url": "your-vianexus-server-url",
                "server_port": 443,
                "software_statement": "your-software-statement-jwt"  # May contain system_prompt
            }
        },
    }
    
    client = AnthropicClient(config)
    await client.setup_connection()
    
    # Ask single questions
    response = await client.ask_single_question("What is AAPL's current price?")
    print(response)
    
    # Ask questions with conversation history
    response1 = await client.ask_question("What is Microsoft's stock price?", maintain_history=True)
    response2 = await client.ask_question("How has it performed this quarter?", maintain_history=True)
    
    await client.cleanup()

asyncio.run(main())
```


```

#### Persistent Connections

For applications requiring multiple requests with maintained context:

```python
from vianexus_agent_sdk.clients.anthropic_client import PersistentAnthropicClient

async def persistent_example():
    client = PersistentAnthropicClient(config)
    
    # Establish persistent connection once
    session_id = await client.establish_persistent_connection()
    
    # Multiple questions maintain context and connection
    response1 = await client.ask_with_persistent_session("Analyze Apple's financials")
    response2 = await client.ask_with_persistent_session("What about their competitors?")
    
    await client.cleanup()
```

#### Available Methods

| Method | Description | History | Use Case |
|--------|-------------|---------|----------|
| `ask_single_question(question)` | Single isolated question | No | Independent queries |
| `ask_question(question, maintain_history=True)` | Question with optional history | Optional | Flexible conversations |
| `ask_with_persistent_session(question)` | Persistent session question | Yes | Long conversations |
| `process_query(question)` | Streaming output | Yes | Interactive chat |
| `run()` | Interactive REPL mode | Yes | Development/testing |

#### Examples

- **Basic Usage**: `examples/clients/anthropic/single_questions.py`
- **Service Integration**: `examples/clients/anthropic/service_integration.py`
- **Persistent Sessions**: `examples/clients/anthropic/persistent_session.py`
- **Interactive Mode**: `examples/clients/anthropic/interactive_repl_chat.py`

The transport layer is established in our StreamableHTTPSetup class
The connection and data layer is managed by the session, and is initialized in our BaseMCPClient class

### OpenAI Client Integration

The `OpenAiClient` uses **OpenAI SDK 2.0.0** with the cutting-edge `responses.create` API, providing advanced AI capabilities with seamless viaNexus integration.

#### 🚀 Quick Start

```python
import asyncio
from vianexus_agent_sdk.clients.openai_client import OpenAiClient

async def main():
    config = {
        "LLM_API_KEY": "your-openai-api-key",
        "LLM_MODEL": "gpt-4o-mini",  # or "gpt-4o", "gpt-3.5-turbo"
        "max_tokens": 1500,
        "system_prompt": "You are a financial AI assistant with real-time market access.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with memory
    client = OpenAiClient.with_in_memory_store(config)
    await client.initialize()
    
    # Ask questions with automatic tool calling
    response = await client.ask_question(
        "What's Apple's current stock price and how has it performed this month?",
        maintain_history=True
    )
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### 📚 Comprehensive Examples

The SDK includes detailed examples for every use case:

- **`examples/clients/openai/basic_setup.py`** - Simple setup and single questions
- **`examples/clients/openai/conversation_with_history.py`** - Maintained conversation context
- **`examples/clients/openai/persistent_session.py`** - Long-running sessions
- **`examples/clients/openai/memory_integration.py`** - Different memory storage options
- **`examples/clients/openai/tool_calling_demo.py`** - MCP tool integration showcase
- **`examples/clients/openai/config_from_yaml.py`** - YAML configuration management
- **`examples/clients/openai/interactive_repl.py`** - Interactive command-line interface

#### 🧠 Memory Integration Options

Choose the memory strategy that fits your application:

```python
# 1. In-Memory Store (fast, session-only)
client = OpenAiClient.with_in_memory_store(config, user_id="user_123")

# 2. File-Based Storage (persistent across restarts)
client = OpenAiClient.with_file_memory_store(
    config, 
    storage_path="./conversations",
    user_id="user_123",
    memory_session_id="portfolio_analysis_001"
)

# 3. Stateless Mode (no memory, each query independent)
client = OpenAiClient.without_memory(config)
```

#### 🔄 Persistent Sessions

For long-running conversations with maintained context and connection:

```python
from vianexus_agent_sdk.clients.openai_client import PersistentOpenAiClient

async def portfolio_analysis_session():
    client = PersistentOpenAiClient(config)
    
    # Establish persistent connection
    session_id = await client.establish_persistent_connection()
    print(f"Session established: {session_id}")
    
    # Multiple related questions with full context
    await client.ask_with_persistent_session("Analyze my tech stock portfolio")
    await client.ask_with_persistent_session("What are the main risks?")
    await client.ask_with_persistent_session("Should I rebalance now?")
    
    # Connection and context maintained throughout
    await client.cleanup()
```

#### 🛠️ Tool Integration & Real-Time Data

The OpenAI client automatically integrates with viaNexus MCP tools:

```python
# Tools are automatically called when needed
response = await client.ask_question(
    "Compare Apple, Microsoft, and Google's P/E ratios and recommend the best buy"
)
# The AI will automatically:
# 1. Call stock price tools for current data
# 2. Calculate P/E ratios
# 3. Analyze and provide recommendations
```

#### ⚡ Advanced Features (OpenAI SDK 2.0.0)

The OpenAI client leverages the cutting-edge `responses.create` API:

- **🎯 Unified Interface**: Single API for text, images, and structured outputs
- **🔧 Enhanced Tool Integration**: Superior function calling with parallel execution
- **💬 Native Conversation Management**: Built-in context handling and memory
- **🧠 Advanced Reasoning**: Support for reasoning, background processing, and response chaining
- **⚡ Optimized Performance**: Faster responses and better token efficiency

#### 📋 Available Methods

| Method | Description | History | Memory | Use Case |
|--------|-------------|---------|--------|----------|
| `ask_single_question(question)` | Single isolated question | ❌ No | ❌ No | Quick independent queries |
| `ask_question(question, maintain_history=True)` | Flexible conversation | ✅ Optional | ✅ Optional | Most conversations |
| `ask_with_persistent_session(question)` | Long-running session | ✅ Yes | ✅ Yes | Extended analysis |
| `process_query(question)` | Streaming with tools | ✅ Yes | ✅ Yes | Interactive chat |

#### ⚙️ Configuration Options

```python
config = {
    # OpenAI Settings
    "LLM_API_KEY": "your-openai-api-key",
    "LLM_MODEL": "gpt-4o-mini",  # gpt-4o, gpt-4o-mini, gpt-3.5-turbo
    "max_tokens": 2000,          # Response length limit
    "temperature": 0.7,          # Creativity (0.0-1.0)
    
    # System Behavior
    "system_prompt": "Custom system prompt...",
    "max_history_length": 50,    # Conversation memory limit
    
    # viaNexus Integration
    "agentServers": {
        "viaNexus": {
            "server_url": "https://api.vianexus.com",
            "server_port": 443,
            "software_statement": "your-jwt-token"  # May contain system prompt
        }
    }
}
```

#### 🎮 Interactive Mode

Run the interactive REPL for hands-on exploration:

```bash
python examples/clients/openai/interactive_repl.py
```

Features:
- **Real-time conversation** with maintained context
- **Tool calling** with live market data
- **Command system** (`/help`, `/history`, `/tools`, `/clear`)
- **Session statistics** and management

---

## Google Gemini Integration

The `GeminiClient` provides seamless integration with Google's Gemini models, featuring the same advanced memory management and persistent session capabilities as other clients.

#### 🚀 Quick Start

```python
import asyncio
from vianexus_agent_sdk.clients.gemini_client import GeminiClient

async def main():
    config = {
        "LLM_API_KEY": "your-gemini-api-key",
        "LLM_MODEL": "gemini-2.5-flash",  # or "gemini-pro", "gemini-pro-vision"
        "max_tokens": 1500,
        "system_prompt": "You are a financial AI assistant with real-time market access.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token"
            }
        }
    }
    
    # Create client with memory
    client = GeminiClient.with_in_memory_store(config)
    await client.initialize()
    
    # Ask questions with automatic tool calling
    response = await client.ask_question(
        "What's Google's current stock price and how has it performed this quarter?",
        maintain_history=True
    )
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

#### 📚 Comprehensive Examples

The SDK includes detailed examples for every use case:

- **`examples/clients/gemini/basic_setup.py`** - Simple setup and single questions
- **`examples/clients/gemini/conversation_with_history.py`** - Maintained conversation context
- **`examples/clients/gemini/persistent_session.py`** - Long-running sessions
- **`examples/clients/gemini/memory_integration.py`** - Different memory storage options
- **`examples/clients/gemini/tool_calling_demo.py`** - MCP tool integration showcase

#### 🧠 Memory Integration Options

Choose the memory strategy that fits your application:

```python
# 1. In-Memory Store (fast, session-only)
client = GeminiClient.with_in_memory_store(config, user_id="user_123")

# 2. File-Based Storage (persistent across restarts)
client = GeminiClient.with_file_memory_store(
    config, 
    storage_path="./conversations",
    user_id="user_123",
    memory_session_id="portfolio_analysis_001"
)

# 3. Stateless Mode (no memory, each query independent)
client = GeminiClient.without_memory(config)
```

#### 🔄 Persistent Sessions

For long-running conversations with maintained context and connection:

```python
from vianexus_agent_sdk.clients.gemini_client import PersistentGeminiClient

async def portfolio_analysis_session():
    client = PersistentGeminiClient(config)
    
    # Establish persistent connection
    session_id = await client.establish_persistent_connection()
    print(f"Session established: {session_id}")
    
    # Multiple related questions with full context
    await client.ask_with_persistent_session("Analyze my tech stock portfolio")
    await client.ask_with_persistent_session("What are the main risks?")
    await client.ask_with_persistent_session("Should I rebalance now?")
    
    # Connection and context maintained throughout
    await client.cleanup()
```

#### 🛠️ Tool Integration & Real-Time Data

The Gemini client automatically integrates with viaNexus MCP tools:

```python
# Tools are automatically called when needed
response = await client.ask_question(
    "Compare Apple, Microsoft, and Google's P/E ratios and recommend the best buy"
)
# The AI will automatically:
# 1. Call stock price tools for current data
# 2. Calculate P/E ratios
# 3. Analyze and provide recommendations
```

#### ⚡ Advanced Features (Gemini API)

The Gemini client leverages Google's advanced AI capabilities:

- **🎯 Multi-Modal Support**: Text, images, and structured outputs
- **🔧 Enhanced Tool Integration**: Superior function calling with parallel execution
- **💬 Native Conversation Management**: Built-in context handling and memory
- **🧠 Advanced Reasoning**: Support for complex reasoning and analysis
- **⚡ Optimized Performance**: Fast responses and efficient token usage

#### 📋 Available Methods

| Method | Description | History | Memory | Use Case |
|--------|-------------|---------|--------|----------|
| `ask_single_question(question)` | Single isolated question | ❌ No | ❌ No | Quick independent queries |
| `ask_question(question, maintain_history=True)` | Flexible conversation | ✅ Optional | ✅ Optional | Most conversations |
| `ask_with_persistent_session(question)` | Long-running session | ✅ Yes | ✅ Yes | Extended analysis |
| `process_query(question)` | Streaming with tools | ✅ Yes | ✅ Yes | Interactive chat |

#### ⚙️ Configuration Options

```python
config = {
    # Gemini Settings
    "LLM_API_KEY": "your-gemini-api-key",
    "LLM_MODEL": "gemini-2.5-flash",  # gemini-pro, gemini-pro-vision
    "max_tokens": 2000,              # Response length limit
    "temperature": 0.7,              # Creativity (0.0-1.0)
    
    # System Behavior
    "system_prompt": "Custom system prompt...",
    "max_history_length": 50,        # Conversation memory limit
    
    # viaNexus Integration
    "agentServers": {
        "viaNexus": {
            "server_url": "https://api.vianexus.com",
            "server_port": 443,
            "software_statement": "your-jwt-token"  # May contain system prompt
        }
    }
}
```

#### 🎯 Gemini-Specific Features

- **System Instructions**: Uses Gemini's native `system_instruction` parameter
- **Multi-Part Messages**: Supports Gemini's rich message format with parts
- **Function Responses**: Optimized for Gemini's function calling format
- **Memory Conversion**: Automatic conversion between universal memory format and Gemini messages

---

#### Available Methods

| Method | Description | History | Use Case |
|--------|-------------|---------|----------|
| `ask_single_question(question)` | Single isolated question | No | Independent queries |
| `ask_question(question, maintain_history=True)` | Question with optional history | Optional | Flexible conversations |
| `ask_with_persistent_session(question)` | Persistent session question | Yes | Long conversations |
| `process_query(question)` | Streaming output | Yes | Interactive chat |
| `run()` | Interactive REPL mode | Yes | Development/testing |

#### Examples

- **Basic Usage**: `examples/clients/anthropic/single_questions.py`
- **Service Integration**: `examples/clients/anthropic/service_integration.py`
- **Persistent Sessions**: `examples/clients/anthropic/persistent_session.py`
- **System Prompt Extraction**: `examples/clients/anthropic/streamable_setup_example.py`
- **Interactive Mode**: `examples/clients/anthropic/interactive_repl_chat.py`
- **YAML Configuration**: `examples/clients/anthropic/config_from_yaml.py`

The transport layer is established in our StreamableHTTPSetup class
The connection and data layer is managed by the session, and is initialized in our BaseMCPClient class


## Contributing

We welcome contributions to the viaNexus AI Agent SDK for Python. If you would like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with a clear and descriptive message.
4.  Push your changes to your fork.
5.  Create a pull request to the main repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
