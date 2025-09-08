import asyncio
import logging
import os
from vianexus_agent_sdk.gemini.agents.llm_agent import GeminiLLMAgent
from vianexus_agent_sdk.gemini.runners.runner import GeminiRunner
from vianexus_agent_sdk.gemini.tools.agent_toolset import GeminiAgentToolset
from vianexus_agent_sdk.providers.oauth import ViaNexusOAuthProvider
# The following import is a patched fork of the adk-python which provides support for OAuth protocol through HTTP transport
from google.adk.tools.agent_tool.agent_session_manager import StreamableHTTPConnectionParams

async def main():
    # Example configuration - replace with your actual values
    config = {
        "LLM_API_KEY": "your-gemini-api-key",
        "server_url": "https://your-vianexus-server.com",
        "server_port": "443",
        "software_statement": "your-jwt-software-statement"
    }
    
    # Before anything set the GEMINI API KEY as an Environment variable
    os.environ["GEMINI_API_KEY"] = config["LLM_API_KEY"]

    # 1. Set up the OAuth provider and authenticate
    # This will handle the OAuth 2.0 flow to authenticate with the viaNexus Agent server.
    # It will start a local server to handle the redirect callback.
    oauth_provider_manager = ViaNexusOAuthProvider(
        server_url=config["server_url"],  # Discovery of Auth server, the server providing /.well-known/oauth-protected-resource
        server_port=config["server_port"],  # Replace with viaNexus Agent server port
        software_statement=config["software_statement"]
    )
    # Initialize the OAuth client and starts the Callback server for client side of OAuth2.0/2.1
    oauth_provider = await oauth_provider_manager.initialize()

    # 2. Create connection parameters from the oauth_provider
    connection_params = StreamableHTTPConnectionParams(
        # Remove trailing forward slash
        url=f"{config['server_url']}:{config['server_port']}/agent",
        auth=oauth_provider,
    )

    # 3. Create a toolset
    agent_toolset = GeminiAgentToolset(connection_params=connection_params)

    # 4. Create a Gemini agent
    agent = GeminiLLMAgent(
        model="gemini-2.5-flash",
        tools=[agent_toolset],
    )

    # 5. Create a runner and execute the agent
    runner = GeminiRunner(
        agent=agent, 
        app_name="my-runner", 
        user_id="example-user-uuid", 
        session_id="my-session"
    )
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