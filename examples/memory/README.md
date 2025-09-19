# Enhanced Session Isolation Memory System

## Overview

This directory contains examples and demonstrations of the enhanced session isolation memory system for the viaNexus Agent SDK. The system guarantees **complete session isolation** with **unique session IDs** and **cross-client retrieval capabilities**.

## Key Features

### 🔒 **Guaranteed Session Isolation**
- Each session has a **guaranteed unique session ID**
- **Complete message isolation** between sessions
- **No data leakage** between different conversations
- **Thread-safe session management**

### 🆔 **Unique Session ID Generation**
```
Format: {client_type}_{user_id}_{context}_{timestamp}_{unique_id}
Example: anthropic_trader_001_portfolio_analysis_20250919_151018_ec8780d3
```

### 🔄 **Cross-Client Session Retrieval**
- Sessions can be **retrieved by ID** across different client instances
- **Same user** can access their sessions from any client
- **Seamless session switching** with guaranteed data integrity

### 📋 **Session Cloning & Branching**
- **Clone conversations** for backup or alternative paths
- **Branch conversations** to explore different scenarios
- **Maintain conversation history** while allowing divergence

## Examples

### 1. **Basic Memory Usage** (`basic_memory_example.py`)
Demonstrates fundamental memory operations:
- In-memory and file-based storage
- Session creation and management
- Message persistence and retrieval

### 2. **Cross-Client Conversation** (`cross_client_conversation.py`)
Shows provider-agnostic memory:
- Same conversation across Anthropic and Gemini clients
- Session sharing between different LLM providers
- Universal message format compatibility

### 3. **Session Isolation Demo** (`session_isolation_demo.py`)
Comprehensive demonstration of enhanced features:
- Guaranteed session isolation
- Session retrieval by ID
- Session cloning and branching
- Advanced session statistics

### 4. **S3 Memory Store** (`s3_memory_example.py`)
Production-ready S3 implementation template:
- Scalable cloud storage
- Enterprise-grade persistence
- Cost-effective lifecycle management

## Usage Patterns

### **Creating Isolated Sessions**
```python
client = AnthropicClient(config, memory_store=store, user_id="user_001")

# Create isolated session with context
session_id = await client.memory_create_isolated_session(
    session_context="portfolio_analysis",
    context_tags=["finance", "portfolio"],
    session_metadata={"department": "trading"}
)
```

### **Retrieving Sessions by ID**
```python
# Client A creates session
session_id = await client_a.memory_create_isolated_session("analysis")

# Client B retrieves same session
client_b = AnthropicClient(config, memory_store=store, user_id="user_001")
await client_b.memory_switch_session(session_id, create_if_not_exists=False)

# Both clients now share the same isolated conversation
```

### **Session Cloning**
```python
# Clone current session for alternative path
cloned_id = await client.memory_clone_current_session(
    new_session_context="conservative_variant"
)

# Continue original conversation
await client.ask_question("Let's be aggressive", maintain_history=True)

# Switch to clone for different approach
await client.memory_switch_session(cloned_id)
await client.ask_question("Let's be conservative", maintain_history=True)
```

## Architecture Benefits

### 🛡️ **Isolation Guarantees**
- **Memory safety**: No session can access another's data
- **User privacy**: Complete separation of user conversations
- **Data integrity**: Messages cannot leak between sessions

### ⚡ **Performance**
- **Session caching**: Active sessions cached for fast access
- **Lazy loading**: Messages loaded on demand
- **Efficient storage**: Optimized for both memory and disk usage

### 🔧 **Reliability**
- **Session locks**: Prevent concurrent modification conflicts
- **Error recovery**: Graceful handling of session failures
- **Data validation**: Comprehensive checks for data integrity

### 📊 **Observability**
- **Session statistics**: Detailed metrics for each session
- **Usage tracking**: Monitor session activity and performance
- **Debug information**: Comprehensive logging for troubleshooting

## Storage Backends

### **In-Memory Store** (`InMemoryStore`)
- **Fast**: Optimal for development and testing
- **Volatile**: Data lost when process ends
- **Thread-safe**: Supports concurrent access

### **File-Based Store** (`FileMemoryStore`)
- **Persistent**: Data survives application restarts
- **Local**: Stores data in local filesystem
- **JSONL format**: Human-readable and efficient

### **S3 Store** (`S3MemoryStore`)
- **Scalable**: Handles enterprise-scale data
- **Durable**: AWS guarantees 99.999999999% durability
- **Cost-effective**: Automatic lifecycle management

## Session ID Format

The system generates guaranteed unique session IDs using this format:

```
{client_type}_{user_id}_{context}_{timestamp}_{unique_id}
```

**Components:**
- `client_type`: LLM provider (anthropic, gemini, etc.)
- `user_id`: User identifier
- `context`: Session context/purpose (optional)
- `timestamp`: Creation timestamp (YYYYMMDD_HHMMSS)
- `unique_id`: 8-character hex UUID

**Example:**
```
anthropic_trader_001_portfolio_analysis_20250919_151018_ec8780d3
```

## Running Examples

### Prerequisites
```bash
# Install dependencies
uv add aiofiles

# Activate virtual environment
source .venv/bin/activate
```

### Run Examples
```bash
# Basic memory functionality
python examples/memory/basic_memory_example.py

# Cross-client conversation
python examples/memory/cross_client_conversation.py

# Enhanced session isolation
python examples/memory/session_isolation_demo.py

# S3 storage template
python examples/memory/s3_memory_example.py
```

## Integration Guide

### **1. Add Memory to Any Client**
```python
from vianexus_agent_sdk.memory import ConversationMemoryMixin

class MyLLMClient(ConversationMemoryMixin):
    def __init__(self, config, memory_store=None, **kwargs):
        ConversationMemoryMixin.__init__(
            self, 
            memory_store=memory_store,
            provider_name="my_provider",
            **kwargs
        )
        # Your client initialization...
```

### **2. Use Enhanced Session Management**
```python
from vianexus_agent_sdk.memory import SessionManager

# Create session manager
session_manager = SessionManager(memory_store)

# Create isolated session
session = await session_manager.create_session(
    user_id="user_001",
    client_type="my_provider"
)

# Get session statistics
stats = await session_manager.get_session_statistics(session.session_id)
```

### **3. Configure Memory Policies**
```python
client.configure_memory(
    auto_persist=True,
    max_context_messages=1000,
    guarantee_isolation=True
)
```

## Best Practices

### **Session Naming**
- Use **descriptive contexts** for session identification
- Include **purpose** and **scope** in context tags
- Add **metadata** for filtering and organization

### **Memory Management**
- **Clean up old sessions** regularly
- **Monitor session sizes** to prevent memory bloat
- **Use appropriate storage** for your scale (in-memory → file → S3)

### **Error Handling**
- **Check session existence** before switching
- **Handle session creation failures** gracefully
- **Log session operations** for debugging

### **Performance**
- **Batch message operations** when possible
- **Use session statistics** to monitor usage
- **Implement cleanup policies** for inactive sessions

## Security Considerations

### **Data Isolation**
- Sessions are **completely isolated** by design
- **No cross-session data access** is possible
- **User sessions are private** to that user

### **Session Access**
- **Session IDs are not guessable** (UUID-based)
- **User ID verification** prevents unauthorized access
- **Session locks** prevent concurrent modification

### **Storage Security**
- **Encrypted storage** recommended for production
- **Access controls** on storage backends
- **Audit logging** for compliance requirements

## Troubleshooting

### **Common Issues**

1. **Session Not Found**
   - Verify session ID is correct
   - Check if session was deleted
   - Ensure memory store is connected

2. **Memory Leaks**
   - Monitor session cache size
   - Implement cleanup policies
   - Use appropriate storage backend

3. **Performance Issues**
   - Check session sizes
   - Optimize message filtering
   - Consider storage backend upgrade

### **Debug Information**
```python
# Get comprehensive session info
info = client.memory_get_current_session_info()

# Get session statistics
stats = await client.memory_get_session_statistics()

# Get complete session data
data = await client.memory_get_isolated_session_data()
```

## Future Enhancements

- **Redis backend** for high-performance caching
- **MongoDB backend** for document-oriented storage
- **Encryption at rest** for sensitive data
- **Session search** across conversation content
- **Analytics dashboard** for session insights
