# viaNexus AI Agent SDK for Python

The viaNexus AI Agent SDK for Python provides a convenient way to create a financial data agent with access to reliable financial data through viaNexus.
This SDK allows you to build a powerful financial Agent or digital employee/assitant that will have access to the viaNexus Data Platform financial dataset catalog.

## Installation

To install the SDK, you can use uv:

```bash
    uv add git+https://github.com/blueskynexus/viaNexus-agent-sdk-python --tag v0.1.17-pre
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
  LLM_API_KEY: "<LLM API Key>" # Currently only supports GEMINI
  LLM_MODEL: "<GEMINI Model Name>" # gemini-2.5-flash
  LOG_LEVEL: "<LOGGING LEVEL>"
  user_id: "<UUID for the Agent Session>"
  app_name: "viaNexus_Agent"
  agentServers:
    viaNexus:
      server_url: "<viaNexus Agent Server HTTP URL>"
      server_port: <viaNexus Agent Port>
      software_statement: "<SOFTWARE STATEMENT>"
```
**Note:** Generate a software statement from the viaNexus api endpoint `v1/agents/register`

Here are examples of how to use the SDK to create an Anthropic agent and run it:

### Anthropic Example Setup

```python
import os
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

user_config = {} # see example config.yaml for setup

async def main():
    try:
        client = AnthropicClient(user_config)
        await client.run()
    except Exception as e:
        print(f"Connection setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Gemini Example Setup
Here's a basic example of how to use the SDK to create a Gemini agent and run it:

```python
import asyncio
from vianexus_agent_sdk.gemini.agents.llm_agent import GeminiLLMAgent
from vianexus_agent_sdk.gemini.runners.runner import GeminiRunner
from vianexus_agent_sdk.gemini.tools.agent_toolset import GeminiAgentToolset
from vianexus_agent_sdk.providers.oauth import ViaNexusOAuthProvider
# The following import is a patched fork of the adk-python which provides support for OAuth protocol through HTTP transport
from google.adk.tools.agent_tool.agent_session_manager import StreamableHTTPConnectionParams

async def main():
    # Before anything set the GEMINI API KEY as an Environment variable
    os.environ["GEMINI_API_KEY"] = config["LLM_API_KEY"]

    # 1. Set up the OAuth provider and authenticate
    # This will handle the OAuth 2.0 flow to authenticate with the viaNexus Agent server.
    # It will start a local server to handle the redirect callback.
    oauth_provider_manager = ViaNexusOAuthProvider(
        server_url="URL for the viaNexus Agent Server>", # Discovery of Auth server, the server providing /.well-known/oauth-protected-resource
        server_port="<Port for the viaNexus Agent Server>", # Replace with viaNexus Agent server port
        software_statement="JWT software statement"
    )
    # Intialize the OAuth client and starts the Callback server for client side of OAuth2.0/2.1
    oauth_provider = await oauth_provider_manager.initialize()

    # 2. Create connection parameters from the.oauth_provider
    connection_params = StreamableHTTPConnectionParams(
        # Remove trailing forward slash
            url=f"{server_url}:{server_port}/mcp",
            auth=oauth_provider,
    )

    # 3. Create a toolset
    agent_toolset = GeminiAgentToolset(connection_params=connection_params)

    # 4. Create a Gemini agent
    agent = GeminiLLMAgent(
        model="<GEMINI model i.e. gemini-2.5-flash>",
        tools=[agent_toolset],
    )

    # 5. Create a runner and execute the agent
    runner = GeminiRunner(agent=agent, app_name="my-runner", user_id="UUID for the session", session_id="my-session")
    await runner.initialize()

     while True:
        try:
            query = input("Enter a query: ")
            logging.debug(f"Query: {query}")
            if query == "exit":
                break
            if not query:
                continue
            async for event in runner.run_async(query):
                logging.info(f"Agent: {event}")
        except KeyboardInterrupt:
            logging.warning("Exiting...")
            break
        except Exception as e:
            logging.warning(f"Error: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())

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
