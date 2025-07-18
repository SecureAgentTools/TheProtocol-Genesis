# AgentVault Server SDK API Reference

## Core Classes

### BaseA2AAgent

Abstract base class for all A2A protocol compliant agents.

```python
class BaseA2AAgent:
    def __init__(self, agent_metadata: Optional[Dict[str, Any]] = None)
```

**Parameters:**
- `agent_metadata` (Optional[Dict[str, Any]]): Metadata specific to this agent instance

**Required Methods:**

#### handle_task_send
```python
async def handle_task_send(self, task_id: Optional[str], message: Message) -> str
```
Handle incoming messages for task initiation or continuation.

**Parameters:**
- `task_id` (Optional[str]): Existing task ID or None for new tasks
- `message` (Message): The message object containing content and metadata

**Returns:**
- `str`: The task ID (existing or newly created)

**Raises:**
- `A2AError`: For processing errors
- `AgentProcessingError`: For agent-specific failures

#### handle_task_get
```python
async def handle_task_get(self, task_id: str) -> Task
```
Retrieve the current state of a task.

**Parameters:**
- `task_id` (str): The ID of the task to retrieve

**Returns:**
- `Task`: Complete task object with state, messages, and artifacts

**Raises:**
- `TaskNotFoundError`: If task doesn't exist
- `A2AError`: For retrieval errors

#### handle_task_cancel
```python
async def handle_task_cancel(self, task_id: str) -> bool
```
Cancel an ongoing task.

**Parameters:**
- `task_id` (str): The ID of the task to cancel

**Returns:**
- `bool`: True if cancellation accepted, False otherwise

**Raises:**
- `TaskNotFoundError`: If task doesn't exist
- `InvalidStateTransitionError`: If task cannot be canceled

#### handle_subscribe_request
```python
async def handle_subscribe_request(self, task_id: str) -> AsyncGenerator[A2AEvent, None]
```
Stream Server-Sent Events for a task.

**Parameters:**
- `task_id` (str): The ID of the task to subscribe to

**Yields:**
- `A2AEvent`: Status updates, messages, or artifact events

**Raises:**
- `TaskNotFoundError`: If task doesn't exist

## FastAPI Integration

### create_a2a_router

Creates a FastAPI router with A2A protocol endpoints.

```python
def create_a2a_router(
    agent: BaseA2AAgent,
    prefix: str = "",
    tags: Optional[List[str]] = None,
    task_store: Optional[BaseTaskStore] = None,
    dependencies: Optional[List[Depends]] = None
) -> APIRouter
```

**Parameters:**
- `agent` (BaseA2AAgent): The agent instance to expose
- `prefix` (str): URL prefix for the router
- `tags` (Optional[List[str]]): OpenAPI tags
- `task_store` (Optional[BaseTaskStore]): Task state storage
- `dependencies` (Optional[List[Depends]]): FastAPI dependencies

**Returns:**
- `APIRouter`: Configured router ready for inclusion

**Example:**
```python
from fastapi import FastAPI, Depends
from agentvault_server_sdk import create_a2a_router

app = FastAPI()
agent = MyCustomAgent()
task_store = PostgresTaskStore()

router = create_a2a_router(
    agent,
    prefix="/api/v1/agent",
    tags=["Agent API"],
    task_store=task_store,
    dependencies=[Depends(verify_auth_token)]
)

app.include_router(router)
```

### a2a_method Decorator

Decorator for custom JSON-RPC method handlers.

```python
def a2a_method(method_name: str) -> Callable[[F], F]
```

**Parameters:**
- `method_name` (str): The JSON-RPC method name to handle

**Example:**
```python
from agentvault_server_sdk import a2a_method, BaseA2AAgent

class AnalysisAgent(BaseA2AAgent):
    @a2a_method("analysis/start")
    async def start_analysis(
        self, 
        data_url: str, 
        analysis_type: str = "basic"
    ) -> dict:
        # Custom analysis logic
        return {
            "analysis_id": "12345",
            "status": "started"
        }
```

## State Management

### BaseTaskStore

Abstract base class for task state storage implementations.

```python
class BaseTaskStore(ABC):
    # Core task operations
    async def get_task(self, task_id: str) -> Optional[TaskContext]
    async def create_task(self, task_id: str) -> TaskContext
    async def update_task_state(self, task_id: str, new_state: Union[TaskState, str], message: Optional[str] = None) -> Optional[TaskContext]
    async def delete_task(self, task_id: str) -> bool
    
    # Listener management
    async def add_listener(self, task_id: str, listener_queue: asyncio.Queue)
    async def remove_listener(self, task_id: str, listener_queue: asyncio.Queue)
    async def get_listeners(self, task_id: str) -> List[asyncio.Queue]
    
    # Event notifications
    async def notify_status_update(self, task_id: str, new_state: Union[TaskState, str], message: Optional[str] = None)
    async def notify_message_event(self, task_id: str, message: Message)
    async def notify_artifact_event(self, task_id: str, artifact: Artifact)
    
    # Data retrieval
    async def get_messages(self, task_id: str) -> Optional[List[Message]]
    async def get_artifacts(self, task_id: str) -> Optional[List[Artifact]]
```

### InMemoryTaskStore

Default in-memory implementation of BaseTaskStore.

```python
class InMemoryTaskStore(BaseTaskStore):
    def __init__(self)
```

**Features:**
- Thread-safe with asyncio locks
- Automatic event notification
- Message and artifact storage
- Listener queue management

**Example:**
```python
task_store = InMemoryTaskStore()

# Create a task
task = await task_store.create_task("task_123")

# Update state
await task_store.update_task_state(
    "task_123", 
    TaskState.WORKING,
    message="Processing started"
)

# Add a message
await task_store.notify_message_event(
    "task_123",
    Message(role="assistant", content="Analysis in progress...")
)
```

### TaskContext

Data class representing a task's state and metadata.

```python
@dataclass
class TaskContext:
    task_id: str
    current_state: Union[TaskState, str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    messages: List[Message]
    artifacts: Dict[str, Artifact]
    
    def update_state(self, new_state: Union[TaskState, str])
    def add_message(self, message: Message)
    def add_or_update_artifact(self, artifact: Artifact)
```

## Exceptions

### AgentServerError

Base exception for all agent-related errors.

```python
class AgentServerError(Exception):
    pass
```

### TaskNotFoundError

Raised when operating on a non-existent task.

```python
class TaskNotFoundError(AgentServerError):
    def __init__(self, task_id: str, message: str = "Task not found")
```

### InvalidStateTransitionError

Raised for invalid task state transitions.

```python
class InvalidStateTransitionError(AgentServerError):
    def __init__(
        self, 
        task_id: str, 
        from_state: str, 
        to_state: str, 
        message: str = "Invalid state transition"
    )
```

### AgentProcessingError

General agent processing failures.

```python
class AgentProcessingError(AgentServerError):
    pass
```

### ConfigurationError

Agent configuration issues.

```python
class ConfigurationError(AgentServerError):
    pass
```

## CLI Tools

### agentvault-sdk package

Command-line tool for generating Docker packaging artifacts.

```bash
agentvault-sdk package [OPTIONS]
```

**Options:**
- `--output-dir, -o` (REQUIRED): Directory for generated files
- `--entrypoint` (REQUIRED): Python import path (e.g., `my_agent.main:app`)
- `--python`: Python version (default: "3.11")
- `--suffix`: Base image suffix (default: "slim-bookworm")
- `--port, -p`: Container port (default: 8000)
- `--requirements, -r`: Path to requirements.txt
- `--agent-card, -c`: Path to agent-card.json
- `--app-dir`: Container app directory (default: "/app")

**Example:**
```bash
agentvault-sdk package \
    --output-dir ./docker_build \
    --entrypoint agent.server:app \
    --python 3.11 \
    --port 8080 \
    --requirements ./requirements.txt \
    --agent-card ./agent-card.json
```

**Generated Files:**
- `Dockerfile`: Multi-stage build optimized for Python
- `.dockerignore`: Standard exclusions
- `requirements.txt`: Copied from source
- `agent-card.json`: Copied if provided

## State Transitions

Valid task state transitions:

```
SUBMITTED   → WORKING, CANCELED
WORKING     → INPUT_REQUIRED, COMPLETED, FAILED, CANCELED  
INPUT_REQUIRED → WORKING, CANCELED
COMPLETED   → COMPLETED (terminal)
FAILED      → FAILED (terminal)
CANCELED    → CANCELED (terminal)
```

## Event Types

### TaskStatusUpdateEvent

```python
class TaskStatusUpdateEvent:
    taskId: str
    state: TaskState
    timestamp: datetime
    message: Optional[str]
```

### TaskMessageEvent

```python
class TaskMessageEvent:
    taskId: str
    message: Message
    timestamp: datetime
```

### TaskArtifactUpdateEvent

```python
class TaskArtifactUpdateEvent:
    taskId: str
    artifact: Artifact
    timestamp: datetime
```

## JSON-RPC Error Codes

Standard error codes returned by the A2A router:

- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000`: Application error
- `-32001`: Task not found

## Complete Example

```python
from typing import AsyncGenerator, Optional
from fastapi import FastAPI
from agentvault_server_sdk import (
    BaseA2AAgent, create_a2a_router, 
    InMemoryTaskStore, a2a_method
)
from agentvault.models import Message, Task, TaskState, A2AEvent

class ExampleAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__(agent_metadata={"version": "1.0.0"})
        self.task_store = InMemoryTaskStore()
    
    async def handle_task_send(
        self, 
        task_id: Optional[str], 
        message: Message
    ) -> str:
        # Create or get task
        if task_id is None:
            task_id = f"task_{uuid.uuid4()}"
            await self.task_store.create_task(task_id)
        
        # Process message
        await self.task_store.notify_message_event(task_id, message)
        await self.task_store.update_task_state(
            task_id, 
            TaskState.WORKING
        )
        
        # Start background processing
        asyncio.create_task(self._process_task(task_id, message))
        
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
    
    async def handle_task_cancel(self, task_id: str) -> bool:
        context = await self.task_store.get_task(task_id)
        if not context:
            raise TaskNotFoundError(task_id)
        
        await self.task_store.update_task_state(
            task_id, 
            TaskState.CANCELED
        )
        return True
    
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
        finally:
            await self.task_store.remove_listener(task_id, queue)
    
    @a2a_method("agent/status")
    async def get_agent_status(self) -> dict:
        return {
            "status": "online",
            "version": self.agent_metadata["version"],
            "capabilities": ["analysis", "summarization"]
        }
    
    async def _process_task(self, task_id: str, message: Message):
        # Simulated processing
        await asyncio.sleep(2)
        
        result_message = Message(
            role="assistant",
            content="Task completed successfully!"
        )
        await self.task_store.notify_message_event(
            task_id, 
            result_message
        )
        
        await self.task_store.update_task_state(
            task_id, 
            TaskState.COMPLETED,
            message="Processing finished"
        )

# Create FastAPI app
app = FastAPI(title="Example Agent")
agent = ExampleAgent()

# Create and include router
router = create_a2a_router(
    agent,
    prefix="/a2a",
    task_store=agent.task_store
)
app.include_router(router)
```
