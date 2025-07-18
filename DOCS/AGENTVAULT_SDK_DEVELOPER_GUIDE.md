# AgentVault SDK Developer Guide

## Building Your First Agent

This guide walks you through creating an A2A protocol compliant agent using the AgentVault Server SDK.

## Prerequisites

- Python 3.10 or 3.11
- Basic understanding of async/await patterns
- Familiarity with FastAPI (helpful but not required)

## Installation

```bash
pip install agentvault-server-sdk agentvault
```

## Step 1: Create Your Agent Class

Start by extending the `BaseA2AAgent` class:

```python
from typing import Optional, AsyncGenerator
import uuid
import asyncio
from agentvault_server_sdk import BaseA2AAgent
from agentvault.models import Message, Task, TaskState, A2AEvent

class TranslationAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__(agent_metadata={
            "name": "Translation Agent",
            "version": "1.0.0",
            "capabilities": ["translate", "detect_language"]
        })
        self.active_tasks = {}
```

## Step 2: Implement Required Methods

### Handle Task Send

This method receives new messages and manages task creation:

```python
async def handle_task_send(
    self, 
    task_id: Optional[str], 
    message: Message
) -> str:
    # Generate task ID if new task
    if task_id is None:
        task_id = f"trans_{uuid.uuid4().hex[:8]}"
        self.active_tasks[task_id] = {
            "status": TaskState.SUBMITTED,
            "messages": [],
            "target_language": None
        }
    
    # Store the message
    task_data = self.active_tasks.get(task_id)
    if not task_data:
        raise TaskNotFoundError(task_id)
    
    task_data["messages"].append(message)
    
    # Extract translation request
    content = message.content
    if "translate to" in content.lower():
        # Parse target language
        task_data["target_language"] = self._extract_language(content)
        task_data["status"] = TaskState.WORKING
        
        # Start async translation
        asyncio.create_task(
            self._perform_translation(task_id, content)
        )
    
    return task_id
```

### Handle Task Get

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

### Handle Task Cancel

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

### Handle Subscribe Request

Stream real-time updates:

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

## Step 3: Add Business Logic

Implement your agent's core functionality:

```python
async def _perform_translation(self, task_id: str, text: str):
    task_data = self.active_tasks[task_id]
    
    try:
        # Simulate translation API call
        await asyncio.sleep(2)  # Replace with actual API call
        
        # Check if cancelled
        if task_data.get("cancel_requested"):
            await self._send_event(
                task_id,
                TaskStatusUpdateEvent(
                    taskId=task_id,
                    state=TaskState.CANCELED,
                    timestamp=datetime.now(timezone.utc),
                    message="Translation cancelled by user"
                )
            )
            return
        
        # Perform translation
        translated_text = f"[Translated to {task_data['target_language']}]: {text}"
        
        # Send result message
        result_message = Message(
            role="assistant",
            content=translated_text
        )
        task_data["messages"].append(result_message)
        
        await self._send_event(
            task_id,
            TaskMessageEvent(
                taskId=task_id,
                message=result_message,
                timestamp=datetime.now(timezone.utc)
            )
        )
        
        # Mark complete
        task_data["status"] = TaskState.COMPLETED
        await self._send_event(
            task_id,
            TaskStatusUpdateEvent(
                taskId=task_id,
                state=TaskState.COMPLETED,
                timestamp=datetime.now(timezone.utc),
                message="Translation completed successfully"
            )
        )
        
    except Exception as e:
        # Handle errors
        task_data["status"] = TaskState.FAILED
        await self._send_event(
            task_id,
            TaskStatusUpdateEvent(
                taskId=task_id,
                state=TaskState.FAILED,
                timestamp=datetime.now(timezone.utc),
                message=f"Translation failed: {str(e)}"
            )
        )

async def _send_event(self, task_id: str, event: A2AEvent):
    """Send event to all subscribers"""
    task_data = self.active_tasks.get(task_id)
    if not task_data:
        return
    
    subscribers = task_data.get("subscribers", [])
    for queue in subscribers:
        await queue.put(event)
```

## Step 4: Use Task Store (Recommended)

Instead of managing state manually, use the built-in task store:

```python
from agentvault_server_sdk import InMemoryTaskStore

class ImprovedTranslationAgent(BaseA2AAgent):
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
            task_id = f"trans_{uuid.uuid4().hex[:8]}"
            await self.task_store.create_task(task_id)
        
        # Store message
        await self.task_store.notify_message_event(task_id, message)
        
        # Update state and process
        await self.task_store.update_task_state(
            task_id, 
            TaskState.WORKING,
            message="Starting translation"
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

## Step 5: Create FastAPI Application

Set up the web server:

```python
from fastapi import FastAPI
from agentvault_server_sdk import create_a2a_router

# Create app
app = FastAPI(
    title="Translation Agent API",
    description="A2A compliant translation service",
    version="1.0.0"
)

# Initialize agent
agent = ImprovedTranslationAgent()

# Create A2A router
a2a_router = create_a2a_router(
    agent,
    prefix="/a2a",
    tags=["Translation Agent"],
    task_store=agent.task_store
)

# Include router
app.include_router(a2a_router)

# Add health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "translation"}
```

## Step 6: Add Custom Methods

Extend functionality with custom JSON-RPC methods:

```python
from agentvault_server_sdk import a2a_method

class AdvancedTranslationAgent(ImprovedTranslationAgent):
    
    @a2a_method("translation/languages")
    async def get_supported_languages(self) -> dict:
        """Return list of supported languages"""
        return {
            "languages": [
                {"code": "es", "name": "Spanish"},
                {"code": "fr", "name": "French"},
                {"code": "de", "name": "German"},
                {"code": "ja", "name": "Japanese"}
            ]
        }
    
    @a2a_method("translation/detect")
    async def detect_language(self, text: str) -> dict:
        """Detect the language of input text"""
        # Implement language detection
        detected = self._detect_language_internal(text)
        return {
            "detected_language": detected,
            "confidence": 0.95
        }
    
    @a2a_method("translation/batch")
    async def batch_translate(
        self, 
        texts: List[str], 
        target_language: str,
        task_store: BaseTaskStore  # Injected automatically
    ) -> dict:
        """Translate multiple texts in one request"""
        # Create task for batch operation
        task_id = f"batch_{uuid.uuid4().hex[:8]}"
        await task_store.create_task(task_id)
        
        # Process in background
        asyncio.create_task(
            self._process_batch(task_id, texts, target_language)
        )
        
        return {
            "task_id": task_id,
            "count": len(texts),
            "status": "processing"
        }
```

## Step 7: Error Handling

Implement robust error handling:

```python
from agentvault_server_sdk import (
    AgentProcessingError,
    ConfigurationError
)

class RobustTranslationAgent(AdvancedTranslationAgent):
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        if not api_key:
            raise ConfigurationError(
                "Translation API key is required"
            )
        self.api_key = api_key
    
    async def _translate_text(
        self, 
        text: str, 
        target_lang: str
    ) -> str:
        try:
            # Call translation API
            result = await self._call_api(text, target_lang)
            return result
        except HttpError as e:
            if e.status_code == 429:
                raise AgentProcessingError(
                    "Rate limit exceeded. Please try again later."
                )
            elif e.status_code == 401:
                raise ConfigurationError(
                    "Invalid API key"
                )
            else:
                raise AgentProcessingError(
                    f"Translation service error: {e}"
                )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise AgentProcessingError(
                "An unexpected error occurred"
            )
```

## Step 8: Add Authentication

Secure your agent with authentication:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    token = credentials.credentials
    
    # Verify JWT token
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        return payload["sub"]
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

# Create router with auth
a2a_router = create_a2a_router(
    agent,
    prefix="/a2a",
    dependencies=[Depends(verify_token)]
)
```

## Step 9: Package for Deployment

Create your project structure:

```
translation-agent/
├── agent/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   └── translator.py     # Agent implementation
├── requirements.txt
├── agent-card.json
├── Dockerfile
└── docker-compose.yml
```

Generate Docker artifacts:

```bash
agentvault-sdk package \
    --output-dir ./docker \
    --entrypoint agent.main:app \
    --agent-card ./agent-card.json \
    --requirements ./requirements.txt
```

## Step 10: Testing Your Agent

### Unit Tests

```python
import pytest
from agentvault.models import Message

@pytest.mark.asyncio
async def test_task_creation():
    agent = TranslationAgent()
    
    message = Message(
        role="user",
        content="Translate to Spanish: Hello world"
    )
    
    task_id = await agent.handle_task_send(None, message)
    assert task_id.startswith("trans_")
    
    task = await agent.handle_task_get(task_id)
    assert task.state == TaskState.WORKING

@pytest.mark.asyncio
async def test_translation_completion():
    agent = TranslationAgent()
    
    # Create task
    message = Message(
        role="user",
        content="Translate to Spanish: Hello"
    )
    task_id = await agent.handle_task_send(None, message)
    
    # Wait for completion
    await asyncio.sleep(3)
    
    # Check result
    task = await agent.handle_task_get(task_id)
    assert task.state == TaskState.COMPLETED
    assert len(task.messages) == 2  # User + assistant
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_json_rpc_endpoint():
    client = TestClient(app)
    
    # Send translation request
    response = client.post("/a2a", json={
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "message": {
                "role": "user",
                "content": "Translate to French: Good morning"
            }
        },
        "id": 1
    })
    
    assert response.status_code == 200
    result = response.json()
    assert result["jsonrpc"] == "2.0"
    assert "result" in result
    assert "id" in result["result"]
```

## Best Practices

### 1. State Management

- Use the provided task store for consistency
- Always validate state transitions
- Store all relevant data in task context

### 2. Async Operations

- Use `asyncio.create_task()` for background work
- Implement proper cancellation handling
- Avoid blocking operations in handlers

### 3. Error Handling

- Raise appropriate SDK exceptions
- Log errors for debugging
- Provide meaningful error messages

### 4. Event Streaming

- Send events promptly as state changes
- Include timestamps on all events
- Clean up listeners on disconnect

### 5. Resource Management

- Implement task cleanup for completed tasks
- Use connection pooling for external services
- Monitor memory usage for long-running agents

## Advanced Patterns

### Background Task Management

```python
class ManagedAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__()
        self.background_tasks = {}
    
    async def handle_task_send(
        self, 
        task_id: Optional[str], 
        message: Message
    ) -> str:
        # Create task
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Cancel existing background task if any
        if task_id in self.background_tasks:
            self.background_tasks[task_id].cancel()
        
        # Start new background task
        task = asyncio.create_task(
            self._process_async(task_id, message)
        )
        self.background_tasks[task_id] = task
        
        # Clean up on completion
        task.add_done_callback(
            lambda t: self.background_tasks.pop(task_id, None)
        )
        
        return task_id
```

### Rate Limiting

```python
from asyncio import Semaphore

class RateLimitedAgent(BaseA2AAgent):
    def __init__(self, max_concurrent: int = 10):
        super().__init__()
        self.semaphore = Semaphore(max_concurrent)
    
    async def _process_with_limit(self, task_id: str):
        async with self.semaphore:
            # Process task
            await self._do_work(task_id)
```

### Persistent Task Store

```python
class PostgresTaskStore(BaseTaskStore):
    def __init__(self, connection_string: str):
        self.pool = await asyncpg.create_pool(connection_string)
    
    async def create_task(self, task_id: str) -> TaskContext:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO tasks (id, state, created_at) "
                "VALUES ($1, $2, $3)",
                task_id, TaskState.SUBMITTED, datetime.now()
            )
        # ... implement other methods
```

## Deployment Checklist

- [ ] Implement all required BaseA2AAgent methods
- [ ] Add comprehensive error handling
- [ ] Write unit and integration tests
- [ ] Create agent-card.json with metadata
- [ ] List all dependencies in requirements.txt
- [ ] Generate Docker artifacts with SDK
- [ ] Configure environment variables
- [ ] Set up logging and monitoring
- [ ] Implement health checks
- [ ] Add authentication if needed
- [ ] Document API endpoints
- [ ] Test SSE streaming
- [ ] Verify state transitions
- [ ] Load test the agent
- [ ] Deploy to target environment
