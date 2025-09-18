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

Currently, the viaNexus AI Agent SDK for Python supports Google's Gemini and Anthropic family of models. As the SDK matures, we plan to extend support to other Large Language Models (LLMs) to provide a wider range of options for your conversational AI applications.


### OAuth
**Note:** OAuth is handled by the viaNexus_agent_sdk in the HTTP transport, you do not need to setup any authentication or authorization mechanisms
### Create a configuration file `config.yaml`
```yaml
development:
  LLM_API_KEY: "<LLM API Key>" # Supports both GEMINI and Anthropic (Claude) API keys
  LLM_MODEL: "<Model Name>" # Examples: gemini-2.5-flash, claude-3-5-sonnet-20241022
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
- **System Prompt Extraction**: `examples/clients/anthropic/streamable_setup_example.py`
- **Interactive Mode**: `examples/clients/anthropic/interactive_repl_chat.py`
- **YAML Configuration**: `examples/clients/anthropic/config_from_yaml.py`

The transport layer is established in our StreamableHTTPSetup class
The connection and data layer is managed by the session, and is initialized in our BaseMCPClient class

### Gemini Example Setup
Here's a basic example of how to use the SDK to create a Gemini agent and run it:

```python
# See examples/clients/gemini/basic_setup.py for full example
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
