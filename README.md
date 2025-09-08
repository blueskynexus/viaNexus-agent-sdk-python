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

### Anthropic Client Setup

The `AnthropicClient` provides two usage modes for different integration scenarios:

1. **Interactive REPL Mode**: For interactive chat sessions
2. **Single Question Mode**: For programmatic integration where you need string responses

#### Mode 1: Interactive REPL Chat

Use this mode for interactive chat sessions where responses are streamed to the console:

```python
# See examples/clients/anthropic/interactive_repl_chat.py for full example
```

#### Mode 2: Single Question Integration

Use this mode when you need to integrate the client into your application and get programmatic responses:

```python
# See examples/clients/anthropic/single_questions.py for full example
```

#### Configuration from YAML File

You can also load configuration from a YAML file:

```python
# See examples/clients/anthropic/config_from_yaml.py for full example
```

#### Integration in Your Application

Here's how to integrate the client into a web application or service:

```python
# See examples/clients/anthropic/service_integration.py for full example
```

#### Key Differences Between Modes

| Feature | Interactive REPL Mode | Single Question Mode |
|---------|----------------------|---------------------|
| Method | `client.run()` | `client.ask_single_question(question)` |
| Output | Streams to console | Returns string |
| Use Case | Interactive chat | Programmatic integration |
| Message History | Persistent across questions | Isolated per question |
| Streaming | Yes | No |

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
