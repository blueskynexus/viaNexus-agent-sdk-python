#!/usr/bin/env python3
"""
OpenAI Client Configuration from YAML Example

This example demonstrates how to configure the OpenAI client
using YAML configuration files for different environments.
"""

import asyncio
import logging
import sys
import os
import yaml
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.openai_client import OpenAiClient

# Configure logging
logging.basicConfig(level=logging.INFO)

# Sample YAML configurations
DEVELOPMENT_CONFIG = """
# Development Configuration for OpenAI Client
llm:
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4o-mini"
  max_tokens: 1000
  temperature: 0.7
  system_prompt: "You are a helpful financial AI assistant in development mode."

memory:
  enabled: true
  type: "in_memory"
  max_history_length: 20

agent_servers:
  via_nexus:
    server_url: "https://dev-api.vianexus.com"
    server_port: 443
    software_statement: "${VIANEXUS_JWT}"

logging:
  level: "DEBUG"
"""

PRODUCTION_CONFIG = """
# Production Configuration for OpenAI Client
llm:
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4o"
  max_tokens: 2000
  temperature: 0.3
  system_prompt: "You are a professional financial AI assistant providing accurate market analysis and investment guidance."

memory:
  enabled: true
  type: "file"
  storage_path: "./conversations"
  max_history_length: 50

agent_servers:
  via_nexus:
    server_url: "https://api.vianexus.com"
    server_port: 443
    software_statement: "${VIANEXUS_JWT}"

logging:
  level: "INFO"
"""

def expand_env_vars(config_dict):
    """Recursively expand environment variables in config"""
    if isinstance(config_dict, dict):
        return {k: expand_env_vars(v) for k, v in config_dict.items()}
    elif isinstance(config_dict, list):
        return [expand_env_vars(item) for item in config_dict]
    elif isinstance(config_dict, str) and config_dict.startswith("${") and config_dict.endswith("}"):
        env_var = config_dict[2:-1]
        return os.getenv(env_var, config_dict)
    else:
        return config_dict

def yaml_to_client_config(yaml_config):
    """Convert YAML config to OpenAI client config format"""
    config = expand_env_vars(yaml_config)
    
    return {
        "LLM_API_KEY": config["llm"]["api_key"],
        "LLM_MODEL": config["llm"]["model"],
        "max_tokens": config["llm"]["max_tokens"],
        "temperature": config["llm"].get("temperature", 0.7),
        "system_prompt": config["llm"]["system_prompt"],
        "max_history_length": config["memory"]["max_history_length"],
        "agentServers": {
            "viaNexus": {
                "server_url": config["agent_servers"]["via_nexus"]["server_url"],
                "server_port": config["agent_servers"]["via_nexus"]["server_port"],
                "software_statement": config["agent_servers"]["via_nexus"]["software_statement"]
            }
        }
    }

async def config_from_yaml_example():
    """Demonstrate loading configuration from YAML files"""
    
    try:
        print("📄 OpenAI Client YAML Configuration Example")
        print("=" * 50)
        
        # Create temporary YAML files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as dev_file:
            dev_file.write(DEVELOPMENT_CONFIG)
            dev_config_path = dev_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as prod_file:
            prod_file.write(PRODUCTION_CONFIG)
            prod_config_path = prod_file.name
        
        # Example 1: Development Configuration
        print("\n1️⃣ Development Configuration:")
        with open(dev_config_path, 'r') as f:
            dev_yaml = yaml.safe_load(f)
        
        dev_config = yaml_to_client_config(dev_yaml)
        print(f"  Model: {dev_config['LLM_MODEL']}")
        print(f"  Max Tokens: {dev_config['max_tokens']}")
        print(f"  Temperature: {dev_config.get('temperature', 'default')}")
        print(f"  Server: {dev_config['agentServers']['viaNexus']['server_url']}")
        
        # Create development client
        dev_client = OpenAiClient.with_in_memory_store(dev_config, user_id="dev_user")
        await dev_client.initialize()
        
        # Test development client
        dev_response = await dev_client.ask_single_question(
            "What's a simple explanation of compound interest?"
        )
        print(f"  Dev Response: {dev_response[:150]}...")
        await dev_client.cleanup()
        
        # Example 2: Production Configuration
        print("\n2️⃣ Production Configuration:")
        with open(prod_config_path, 'r') as f:
            prod_yaml = yaml.safe_load(f)
        
        prod_config = yaml_to_client_config(prod_yaml)
        print(f"  Model: {prod_config['LLM_MODEL']}")
        print(f"  Max Tokens: {prod_config['max_tokens']}")
        print(f"  Temperature: {prod_config.get('temperature', 'default')}")
        print(f"  Server: {prod_config['agentServers']['viaNexus']['server_url']}")
        
        # Create production client with file storage
        temp_storage = tempfile.mkdtemp()
        prod_client = OpenAiClient.with_file_memory_store(
            prod_config, 
            storage_path=temp_storage,
            user_id="prod_user"
        )
        await prod_client.initialize()
        
        # Test production client
        prod_response = await prod_client.ask_question(
            "Provide a detailed analysis of diversification strategies for a $100k portfolio.",
            maintain_history=True
        )
        print(f"  Prod Response: {prod_response[:150]}...")
        await prod_client.cleanup()
        
        # Example 3: Environment-specific settings
        print("\n3️⃣ Environment Variables:")
        print(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
        print(f"  VIANEXUS_JWT: {'✅ Set' if os.getenv('VIANEXUS_JWT') else '❌ Not set'}")
        
        # Example 4: Configuration validation
        print("\n4️⃣ Configuration Validation:")
        required_keys = ["LLM_API_KEY", "LLM_MODEL", "agentServers"]
        for key in required_keys:
            if key in prod_config:
                print(f"  ✅ {key}: Present")
            else:
                print(f"  ❌ {key}: Missing")
        
        print("\n✅ YAML configuration examples completed!")
        
        # Clean up
        os.unlink(dev_config_path)
        os.unlink(prod_config_path)
        import shutil
        shutil.rmtree(temp_storage, ignore_errors=True)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def dynamic_config_example():
    """Demonstrate dynamic configuration switching"""
    
    print("\n🔄 Dynamic Configuration Switching:")
    
    # Base configuration
    base_config = {
        "LLM_API_KEY": os.getenv("OPENAI_API_KEY", "test-key"),
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": os.getenv("VIANEXUS_JWT", "test-jwt")
            }
        }
    }
    
    # Different model configurations
    model_configs = {
        "fast": {"LLM_MODEL": "gpt-4o-mini", "max_tokens": 500},
        "balanced": {"LLM_MODEL": "gpt-4o-mini", "max_tokens": 1500},
        "powerful": {"LLM_MODEL": "gpt-4o", "max_tokens": 2000}
    }
    
    for mode, model_config in model_configs.items():
        config = {**base_config, **model_config}
        print(f"\n  🎯 {mode.upper()} mode: {config['LLM_MODEL']} ({config['max_tokens']} tokens)")
        
        # You could create different clients for different use cases
        # client = OpenAiClient.without_memory(config)
        # await client.initialize()
        # ... use client ...
        # await client.cleanup()

if __name__ == "__main__":
    asyncio.run(config_from_yaml_example())
    asyncio.run(dynamic_config_example())
