#!/usr/bin/env python3
"""
Real-World Unified LLM Client Usage Example

This example demonstrates practical, real-world usage patterns of the
unified LLM client factory, including error handling, logging, and
production-ready patterns.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from vianexus_agent_sdk import LLMClientFactory, LLMProvider, BaseLLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMService:
    """
    A production-ready service class that uses the unified LLM client factory.
    
    This class demonstrates how to build a robust service layer on top of
    the factory pattern, with features like:
    - Configuration management
    - Error handling and retries
    - Logging and monitoring
    - Client lifecycle management
    - Graceful degradation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[BaseLLMClient] = None
        self.provider_name: Optional[str] = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the LLM service with automatic provider detection and fallback.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing LLM service...")
            
            # Create client using factory
            self.client = LLMClientFactory.create_client(self.config)
            self.provider_name = self.client.provider_name
            
            # Initialize the client
            await self.client.initialize()
            
            self.is_initialized = True
            logger.info(f"LLM service initialized successfully with {self.provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            return False
    
    async def ask_question(
        self, 
        question: str, 
        use_memory: bool = True,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Ask a question with retry logic and error handling.
        
        Args:
            question: The question to ask
            use_memory: Whether to use conversation memory
            max_retries: Maximum number of retry attempts
            
        Returns:
            The response string or None if all attempts failed
        """
        if not self.is_initialized or not self.client:
            logger.error("LLM service not initialized")
            return None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Asking question (attempt {attempt + 1}/{max_retries})")
                
                response = await self.client.ask_question(
                    question=question,
                    maintain_history=use_memory,
                    use_memory=use_memory
                )
                
                logger.info(f"Question answered successfully by {self.provider_name}")
                return response
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed")
                    return None
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        return None
    
    async def batch_questions(
        self, 
        questions: List[str], 
        use_memory: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process multiple questions in batch with detailed results.
        
        Args:
            questions: List of questions to process
            use_memory: Whether to maintain conversation context across questions
            
        Returns:
            List of result dictionaries with question, response, and metadata
        """
        results = []
        
        logger.info(f"Processing batch of {len(questions)} questions")
        
        for i, question in enumerate(questions, 1):
            start_time = datetime.now()
            
            logger.info(f"Processing question {i}/{len(questions)}")
            
            response = await self.ask_question(question, use_memory=use_memory)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "question_id": i,
                "question": question,
                "response": response,
                "success": response is not None,
                "provider": self.provider_name,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }
            
            results.append(result)
            
            if response:
                logger.info(f"Question {i} completed in {duration:.2f}s")
            else:
                logger.error(f"Question {i} failed after {duration:.2f}s")
        
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Batch completed: {success_count}/{len(questions)} successful")
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the LLM service.
        
        Returns:
            Health check results
        """
        health_status = {
            "service": "LLM Service",
            "status": "unknown",
            "provider": self.provider_name,
            "initialized": self.is_initialized,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.is_initialized or not self.client:
            health_status["status"] = "unhealthy"
            health_status["error"] = "Service not initialized"
            return health_status
        
        try:
            # Test with a simple question
            test_response = await self.client.ask_single_question("Hello, are you working?")
            
            if test_response:
                health_status["status"] = "healthy"
                health_status["test_response_length"] = len(test_response)
            else:
                health_status["status"] = "unhealthy"
                health_status["error"] = "No response to test question"
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get detailed service information."""
        info = {
            "service": "LLM Service",
            "provider": self.provider_name,
            "initialized": self.is_initialized,
            "supported_providers": LLMClientFactory.get_supported_providers(),
            "provider_detection_patterns": LLMClientFactory.get_provider_info()
        }
        
        if self.client:
            info.update({
                "model_name": getattr(self.client, 'model_name', 'unknown'),
                "system_prompt": getattr(self.client, 'system_prompt', 'unknown')[:100] + "...",
                "memory_enabled": hasattr(self.client, 'memory_enabled') and getattr(self.client, 'memory_enabled', False)
            })
        
        return info
    
    async def cleanup(self):
        """Clean up service resources."""
        if self.client:
            try:
                await self.client.cleanup()
                logger.info("LLM service cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        self.is_initialized = False
        self.client = None
        self.provider_name = None

async def demonstrate_production_service():
    """Demonstrate the production-ready LLM service."""
    
    print("🏭 Production LLM Service Demo")
    print("=" * 50)
    
    # Production-like configuration
    config = {
        "LLM_MODEL": "gpt-4o-mini",  # Will auto-detect OpenAI
        "LLM_API_KEY": "sk-your-production-api-key",
        "max_tokens": 2000,
        "system_prompt": "You are a professional AI assistant for a financial services company.",
        "agentServers": {
            "viaNexus": {
                "server_url": "https://api.vianexus.com",
                "server_port": 443,
                "software_statement": "your-production-jwt-token"
            }
        }
    }
    
    # Create and initialize service
    service = LLMService(config)
    
    try:
        # Initialize service
        print("\n🚀 Initializing LLM service...")
        success = await service.initialize()
        
        if not success:
            print("❌ Service initialization failed")
            return
        
        # Get service info
        print("\n📊 Service Information:")
        info = await service.get_service_info()
        print(json.dumps(info, indent=2))
        
        # Health check
        print("\n🏥 Health Check:")
        health = await service.health_check()
        print(json.dumps(health, indent=2))
        
        # Single question
        print("\n❓ Single Question Test:")
        response = await service.ask_question(
            "What are the key factors to consider when evaluating a company's financial health?"
        )
        if response:
            print(f"✅ Response: {response[:200]}...")
        else:
            print("❌ No response received")
        
        # Batch questions
        print("\n📦 Batch Questions Test:")
        questions = [
            "What is diversification in investment?",
            "Explain the concept of compound interest.",
            "What are the main types of financial statements?"
        ]
        
        batch_results = await service.batch_questions(questions, use_memory=True)
        
        print(f"\n📊 Batch Results Summary:")
        for result in batch_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} Q{result['question_id']}: {result['duration_seconds']:.2f}s")
        
        # Final health check
        print("\n🏥 Final Health Check:")
        final_health = await service.health_check()
        print(f"Status: {final_health['status']}")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo failed: {e}")
    
    finally:
        # Always clean up
        await service.cleanup()
        print("🧹 Service cleaned up")

async def demonstrate_multi_provider_service():
    """Demonstrate a service that can work with multiple providers."""
    
    print("\n\n🔄 Multi-Provider Service Demo")
    print("=" * 50)
    
    # Configurations for different providers
    provider_configs = {
        "primary": {
            "LLM_MODEL": "gpt-4o-mini",
            "LLM_API_KEY": "sk-openai-key",
            "max_tokens": 1500,
            "agentServers": {
                "viaNexus": {
                    "server_url": "https://api.vianexus.com",
                    "server_port": 443,
                    "software_statement": "jwt-token"
                }
            }
        },
        "fallback": {
            "LLM_MODEL": "claude-3-5-sonnet-20241022",
            "LLM_API_KEY": "sk-ant-anthropic-key",
            "max_tokens": 1500,
            "agentServers": {
                "viaNexus": {
                    "server_url": "https://api.vianexus.com",
                    "server_port": 443,
                    "software_statement": "jwt-token"
                }
            }
        },
        "backup": {
            "LLM_MODEL": "gemini-2.5-flash",
            "LLM_API_KEY": "gemini-key",
            "max_tokens": 1500,
            "agentServers": {
                "viaNexus": {
                    "server_url": "https://api.vianexus.com",
                    "server_port": 443,
                    "software_statement": "jwt-token"
                }
            }
        }
    }
    
    services = {}
    
    # Initialize all services
    for name, config in provider_configs.items():
        print(f"\n🚀 Initializing {name} service...")
        service = LLMService(config)
        
        if await service.initialize():
            services[name] = service
            print(f"✅ {name} service ready ({service.provider_name})")
        else:
            print(f"❌ {name} service failed")
    
    if services:
        print(f"\n🎯 Successfully initialized {len(services)} services")
        
        # Test question with all services
        test_question = "What is the time value of money?"
        
        for name, service in services.items():
            print(f"\n📋 Testing {name} service ({service.provider_name}):")
            response = await service.ask_question(test_question)
            if response:
                print(f"✅ Response length: {len(response)} characters")
            else:
                print("❌ No response")
    
    # Clean up all services
    for name, service in services.items():
        await service.cleanup()
        print(f"🧹 Cleaned up {name} service")

async def main():
    """Run all real-world usage demonstrations."""
    
    print("🚀 Real-World Unified LLM Client Usage Demo")
    print("=" * 60)
    print("This demo shows production-ready patterns for using the")
    print("unified LLM client factory in real applications.")
    print()
    
    await demonstrate_production_service()
    await demonstrate_multi_provider_service()
    
    print("\n\n🎉 Real-world usage demo completed!")
    print("=" * 60)
    print("Key patterns demonstrated:")
    print("  • Service layer abstraction")
    print("  • Error handling and retries")
    print("  • Health checks and monitoring")
    print("  • Batch processing")
    print("  • Multi-provider support")
    print("  • Graceful cleanup")

if __name__ == "__main__":
    asyncio.run(main())
