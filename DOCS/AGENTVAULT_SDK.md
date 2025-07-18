# AgentVault Server SDK Documentation

## Overview

The AgentVault Server SDK provides the foundation for building A2A (Agent-to-Agent) protocol compliant agents within the Sovereign Stack ecosystem. It offers a complete framework for agent development, including base classes, FastAPI integration, state management, and Docker packaging utilities.

## Core Components

### 1. BaseA2AAgent Abstract Class

The heart of the SDK is the `BaseA2AAgent` abstract class that defines the interface all agents must implement:

```python
from agentvault_server_sdk import BaseA2AAgent
from agentvault.models import Message, Task

class MyAgent(BaseA2AAgent):
    async def handle_task_send(self, task_id: Optional[str], message: Message) -> str:
        # Process incoming messages
        pass
    
    async def handle_task_get(self, task_id: str) -> Task:
        # Return current task state
        pass
    
    async def handle_task_cancel(self, task_id: str) -> bool:
        # Cancel a running task
        pass
    
    async def handle_subscribe_request(self, task_id: str) -> AsyncGenerator[A2AEvent, None]:
        # Stream real-time events
        pass
```

### 2. FastAPI Integration

The SDK provides seamless FastAPI integration through the `create_a2a_router` function:

```python
from fastapi import FastAPI
from agentvault_server_sdk import create_a2a_router, BaseA2AAgent

app = FastAPI()
agent = MyAgent()
router = create_a2a_router(agent, prefix="/a2a", tags=["Agent API"])
app.include_router(router)
```

### 3. State Management

Built-in task state management with event notification support:

```python
from agentvault_server_sdk import InMemoryTaskStore, TaskContext

# Create task store
task_store = InMemoryTaskStore()

# Create and manage tasks
task_context = await task_store.create_task("task_123")
await task_store.update_task_state("task_123", TaskState.WORKING)

# Notifications are automatically sent to subscribers
```

### 4. Docker Packaging

The SDK includes a CLI tool for generating Docker artifacts:

```bash
agentvault-sdk package \
    --output-dir ./build \
    --entrypoint my_agent.main:app \
    --agent-card ./agent-card.json \
    --python 3.11
```

## Key Features

### JSON-RPC Protocol Support

All agent endpoints follow the JSON-RPC 2.0 specification:
- Standardized request/response format
- Proper error handling with specific error codes
- Method-based routing (tasks/send, tasks/get, etc.)

### Server-Sent Events (SSE)

Real-time event streaming for task progress:
- Status updates
- Message events  
- Artifact updates
- Automatic error handling and reconnection support

### Decorator-Based Method Mapping

Custom method handlers using the `@a2a_method` decorator:

```python
from agentvault_server_sdk import a2a_method

class MyAgent(BaseA2AAgent):
    @a2a_method("custom/analyze")
    async def analyze_data(self, data: dict, options: dict = None) -> dict:
        # Custom analysis logic
        return {"result": "analysis_complete"}
```

### Comprehensive Error Handling

Built-in exception classes for common scenarios:
- `TaskNotFoundError` - Task doesn't exist
- `InvalidStateTransitionError` - Invalid state change
- `AgentProcessingError` - Processing failures
- `ConfigurationError` - Configuration issues

## Architecture

### Request Flow

1. **Client Request** → JSON-RPC over HTTP POST
2. **Router** → Validates and routes to appropriate handler
3. **Agent Handler** → Processes request using BaseA2AAgent methods
4. **State Store** → Updates task state and notifies listeners
5. **Response** → JSON-RPC response or SSE stream

### Task Lifecycle

```
SUBMITTED → WORKING → INPUT_REQUIRED ↔ WORKING
                    ↓
                COMPLETED / FAILED / CANCELED
```

### Event System

The SDK uses an event-driven architecture for real-time updates:

1. **Event Generation**: State changes trigger events
2. **Event Queue**: Events are queued for each subscriber
3. **SSE Streaming**: Events are formatted and streamed to clients
4. **Error Recovery**: Failed streams are automatically cleaned up

## Best Practices

### 1. State Management

- Always use the provided task store for state consistency
- Handle state transitions carefully to avoid invalid states
- Store messages and artifacts in the task context

### 2. Error Handling

- Raise appropriate SDK exceptions for clear error messages
- Use try-catch blocks in handler methods
- Log errors for debugging while returning clean responses

### 3. Async Patterns

- Use async/await throughout for non-blocking operations
- Leverage asyncio for concurrent task processing
- Stream events efficiently without blocking

### 4. Docker Deployment

- Include all dependencies in requirements.txt
- Use the SDK packager for consistent container builds
- Follow security best practices (non-root user, minimal base image)

## Integration with Sovereign Stack

The SDK integrates seamlessly with other Sovereign Stack components:

- **Registry**: Agents register using SDK-generated metadata
- **TEG Layer**: Economic transactions through SDK interfaces
- **Identity Fabric**: Automatic SPIFFE/SPIRE integration
- **Federation**: Cross-registry agent discovery

## Migration Guide

### From Custom Implementation

1. Extend `BaseA2AAgent` instead of custom base class
2. Implement the four required handler methods
3. Replace custom routing with `create_a2a_router`
4. Use `InMemoryTaskStore` or implement `BaseTaskStore`

### Version Compatibility

- SDK 1.0.0 requires AgentVault Library 1.0.0+
- Python 3.10-3.11 supported
- FastAPI 0.111+ required

## Advanced Topics

### Custom Task Stores

Implement `BaseTaskStore` for persistent storage:

```python
class PostgresTaskStore(BaseTaskStore):
    async def get_task(self, task_id: str) -> Optional[TaskContext]:
        # Query PostgreSQL
        pass
    
    # Implement other required methods
```

### Authentication Integration

Add auth dependencies to the router:

```python
from fastapi import Depends

async def verify_token(token: str = Depends(oauth2_scheme)):
    # Verify JWT token
    pass

router = create_a2a_router(
    agent,
    dependencies=[Depends(verify_token)]
)
```

### Performance Optimization

- Use connection pooling for external services
- Implement caching for frequently accessed data
- Stream large artifacts instead of loading into memory
- Use background tasks for long-running operations

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure agentvault library is installed
2. **State Transition Errors**: Check ALLOWED_TRANSITIONS
3. **SSE Connection Drops**: Implement client-side reconnection
4. **Docker Build Failures**: Verify requirements.txt format

### Debug Logging

Enable detailed logging:

```python
import logging
logging.getLogger("agentvault_server_sdk").setLevel(logging.DEBUG)
```

## Example Implementation

See the echo agent examples in the Sovereign Stack repository for complete working implementations using the SDK.
