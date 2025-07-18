# Building an Agent

## Overview

Building an agent in the AgentVault ecosystem means creating an autonomous service that can communicate via the Agent-to-Agent (A2A) protocol. This guide walks through creating your first agent using the AgentVault Server SDK, from basic setup to advanced features.

## Prerequisites

- Python 3.10 or 3.11
- Basic understanding of async/await patterns
- Familiarity with FastAPI (helpful but not required)
- AgentVault SDK installed:
  ```bash
  pip install agentvault-server-sdk agentvault
  ```

## Core Concepts

### The A2A Protocol

The Agent-to-Agent protocol defines how agents communicate:
- **JSON-RPC 2.0**: All messages use JSON-RPC format
- **Task-based**: Interactions are organized as tasks with unique IDs
- **Streaming**: Support for Server-Sent Events (SSE) for real-time updates
- **Stateful**: Tasks maintain state throughout their lifecycle

### Task Lifecycle

```
1. SUBMITTED → 2. WORKING → 3. INPUT_REQUIRED → 4. COMPLETED
   (Created)     (Processing)   (Optional)        (Finished)
                                                  
Alternative endings: FAILED, CANCELED
```

## Quick Start: Echo Agent

Let's build a simple echo agent that repeats back messages.

### Step 1: Create Your Agent Class

```python
from typing import Optional, AsyncGenerator
import uuid
import asyncio
from agentvault_server_sdk import BaseA2AAgent
from agentvault.models import Message, Task, TaskState, A2AEvent

class EchoAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__(agent_metadata={
            "name": "Echo Agent",
            "version": "1.0.0",
            "capabilities": ["echo"]
        })
        self.active_tasks = {}
```

### Step 2: Implement Required Methods

#### Handle Task Send

This method receives new messages and manages task creation:

```python
async def handle_task_send(
    self, 
    task_id: Optional[str], 
    message: Message
) -> str:
    # Generate task ID if new task
    if task_id is None:
        task_id = f"echo_{uuid.uuid4().hex[:8]}"
        self.active_tasks[task_id] = {
            "status": TaskState.SUBMITTED,
            "messages": [],
            "original_text": ""
        }
    
    # Store the message
    task_data = self.active_tasks.get(task_id)
    if not task_data:
        raise TaskNotFoundError(task_id)
    
    task_data["messages"].append(message)
    
    # Extract text content
    text_content = ""
    for part in message.parts:
        if hasattr(part, 'content'):
            text_content += part.content
    
    task_data["original_text"] = text_content
    task_data["status"] = TaskState.WORKING
    
    # Start async processing
    asyncio.create_task(self._process_echo(task_id))
    
    return task_id
```

#### Handle Task Get

Return the current state of a task:

```python
async def handle_task_get(self, task_id: str) -> Task:
    task_data = self.active_tasks.get(task_id)
    if not task_data:
        raise TaskNotFoundError(task_id)
    
    return Task(
        id=task_id,
        state=task_data["status"],
        messages=task_data["messages"],
        artifacts=task_data.get("artifacts", [])
    )
```

#### Handle Task Cancel

Allow task cancellation:

```python
async def handle_task_cancel(self, task_id: str) -> bool:
    task_data = self.active_tasks.get(task_id)
    if not task_data:
        raise TaskNotFoundError(task_id)
    
    # Only cancel if not completed
    if task_data["status"] not in [
        TaskState.COMPLETED, 
        TaskState.FAILED, 
        TaskState.CANCELED
    ]:
        task_data["status"] = TaskState.CANCELED
        task_data["cancel_requested"] = True
        return True
    
    return False
```

#### Handle Subscribe Request

Stream real-time updates via SSE:

```python
async def handle_subscribe_request(
    self, 
    task_id: str
) -> AsyncGenerator[A2AEvent, None]:
    task_data = self.active_tasks.get(task_id)
    if not task_data:
        raise TaskNotFoundError(task_id)
    
    # Create event queue for this subscriber
    event_queue = asyncio.Queue()
    task_data.setdefault("subscribers", []).append(event_queue)
    
    try:
        # Send initial status
        yield TaskStatusUpdateEvent(
            taskId=task_id,
            state=task_data["status"],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Stream events as they occur
        while True:
            event = await event_queue.get()
            yield event
            
            # Stop if task is complete
            if isinstance(event, TaskStatusUpdateEvent):
                if event.state in [
                    TaskState.COMPLETED,
                    TaskState.FAILED,
                    TaskState.CANCELED
                ]:
                    break
    finally:
        # Clean up subscriber
        task_data["subscribers"].remove(event_queue)
```

### Step 3: Create FastAPI Application

```python
from fastapi import FastAPI
from agentvault_server_sdk import create_a2a_router

# Create app
app = FastAPI(
    title="Echo Agent API",
    description="A2A compliant echo service",
    version="1.0.0"
)

# Initialize agent
agent = EchoAgent()

# Create A2A router
a2a_router = create_a2a_router(
    agent,
    prefix="/a2a",
    tags=["Echo Agent"]
)

# Include router
app.include_router(a2a_router)

# Add health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "echo"}
```

### Step 4: Create Agent Card

Create `agent-card.json` to describe your agent:

```json
{
  "schemaVersion": "1.0",
  "name": "Echo Agent",
  "description": "Simple agent that echoes messages back",
  "humanReadableId": "examples/echo-agent",
  "url": "https://echo-agent.example.com/a2a",
  "authSchemes": [
    {
      "scheme": "apiKey",
      "serviceIdentifier": "echo-agent"
    }
  ],
  "capabilities": {
    "a2aVersion": "0.2",
    "supportedMessageParts": ["text"],
    "supportsEventStream": true,
    "supportsCancellation": true
  },
  "tags": ["example", "echo", "tutorial"],
  "creator": {
    "name": "AgentVault Tutorial",
    "url": "https://docs.agentvault.com"
  }
}
```

## Advanced Agent Development

### Using the Task Store

Instead of managing state manually, use the built-in task store for better reliability:

```python
from agentvault_server_sdk import InMemoryTaskStore

class ImprovedEchoAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__()
        self.task_store = InMemoryTaskStore()
    
    async def handle_task_send(
        self, 
        task_id: Optional[str], 
        message: Message
    ) -> str:
        # Create task if new
        if task_id is None:
            task_id = f"echo_{uuid.uuid4().hex[:8]}"
            await self.task_store.create_task(task_id)
        
        # Store message
        await self.task_store.notify_message_event(task_id, message)
        
        # Update state and process
        await self.task_store.update_task_state(
            task_id, 
            TaskState.WORKING,
            message="Starting echo processing"
        )
        
        # Start async processing
        asyncio.create_task(
            self._process_with_store(task_id, message)
        )
        
        return task_id
    
    async def handle_task_get(self, task_id: str) -> Task:
        context = await self.task_store.get_task(task_id)
        if not context:
            raise TaskNotFoundError(task_id)
        
        messages = await self.task_store.get_messages(task_id)
        artifacts = await self.task_store.get_artifacts(task_id)
        
        return Task(
            id=task_id,
            state=context.current_state,
            messages=messages or [],
            artifacts=artifacts or []
        )
    
    async def handle_subscribe_request(
        self, 
        task_id: str
    ) -> AsyncGenerator[A2AEvent, None]:
        queue = asyncio.Queue()
        await self.task_store.add_listener(task_id, queue)
        
        try:
            while True:
                event = await queue.get()
                yield event
                
                # Check for terminal state
                if isinstance(event, TaskStatusUpdateEvent):
                    if event.state in [
                        TaskState.COMPLETED,
                        TaskState.FAILED,
                        TaskState.CANCELED
                    ]:
                        break
        finally:
            await self.task_store.remove_listener(task_id, queue)
```

### Custom JSON-RPC Methods

Extend your agent with custom methods using decorators:

```python
from agentvault_server_sdk import a2a_method

class AdvancedAgent(ImprovedEchoAgent):
    
    @a2a_method("echo/stats")
    async def get_echo_stats(self) -> dict:
        """Return statistics about echo operations"""
        return {
            "total_echoes": await self.get_total_echoes(),
            "active_tasks": len(self.task_store.tasks),
            "uptime": self.get_uptime()
        }
    
    @a2a_method("echo/configure")
    async def configure_echo(self, mode: str = "normal", delay: float = 0.0) -> dict:
        """Configure echo behavior"""
        self.echo_mode = mode
        self.echo_delay = delay
        return {
            "mode": self.echo_mode,
            "delay": self.echo_delay,
            "status": "configured"
        }
    
    @a2a_method("echo/batch")
    async def batch_echo(
        self, 
        messages: List[str], 
        task_store: BaseTaskStore  # Injected automatically
    ) -> dict:
        """Echo multiple messages in one request"""
        # Create task for batch operation
        task_id = f"batch_{uuid.uuid4().hex[:8]}"
        await task_store.create_task(task_id)
        
        # Process in background
        asyncio.create_task(
            self._process_batch(task_id, messages)
        )
        
        return {
            "task_id": task_id,
            "count": len(messages),
            "status": "processing"
        }
```

### Error Handling

Implement robust error handling for production agents:

```python
from agentvault_server_sdk import (
    AgentProcessingError,
    ConfigurationError,
    TaskNotFoundError
)

class RobustAgent(AdvancedAgent):
    
    async def _process_echo(self, task_id: str):
        try:
            # Get task data
            context = await self.task_store.get_task(task_id)
            if not context:
                raise TaskNotFoundError(task_id)
            
            # Simulate processing
            await asyncio.sleep(self.echo_delay)
            
            # Check if cancelled
            if context.current_state == TaskState.CANCELED:
                return
            
            # Process message
            messages = await self.task_store.get_messages(task_id)
            if not messages:
                raise AgentProcessingError("No messages to echo")
            
            # Create echo response
            original_text = messages[-1].parts[0].content
            echo_message = Message(
                role="assistant",
                parts=[TextPart(content=f"Echo: {original_text}")]
            )
            
            # Send response
            await self.task_store.notify_message_event(task_id, echo_message)
            
            # Mark complete
            await self.task_store.update_task_state(
                task_id, 
                TaskState.COMPLETED,
                message="Echo completed successfully"
            )
            
        except TaskNotFoundError:
            self.logger.error(f"Task {task_id} not found")
            raise
        except Exception as e:
            self.logger.error(f"Error processing {task_id}: {e}")
            await self.task_store.update_task_state(
                task_id,
                TaskState.FAILED,
                message=f"Echo failed: {str(e)}"
            )
```

### Authentication and Security

Add authentication to your agent:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    token = credentials.credentials
    
    # Verify API key or JWT token
    if not is_valid_token(token):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    return extract_agent_id(token)

# Create router with auth
a2a_router = create_a2a_router(
    agent,
    prefix="/a2a",
    dependencies=[Depends(verify_token)]
)
```

### Deployment

#### Docker Packaging

Use the SDK's packaging tool:

```bash
# Generate Dockerfile and build artifacts
agentvault-sdk package \
    --output-dir ./docker \
    --entrypoint main:app \
    --agent-card ./agent-card.json \
    --requirements ./requirements.txt

# Build image
docker build -t my-agent:latest ./docker

# Run container
docker run -p 8000:8000 \
  -e AGENT_AUTH_TOKEN=$AUTH_TOKEN \
  my-agent:latest
```

#### Production Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class AgentSettings(BaseSettings):
    # Agent configuration
    agent_name: str = "My Agent"
    agent_version: str = "1.0.0"
    
    # API settings
    port: int = 8000
    host: str = "0.0.0.0"
    workers: int = 4
    
    # Security
    enable_auth: bool = True
    auth_token: str
    allowed_origins: List[str] = ["*"]
    
    # Task management
    max_concurrent_tasks: int = 100
    task_timeout: int = 300
    
    # External services
    redis_url: Optional[str] = None
    database_url: Optional[str] = None
    
    class Config:
        env_prefix = "AGENT_"
        env_file = ".env"

settings = AgentSettings()
```

## Testing Your Agent

### Unit Tests

```python
import pytest
from agentvault.models import Message, TextPart

@pytest.mark.asyncio
async def test_echo_agent():
    # Create agent and store
    store = InMemoryTaskStore()
    agent = ImprovedEchoAgent()
    agent.task_store = store
    
    # Test task creation
    message = Message(
        role="user",
        parts=[TextPart(content="Hello, Agent!")]
    )
    task_id = await agent.handle_task_send(None, message)
    
    assert task_id.startswith("echo_")
    
    # Test task retrieval
    task = await agent.handle_task_get(task_id)
    assert task.state == TaskState.WORKING
    
    # Test event streaming
    events = []
    async for event in agent.handle_subscribe_request(task_id):
        events.append(event)
        if len(events) >= 3:  # Limit for test
            break
    
    assert any(isinstance(e, TaskMessageEvent) for e in events)
```

### Integration Tests

```python
from fastapi.testclient import TestClient
import json

def test_a2a_json_rpc():
    client = TestClient(app)
    
    # Test task creation
    response = client.post("/a2a", json={
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "content": "Test echo"}]
            }
        },
        "id": 1
    })
    
    assert response.status_code == 200
    result = response.json()
    assert "result" in result
    assert "id" in result["result"]
    
    task_id = result["result"]["id"]
    
    # Test task retrieval
    response = client.post("/a2a", json={
        "jsonrpc": "2.0",
        "method": "tasks/get",
        "params": {"task_id": task_id},
        "id": 2
    })
    
    assert response.status_code == 200
    task_data = response.json()["result"]
    assert task_data["state"] in ["SUBMITTED", "WORKING"]
```

## Best Practices

### 1. Async All the Way

Always use async operations to avoid blocking the event loop:

```python
# Good
async def process_data(self, data):
    results = await asyncio.gather(
        self.analyze_part1(data),
        self.analyze_part2(data),
        self.analyze_part3(data)
    )
    return combine_results(results)

# Bad - blocks event loop
def process_data(self, data):
    result1 = analyze_sync(data)  # Blocks!
    return result1
```

### 2. Resource Management

Implement proper cleanup and resource limits:

```python
class ResourceAwareAgent(BaseA2AAgent):
    def __init__(self, max_concurrent_tasks=10):
        super().__init__()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.active_tasks = set()
    
    async def handle_task_send(self, task_id, message):
        async with self.semaphore:
            # Process with limited concurrency
            task_id = await self._create_task(task_id, message)
            self.active_tasks.add(task_id)
            return task_id
    
    async def cleanup_completed_tasks(self):
        """Periodic cleanup of completed tasks"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            completed = []
            for task_id in self.active_tasks:
                context = await self.task_store.get_task(task_id)
                if context.current_state in [
                    TaskState.COMPLETED,
                    TaskState.FAILED,
                    TaskState.CANCELED
                ]:
                    completed.append(task_id)
            
            for task_id in completed:
                self.active_tasks.remove(task_id)
```

### 3. Monitoring and Observability

Add comprehensive logging and metrics:

```python
import structlog
from prometheus_client import Counter, Histogram, Gauge

# Configure structured logging
logger = structlog.get_logger()

# Define metrics
task_counter = Counter(
    'agent_tasks_total',
    'Total tasks processed',
    ['status']
)

task_duration = Histogram(
    'agent_task_duration_seconds',
    'Task processing duration'
)

active_tasks = Gauge(
    'agent_active_tasks',
    'Currently active tasks'
)

class MonitoredAgent(ResourceAwareAgent):
    
    async def handle_task_send(self, task_id, message):
        start_time = time.time()
        
        try:
            result = await super().handle_task_send(task_id, message)
            task_counter.labels(status='created').inc()
            active_tasks.inc()
            
            logger.info(
                "task_created",
                task_id=result,
                message_length=len(str(message))
            )
            
            return result
            
        except Exception as e:
            task_counter.labels(status='failed').inc()
            logger.error(
                "task_creation_failed",
                error=str(e),
                task_id=task_id
            )
            raise
        finally:
            task_duration.observe(time.time() - start_time)
```

### 4. Graceful Shutdown

Handle shutdown signals properly:

```python
import signal
import sys

class GracefulAgent(MonitoredAgent):
    def __init__(self):
        super().__init__()
        self.shutdown_event = asyncio.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, sig, frame):
        logger.info("Shutdown signal received")
        self.shutdown_event.set()
    
    async def shutdown(self):
        """Graceful shutdown procedure"""
        logger.info("Starting graceful shutdown")
        
        # Stop accepting new tasks
        self.accepting_tasks = False
        
        # Wait for active tasks to complete (with timeout)
        try:
            await asyncio.wait_for(
                self._wait_for_tasks(), 
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning("Shutdown timeout - forcing exit")
        
        # Clean up resources
        await self.task_store.close()
        
        logger.info("Shutdown complete")
    
    async def _wait_for_tasks(self):
        """Wait for all active tasks to complete"""
        while self.active_tasks:
            await asyncio.sleep(0.5)
```

## Production Checklist

Before deploying your agent to production:

- [ ] Implement all required BaseA2AAgent methods
- [ ] Add comprehensive error handling
- [ ] Write unit and integration tests (aim for >80% coverage)
- [ ] Create detailed agent-card.json with accurate metadata
- [ ] List all dependencies in requirements.txt
- [ ] Generate Docker artifacts with SDK packaging tool
- [ ] Configure environment variables securely
- [ ] Set up structured logging with appropriate levels
- [ ] Implement health check endpoint
- [ ] Add authentication if handling sensitive data
- [ ] Document all custom JSON-RPC methods
- [ ] Test SSE streaming under load
- [ ] Verify graceful shutdown handling
- [ ] Load test with expected traffic patterns
- [ ] Set up monitoring and alerting

## Next Steps

1. **Explore Example Agents**: Check the SDK repository for more complex examples
2. **Join the Community**: Share your agents and learn from others
3. **Register Your Agent**: Use the AgentVault Registry to make your agent discoverable
4. **Contribute**: Help improve the SDK and documentation

---

Building agents with the AgentVault SDK empowers you to create autonomous, interoperable services that participate in the decentralized agent economy. Start simple, iterate quickly, and build the future of agent-to-agent communication.
