#!/usr/bin/env python3
"""
Configuration-Based LLM Client Selection Example

This example demonstrates how to use configuration files and environment
variables to dynamically select and configure LLM clients using the factory pattern.
"""

import asyncio
import logging
import sys
import os
import yaml
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vianexus_agent_sdk import LLMClientFactory, LLMProvider

# Configure logging
logging.basicConfig(level=logging.INFO)

def load_config_from_yaml(yaml_content: str) -> Dict[str, Any]:
    """Load configuration from YAML content."""
    return yaml.safe_load(yaml_content)

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        "provider": os.getenv("LLM_PROVIDER"),  # Optional explicit provider
        "LLM_MODEL": os.getenv("LLM_MODEL", "gpt-4o-mini"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", "your-api-key-here"),
        "max_tokens": int(os.getenv("MAX_TOKENS", "1500")),
        "system_prompt": os.getenv("SYSTEM_PROMPT", "You are a helpful AI assistant."),
        "agentServers": {
            "viaNexus": {
                "server_url": os.getenv("VIANEXUS_SERVER_URL", "https://api.vianexus.com"),
                "server_port": int(os.getenv("VIANEXUS_SERVER_PORT", "443")),
                "software_statement": os.getenv("VIANEXUS_JWT_TOKEN", "your-jwt-token-here")
            }
        }
    }

async def demonstrate_yaml_config():
    """Demonstrate client creation from YAML configuration."""
    
    print("📄 YAML Configuration Demo")
    print("=" * 50)
    
    # Sample YAML configurations for different providers
    yaml_configs = {
        "OpenAI": """
provider: openai
LLM_MODEL: gpt-4o-mini
LLM_API_KEY: sk-your-openai-key-here
max_tokens: 2000
temperature: 0.7
system_prompt: "You are a financial AI assistant with access to real-time market data."
agentServers:
  viaNexus:
    server_url: https://api.vianexus.com
    server_port: 443
    software_statement: your-jwt-token-here
memory:
  store_type: file
  file_path: ./openai_conversations
""",
        "Anthropic": """
provider: anthropic
LLM_MODEL: claude-3-5-sonnet-20241022
LLM_API_KEY: sk-ant-your-anthropic-key-here
max_tokens: 1500
temperature: 0.8
system_prompt: "You are Claude, a helpful AI assistant created by Anthropic."
agentServers:
  viaNexus:
    server_url: https://api.vianexus.com
    server_port: 443
    software_statement: your-jwt-token-here
memory:
  store_type: in_memory
""",
        "Gemini": """
provider: gemini
LLM_MODEL: gemini-2.5-flash
LLM_API_KEY: your-gemini-api-key-here
max_tokens: 1800
temperature: 0.6
system_prompt: "You are Gemini, Google's advanced AI assistant."
agentServers:
  viaNexus:
    server_url: https://api.vianexus.com
    server_port: 443
    software_statement: your-jwt-token-here
memory:
  store_type: file
  file_path: ./gemini_conversations
"""
    }
    
    for provider_name, yaml_content in yaml_configs.items():
        print(f"\n📋 Testing {provider_name} from YAML config")
        print("-" * 30)
        
        try:
            # Load configuration from YAML
            config = load_config_from_yaml(yaml_content)
            
            # Create client using factory
            client = LLMClientFactory.create_client(config)
            
            print(f"✅ Provider: {client.provider_name}")
            print(f"📝 Model: {client.model_name}")
            print(f"🎯 System prompt: {client.system_prompt[:50]}...")
            
            # Initialize and clean up
            await client.initialize()
            await client.cleanup()
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def demonstrate_env_config():
    """Demonstrate client creation from environment variables."""
    
    print("\n\n🌍 Environment Variables Demo")
    print("=" * 50)
    
    # Set some example environment variables
    test_env_configs = [
        {
            "name": "OpenAI from ENV",
            "env_vars": {
                "LLM_PROVIDER": "openai",
                "LLM_MODEL": "gpt-4o-mini",
                "LLM_API_KEY": "sk-test-openai-key",
                "MAX_TOKENS": "1200",
                "SYSTEM_PROMPT": "You are an AI assistant configured via environment variables."
            }
        },
        {
            "name": "Auto-detect Anthropic from ENV",
            "env_vars": {
                # No explicit provider - should auto-detect from model name
                "LLM_MODEL": "claude-3-5-sonnet-20241022",
                "LLM_API_KEY": "sk-ant-test-anthropic-key",
                "MAX_TOKENS": "1500"
            }
        },
        {
            "name": "Auto-detect Gemini from ENV",
            "env_vars": {
                # No explicit provider - should auto-detect from model name
                "LLM_MODEL": "gemini-2.5-flash",
                "LLM_API_KEY": "test-gemini-key",
                "MAX_TOKENS": "1800"
            }
        }
    ]
    
    for test_case in test_env_configs:
        print(f"\n📋 Testing: {test_case['name']}")
        print("-" * 30)
        
        # Temporarily set environment variables
        original_env = {}
        for key, value in test_case['env_vars'].items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            # Load configuration from environment
            config = load_config_from_env()
            
            # Create client using factory
            client = LLMClientFactory.create_client(config)
            
            print(f"✅ Provider: {client.provider_name}")
            print(f"📝 Model: {client.model_name}")
            print(f"🔢 Max tokens: {getattr(client, 'max_tokens', 'N/A')}")
            
            # Initialize and clean up
            await client.initialize()
            await client.cleanup()
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            # Restore original environment variables
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

async def demonstrate_dynamic_switching():
    """Demonstrate dynamic switching between providers at runtime."""
    
    print("\n\n🔄 Dynamic Provider Switching Demo")
    print("=" * 50)
    
    # Base configuration
    base_config = {
        "max_tokens": 1000,
        "system_prompt": "You are a helpful AI assistant.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token-here"
            }
        }
    }
    
    # Provider-specific configurations
    provider_configs = {
        LLMProvider.OPENAI: {
            **base_config,
            "LLM_MODEL": "gpt-4o-mini",
            "LLM_API_KEY": "sk-openai-key"
        },
        LLMProvider.ANTHROPIC: {
            **base_config,
            "LLM_MODEL": "claude-3-5-sonnet-20241022",
            "LLM_API_KEY": "sk-ant-anthropic-key"
        },
        LLMProvider.GEMINI: {
            **base_config,
            "LLM_MODEL": "gemini-2.5-flash",
            "LLM_API_KEY": "gemini-key"
        }
    }
    
    print("🔄 Creating clients for all providers dynamically...")
    
    clients = {}
    for provider, config in provider_configs.items():
        try:
            print(f"\n📋 Creating {provider.value} client...")
            
            # Create client with explicit provider
            client = LLMClientFactory.create_client(config, provider=provider)
            clients[provider] = client
            
            print(f"✅ {provider.value} client created successfully")
            print(f"📝 Model: {client.model_name}")
            
            # Initialize client
            await client.initialize()
            
        except Exception as e:
            print(f"❌ Failed to create {provider.value} client: {e}")
    
    # Simulate switching between providers
    print(f"\n🎯 Successfully created {len(clients)} clients")
    print("In a real application, you could switch between these clients based on:")
    print("  • User preferences")
    print("  • Cost optimization")
    print("  • Feature requirements")
    print("  • Performance needs")
    print("  • Availability/failover")
    
    # Clean up all clients
    for provider, client in clients.items():
        try:
            await client.cleanup()
            print(f"🧹 Cleaned up {provider.value} client")
        except Exception as e:
            print(f"❌ Error cleaning up {provider.value} client: {e}")

async def demonstrate_failover_pattern():
    """Demonstrate a failover pattern using multiple providers."""
    
    print("\n\n🛡️ Failover Pattern Demo")
    print("=" * 50)
    
    # Configuration with provider priority list
    config = {
        "max_tokens": 1000,
        "system_prompt": "You are a helpful AI assistant.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token-here"
            }
        }
    }
    
    # Provider priority list (first available will be used)
    provider_priority = [
        {
            "provider": LLMProvider.OPENAI,
            "config": {**config, "LLM_MODEL": "gpt-4o-mini", "LLM_API_KEY": "sk-openai-key"}
        },
        {
            "provider": LLMProvider.ANTHROPIC,
            "config": {**config, "LLM_MODEL": "claude-3-5-sonnet-20241022", "LLM_API_KEY": "sk-ant-anthropic-key"}
        },
        {
            "provider": LLMProvider.GEMINI,
            "config": {**config, "LLM_MODEL": "gemini-2.5-flash", "LLM_API_KEY": "gemini-key"}
        }
    ]
    
    print("🛡️ Attempting to create client with failover...")
    
    active_client = None
    for i, provider_config in enumerate(provider_priority, 1):
        provider = provider_config["provider"]
        config = provider_config["config"]
        
        print(f"\n🔄 Attempt {i}: Trying {provider.value}...")
        
        try:
            client = LLMClientFactory.create_client(config, provider=provider)
            await client.initialize()
            
            print(f"✅ Successfully connected to {provider.value}")
            active_client = client
            break
            
        except Exception as e:
            print(f"❌ {provider.value} failed: {e}")
            print(f"🔄 Falling back to next provider...")
    
    if active_client:
        print(f"\n🎉 Active client: {active_client.provider_name}")
        print(f"📝 Model: {active_client.model_name}")
        
        # Clean up
        await active_client.cleanup()
    else:
        print("\n💥 All providers failed - no client available")

async def main():
    """Run all configuration demonstrations."""
    
    print("🚀 Configuration-Based LLM Client Selection Demo")
    print("=" * 60)
    print("This demo shows how to use configuration files and environment")
    print("variables to dynamically select and configure LLM clients.")
    print()
    
    await demonstrate_yaml_config()
    await demonstrate_env_config()
    await demonstrate_dynamic_switching()
    await demonstrate_failover_pattern()
    
    print("\n\n🎉 Configuration demo completed!")
    print("=" * 60)
    print("The factory pattern makes it easy to:")
    print("  • Switch providers based on configuration")
    print("  • Implement failover strategies")
    print("  • Support multiple deployment environments")
    print("  • Maintain consistent interfaces across providers")

if __name__ == "__main__":
    asyncio.run(main())
