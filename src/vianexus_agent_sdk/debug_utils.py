"""
Debugging utilities for troubleshooting persistent session and memory issues.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager


class PersistentSessionDebugger:
    """Comprehensive debugging utilities for persistent session issues."""
    
    def __init__(self, client):
        self.client = client
        self.debug_logs = []
    
    def log_debug(self, message: str, level: str = "INFO"):
        """Add debug message with timestamp."""
        timestamp = time.time()
        self.debug_logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        getattr(logging, level.lower())(f"[DEBUG] {message}")
    
    async def safe_ask_with_persistent_session(
        self, 
        question: str, 
        maintain_history: bool = True,
        use_memory: bool = True,
        auto_establish_connection: bool = True,
        max_retries: int = 3,
        timeout: int = 60
    ) -> str:
        """Ask question with comprehensive error handling and debugging."""
        
        # Pre-flight checks
        self.log_debug(f"Starting safe persistent session request - question length: {len(question)}")
        
        # Memory health check if enabled
        if use_memory:
            try:
                health_status = await self.client.memory_health_check()
                if not health_status["healthy"]:
                    self.log_debug(f"Memory health issues detected: {health_status['errors']}", "WARNING")
                    if health_status["errors"]:
                        self.log_debug("Memory system has errors - consider disabling memory for this request", "ERROR")
                else:
                    self.log_debug("Memory health check passed")
            except Exception as e:
                self.log_debug(f"Memory health check failed: {e}", "ERROR")
        
        for attempt in range(max_retries):
            try:
                self.log_debug(f"Attempt {attempt + 1}/{max_retries}: Processing question")
                start_time = time.time()
                
                # Check connection before asking
                if not self.client.is_connected:
                    self.log_debug("Connection not active, will auto-establish", "WARNING")
                
                # Execute with timeout
                response = await asyncio.wait_for(
                    self.client.ask_with_persistent_session(
                        question=question,
                        maintain_history=maintain_history,
                        use_memory=use_memory,
                        auto_establish_connection=auto_establish_connection
                    ),
                    timeout=timeout
                )
                
                # Validate response
                if response is None:
                    raise ValueError("Received None response")
                if not isinstance(response, str):
                    raise ValueError(f"Invalid response type: {type(response)}")
                if len(response.strip()) == 0:
                    raise ValueError("Received empty response")
                
                elapsed = time.time() - start_time
                self.log_debug(f"Success: Received response of length {len(response)} in {elapsed:.2f}s")
                return response
                
            except asyncio.TimeoutError:
                self.log_debug(f"Attempt {attempt + 1} timed out after {timeout} seconds", "ERROR")
                # Force connection reset on timeout
                try:
                    await self.client.close_persistent_connection()
                    self.log_debug("Closed connection after timeout")
                except Exception as close_e:
                    self.log_debug(f"Error closing connection after timeout: {close_e}", "ERROR")
                
            except Exception as e:
                self.log_debug(f"Attempt {attempt + 1} failed: {e}", "ERROR")
                
                # Log additional context for debugging
                self.log_debug(f"Connection status: {self.client.is_connected}")
                self.log_debug(f"MCP session ID: {self.client.mcp_session_id}")
                self.log_debug(f"Memory enabled: {self.client.memory_enabled}")
                
            if attempt == max_retries - 1:
                self.log_debug("All retry attempts failed", "ERROR")
                raise RuntimeError(f"Failed after {max_retries} attempts")
            
            # Exponential backoff
            wait_time = 2 ** attempt
            self.log_debug(f"Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)
        
        raise RuntimeError("Unexpected end of retry loop")
    
    async def monitor_connection_health(self, interval: int = 30, duration: int = 300):
        """Monitor connection health periodically."""
        self.log_debug(f"Starting connection monitoring for {duration}s with {interval}s intervals")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                is_connected = self.client.is_connected
                mcp_session_id = self.client.mcp_session_id
                
                self.log_debug(f"Connection status: connected={is_connected}, session_id={mcp_session_id}")
                
                if is_connected:
                    # Test actual connectivity
                    health_ok = await self.client._verify_connection_health()
                    self.log_debug(f"Health check result: {health_ok}")
                    
                    if not health_ok:
                        self.log_debug("Health check failed - connection may be stale", "WARNING")
                
            except Exception as e:
                self.log_debug(f"Connection monitoring error: {e}", "ERROR")
            
            await asyncio.sleep(interval)
        
        self.log_debug("Connection monitoring completed")
    
    async def test_memory_operations(self):
        """Test memory operations comprehensively."""
        self.log_debug("Starting comprehensive memory operations test")
        
        if not self.client.memory_enabled:
            self.log_debug("Memory is disabled - skipping memory tests", "WARNING")
            return
        
        try:
            # Test basic save/load cycle
            test_data = [
                ("user", "Test user message 1"),
                ("assistant", "Test assistant response 1"),
                ("user", "Test user message 2"),
                ("assistant", "Test assistant response 2")
            ]
            
            # Save test messages
            for role, content in test_data:
                success = await self.client.memory_save_message(role, content)
                self.log_debug(f"Save {role} message: {'SUCCESS' if success else 'FAILED'}")
            
            # Load messages back
            messages = await self.client.memory_load_history(limit=10)
            self.log_debug(f"Loaded {len(messages)} messages from memory")
            
            # Test session isolation
            original_session = self.client.memory_session_id
            self.client.memory_session_id = f"test_session_{int(time.time())}"
            
            isolated_messages = await self.client.memory_load_history(limit=10)
            self.log_debug(f"Isolated session has {len(isolated_messages)} messages")
            
            # Restore original session
            self.client.memory_session_id = original_session
            
            self.log_debug("Memory operations test completed successfully")
            
        except Exception as e:
            self.log_debug(f"Memory operations test failed: {e}", "ERROR")
    
    def get_debug_report(self) -> Dict[str, Any]:
        """Generate comprehensive debug report."""
        return {
            "client_info": {
                "provider": self.client.provider_name,
                "model": getattr(self.client, 'model', 'unknown'),
                "memory_enabled": self.client.memory_enabled,
                "memory_session_id": self.client.memory_session_id,
                "user_id": self.client.user_id,
                "is_connected": self.client.is_connected,
                "mcp_session_id": getattr(self.client, 'mcp_session_id', None)
            },
            "debug_logs": self.debug_logs,
            "log_count": len(self.debug_logs),
            "error_count": len([log for log in self.debug_logs if log["level"] == "ERROR"]),
            "warning_count": len([log for log in self.debug_logs if log["level"] == "WARNING"])
        }
    
    def print_debug_report(self):
        """Print formatted debug report."""
        report = self.get_debug_report()
        
        print("\n" + "="*60)
        print("PERSISTENT SESSION DEBUG REPORT")
        print("="*60)
        
        print("\nClient Information:")
        for key, value in report["client_info"].items():
            print(f"  {key}: {value}")
        
        print(f"\nLog Summary:")
        print(f"  Total logs: {report['log_count']}")
        print(f"  Errors: {report['error_count']}")
        print(f"  Warnings: {report['warning_count']}")
        
        if report["error_count"] > 0:
            print(f"\nRecent Errors:")
            error_logs = [log for log in self.debug_logs if log["level"] == "ERROR"][-5:]
            for log in error_logs:
                print(f"  [{log['timestamp']:.2f}] {log['message']}")
        
        print("\n" + "="*60)


@asynccontextmanager
async def debug_persistent_session(client, enable_monitoring: bool = False):
    """Context manager for debugging persistent sessions."""
    debugger = PersistentSessionDebugger(client)
    
    # Start monitoring if requested
    monitor_task = None
    if enable_monitoring:
        monitor_task = asyncio.create_task(debugger.monitor_connection_health())
    
    try:
        yield debugger
    finally:
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        
        # Print final debug report
        debugger.print_debug_report()


# Usage example functions
async def debug_memory_issues(client):
    """Debug memory-related issues."""
    debugger = PersistentSessionDebugger(client)
    
    print("🔍 Starting Memory Debugging Session")
    print("="*50)
    
    # Run memory health check
    try:
        health_status = await client.memory_health_check()
        print(f"\n📊 Memory Health Status:")
        for key, value in health_status.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Memory health check failed: {e}")
    
    # Test memory operations
    await debugger.test_memory_operations()
    
    # Print debug report
    debugger.print_debug_report()


async def debug_connection_issues(client, test_question: str = "Hello, can you hear me?"):
    """Debug connection-related issues."""
    async with debug_persistent_session(client, enable_monitoring=True) as debugger:
        print("🔍 Starting Connection Debugging Session")
        print("="*50)
        
        try:
            response = await debugger.safe_ask_with_persistent_session(test_question)
            print(f"\n✅ Successfully received response: {response[:100]}...")
        except Exception as e:
            print(f"\n❌ Failed to get response: {e}")


if __name__ == "__main__":
    # Example usage
    print("This is a utility module. Import and use the debugging functions in your code.")
    print("\nExample usage:")
    print("""
    from vianexus_agent_sdk.debug_utils import debug_memory_issues, debug_connection_issues
    
    # Debug memory issues
    await debug_memory_issues(your_client)
    
    # Debug connection issues
    await debug_connection_issues(your_client, "Test question")
    
    # Use safe wrapper
    async with debug_persistent_session(your_client) as debugger:
        response = await debugger.safe_ask_with_persistent_session("Your question")
    """)
