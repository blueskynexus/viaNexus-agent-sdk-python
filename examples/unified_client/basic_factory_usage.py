#!/usr/bin/env python3
"""
Basic Unified LLM Client Factory Usage Example

This example demonstrates how to use the LLMClientFactory to create
clients automatically based on configuration, without needing to know
which specific LLM provider to use.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vianexus_agent_sdk import LLMClientFactory

# Configure logging
logging.basicConfig(level=logging.INFO)

async def demonstrate_auto_detection():
    """Demonstrate automatic provider detection based on model names."""
    
    print("🤖 Unified LLM Client Factory - Auto Detection Demo")
    print("=" * 60)
    
    # Base configuration (same for all providers)
    base_config = {
        "max_tokens": 1500,
        "system_prompt": "You are a helpful AI assistant.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token-here"
            }
        }
    }
    
    # Test configurations for different providers
    test_configs = [
        {
            "name": "OpenAI GPT-4o",
            "config": {
                **base_config,
                "LLM_MODEL": "gpt-4o-mini",
                "LLM_API_KEY": "sk-your-openai-key-here"
            }
        },
        {
            "name": "Anthropic Claude",
            "config": {
                **base_config,
                "LLM_MODEL": "claude-3-5-sonnet-20241022",
                "LLM_API_KEY": "sk-ant-your-anthropic-key-here"
            }
        },
        {
            "name": "Google Gemini",
            "config": {
                **base_config,
                "LLM_MODEL": "gemini-2.5-flash",
                "LLM_API_KEY": "your-gemini-api-key-here"
            }
        }
    ]
    
    for test_case in test_configs:
        print(f"\n📋 Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Create client using factory (auto-detection)
            client = LLMClientFactory.create_client(test_case['config'])
            
            print(f"✅ Provider detected: {client.provider_name}")
            print(f"📝 Model: {client.model_name}")
            print(f"🧠 Memory enabled: {hasattr(client, 'memory_enabled') and client.memory_enabled}")
            
            # Initialize client
            await client.initialize()
            print(f"🔗 Client initialized successfully")
            
            # Clean up
            await client.cleanup()
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def demonstrate_explicit_provider():
    """Demonstrate explicit provider specification."""
    
    print("\n\n🎯 Explicit Provider Specification Demo")
    print("=" * 60)
    
    # Configuration that could match multiple providers
    ambiguous_config = {
        "LLM_MODEL": "custom-model-name",  # Doesn't match any pattern
        "LLM_API_KEY": "custom-api-key",   # Doesn't match any pattern
        "max_tokens": 1000,
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token-here"
            }
        }
    }
    
    providers_to_test = ["openai", "anthropic", "gemini"]
    
    for provider in providers_to_test:
        print(f"\n📋 Creating {provider.upper()} client explicitly")
        print("-" * 40)
        
        try:
            # Create client with explicit provider
            client = LLMClientFactory.create_client(
                ambiguous_config, 
                provider=provider
            )
            
            print(f"✅ Provider: {client.provider_name}")
            print(f"📝 Model: {client.model_name}")
            
            # Initialize and clean up
            await client.initialize()
            await client.cleanup()
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def demonstrate_memory_configurations():
    """Demonstrate different memory configurations."""
    
    print("\n\n🧠 Memory Configuration Demo")
    print("=" * 60)
    
    config = {
        "LLM_MODEL": "gpt-4o-mini",  # Will auto-detect OpenAI
        "LLM_API_KEY": "sk-test-key",
        "max_tokens": 1000,
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token-here"
            }
        }
    }
    
    memory_configs = [
        {
            "name": "In-Memory Store",
            "type": "in_memory",
            "description": "Fast, temporary memory (lost on restart)"
        },
        {
            "name": "File-Based Store",
            "type": "file",
            "description": "Persistent local file storage",
            "storage_path": "./demo_conversations"
        },
        {
            "name": "No Memory",
            "type": "none",
            "description": "Stateless mode (no conversation history)"
        }
    ]
    
    for memory_config in memory_configs:
        print(f"\n📋 Testing: {memory_config['name']}")
        print(f"📄 {memory_config['description']}")
        print("-" * 40)
        
        try:
            # Create client with specific memory configuration
            kwargs = {"memory_type": memory_config["type"]}
            if "storage_path" in memory_config:
                kwargs["storage_path"] = memory_config["storage_path"]
            
            client = LLMClientFactory.create_client_with_memory(config, **kwargs)
            
            print(f"✅ Provider: {client.provider_name}")
            print(f"🧠 Memory type: {memory_config['type']}")
            
            # Initialize and clean up
            await client.initialize()
            await client.cleanup()
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def demonstrate_persistent_clients():
    """Demonstrate persistent client creation."""
    
    print("\n\n🔗 Persistent Client Demo")
    print("=" * 60)
    
    config = {
        "LLM_MODEL": "claude-3-5-sonnet-20241022",  # Will auto-detect Anthropic
        "LLM_API_KEY": "sk-ant-test-key",
        "max_tokens": 1000,
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-jwt-token-here"
            }
        }
    }
    
    try:
        # Create persistent client
        persistent_client = LLMClientFactory.create_persistent_client(config)
        
        print(f"✅ Provider: {persistent_client.provider_name}")
        print(f"📝 Model: {persistent_client.model_name}")
        print(f"🔗 Is connected: {persistent_client.is_connected}")
        print(f"🆔 MCP Session ID: {persistent_client.mcp_session_id}")
        
        # Initialize
        await persistent_client.initialize()
        
        # Note: In a real scenario, you would establish the persistent connection
        # await persistent_client.establish_persistent_connection()
        
        # Clean up
        await persistent_client.cleanup()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_factory_info():
    """Show information about the factory and supported providers."""
    
    print("\n\n📊 Factory Information")
    print("=" * 60)
    
    print("🔧 Supported Providers:")
    for provider in LLMClientFactory.get_supported_providers():
        print(f"  • {provider}")
    
    print("\n🔍 Provider Detection Patterns:")
    provider_info = LLMClientFactory.get_provider_info()
    for provider, info in provider_info.items():
        print(f"\n  {provider.upper()}:")
        print(f"    Model patterns: {info['model_patterns']}")
        print(f"    API key patterns: {info['api_key_patterns']}")
        print(f"    Client class: {info['client_class']}")
        print(f"    Persistent class: {info['persistent_client_class']}")

async def main():
    """Run all demonstrations."""
    
    print("🚀 viaNexus Unified LLM Client Factory Demo")
    print("=" * 60)
    print("This demo shows how to use the factory pattern to create")
    print("LLM clients automatically based on configuration.")
    print()
    
    # Show factory information
    show_factory_info()
    
    # Run demonstrations
    await demonstrate_auto_detection()
    await demonstrate_explicit_provider()
    await demonstrate_memory_configurations()
    await demonstrate_persistent_clients()
    
    print("\n\n🎉 Demo completed!")
    print("=" * 60)
    print("The LLMClientFactory provides a unified interface for all LLM providers.")
    print("Use it to create clients without worrying about specific implementations!")

if __name__ == "__main__":
    asyncio.run(main())
