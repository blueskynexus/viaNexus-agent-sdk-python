import yaml
import asyncio
from vianexus_agent_sdk.clients.anthropic_client import AnthropicClient

async def main():
    # Load config from YAML
    with open('config.yaml', 'r') as file:
        full_config = yaml.safe_load(file)
        client_config = full_config.get('development', {})
     
    client = AnthropicClient(client_config)
    
    # Use either mode
    await client.run()  # Interactive mode
    # OR
    # response = await client.ask_single_question("Your question")  # Single question mode

if __name__ == "__main__":
    asyncio.run(main())