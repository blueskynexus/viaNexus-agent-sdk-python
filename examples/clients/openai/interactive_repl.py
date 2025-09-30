#!/usr/bin/env python3
"""
OpenAI Client Interactive REPL Example

This example provides an interactive command-line interface
for chatting with the OpenAI client using the responses API.
"""

import asyncio
import logging
import sys
import os
import signal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from vianexus_agent_sdk.clients.openai_client import OpenAiClient, PersistentOpenAiClient

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise in interactive mode

class OpenAIREPL:
    """Interactive REPL for OpenAI client"""
    
    def __init__(self):
        self.client = None
        self.persistent_client = None
        self.session_id = None
        self.running = True
        
    async def setup_client(self, mode="standard"):
        """Setup the OpenAI client based on mode"""
        config = {
            "LLM_API_KEY": os.getenv("OPENAI_API_KEY", "your-openai-api-key-here"),
            "LLM_MODEL": "gpt-4o-mini",
            "max_tokens": 2000,
            "system_prompt": """You are a helpful financial AI assistant with access to real-time market data. 
            You can help with investment analysis, market research, portfolio management, and financial planning.
            Be conversational and helpful, and use tools when you need current market data.""",
            "agentServers": {
                "viaNexus": {
                    "server_url": "https://api.vianexus.com",
                    "server_port": 443,
                    "software_statement": os.getenv("VIANEXUS_JWT", "your-jwt-token-here")
                }
            }
        }
        
        if mode == "persistent":
            self.persistent_client = PersistentOpenAiClient(config)
            self.client = self.persistent_client
            await self.client.initialize()
            self.session_id = await self.persistent_client.establish_persistent_connection()
            print(f"🔄 Persistent session established: {self.session_id}")
        else:
            self.client = OpenAiClient.with_in_memory_store(config, user_id="repl_user")
            await self.client.initialize()
            print("💭 Standard client with memory initialized")
    
    def print_help(self):
        """Print help information"""
        print("\n📚 Available Commands:")
        print("  /help     - Show this help message")
        print("  /history  - Show conversation history")
        print("  /clear    - Clear conversation history")
        print("  /tools    - List available tools")
        print("  /stats    - Show session statistics")
        print("  /quit     - Exit the REPL")
        print("  /exit     - Exit the REPL")
        print("\n💡 Tips:")
        print("  - Ask about stocks, market data, or financial analysis")
        print("  - The AI has access to real-time financial tools")
        print("  - Conversation history is maintained across questions")
        print("  - Use Ctrl+C to interrupt long responses")
        print()
    
    async def handle_command(self, command):
        """Handle special commands"""
        if command in ["/quit", "/exit"]:
            self.running = False
            return True
        
        elif command == "/help":
            self.print_help()
            return True
        
        elif command == "/history":
            if hasattr(self.client, 'messages') and self.client.messages:
                print(f"\n📜 Conversation History ({len(self.client.messages)} messages):")
                for i, msg in enumerate(self.client.messages, 1):
                    role_icon = "👤" if msg["role"] == "user" else "🤖"
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    print(f"  {i}. {role_icon} {content}")
            else:
                print("📜 No conversation history available")
            return True
        
        elif command == "/clear":
            if hasattr(self.client, 'messages'):
                self.client.messages.clear()
                print("🧹 Conversation history cleared")
            return True
        
        elif command == "/tools":
            try:
                tools = await self.client._get_available_tools()
                print(f"\n🛠️ Available Tools ({len(tools)}):")
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool['name']}: {tool['description']}")
                if not tools:
                    print("  No tools available")
            except Exception as e:
                print(f"❌ Error listing tools: {e}")
            return True
        
        elif command == "/stats":
            stats = {
                "Client Type": "Persistent" if self.persistent_client else "Standard",
                "Session ID": self.session_id or "N/A",
                "Model": getattr(self.client, 'model', 'Unknown'),
                "Messages": len(getattr(self.client, 'messages', [])),
                "Max Tokens": getattr(self.client, 'max_tokens', 'Unknown')
            }
            print("\n📊 Session Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            return True
        
        return False
    
    async def run_repl(self, mode="standard"):
        """Run the interactive REPL"""
        print("🚀 OpenAI Client Interactive REPL")
        print("=" * 40)
        print(f"Mode: {mode.upper()}")
        print("Type '/help' for commands or '/quit' to exit")
        print()
        
        try:
            await self.setup_client(mode)
            
            while self.running:
                try:
                    # Get user input
                    user_input = input("👤 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.startswith("/"):
                        await self.handle_command(user_input)
                        continue
                    
                    # Process regular questions
                    print("🤖 Assistant: ", end="", flush=True)
                    
                    if self.persistent_client:
                        # Use persistent session
                        response = await self.persistent_client.ask_with_persistent_session(user_input)
                        print(response)
                    else:
                        # Use standard client with history
                        response = await self.client.ask_question(user_input, maintain_history=True)
                        print(response)
                    
                    print()  # Add spacing
                    
                except KeyboardInterrupt:
                    print("\n⏸️ Interrupted. Type '/quit' to exit or continue chatting.")
                    continue
                except EOFError:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ Setup error: {e}")
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.persistent_client:
            await self.persistent_client.close_persistent_connection()
        if self.client:
            await self.client.cleanup()
        print("🧹 Cleaned up resources")

async def main():
    """Main function with mode selection"""
    print("🎯 Select OpenAI Client Mode:")
    print("1. Standard (with memory)")
    print("2. Persistent (long-running session)")
    
    while True:
        try:
            choice = input("Enter choice (1-2): ").strip()
            if choice == "1":
                mode = "standard"
                break
            elif choice == "2":
                mode = "persistent"
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            return
    
    # Setup signal handler for graceful shutdown
    repl = OpenAIREPL()
    
    def signal_handler(signum, frame):
        print("\n🛑 Received interrupt signal. Shutting down gracefully...")
        repl.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await repl.run_repl(mode)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
