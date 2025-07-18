# AgentVault Library API Reference

## Client Module

### AgentVaultClient

Main client class for A2A protocol interactions.

```python
class AgentVaultClient:
    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        default_timeout: float = 30.0
    )
```

**Parameters:**
- `http_client` (Optional[httpx.AsyncClient]): Custom HTTP client instance
- `default_timeout` (float): Default timeout for requests in seconds

**Methods:**

#### initiate_task
```python
async def initiate_task(
    self,
    agent_card: AgentCard,
    initial_message: Message,
    key_manager: KeyManager,
    mcp_context: Optional[Dict[str, Any]] = None,
    webhook_url: Optional[str] = None
) -> str
```
Initiates a new task with an agent.

**Parameters:**
- `agent_card` (AgentCard): Agent metadata and configuration
- `initial_message` (Message): Initial message to send
- `key_manager` (KeyManager): Credential manager instance
- `mcp_context` (Optional[Dict]): MCP context data to embed
- `webhook_url` (Optional[str]): URL for push notifications

**Returns:**
- `str`: Task ID for the initiated task

**Raises:**
- `A2AAuthenticationError`: Authentication failure
- `A2AConnectionError`: Network connection issues
- `A2ARemoteAgentError`: Agent returned an error
- `A2ATimeoutError`: Request timed out

#### send_message
```python
async def send_message(
    self,
    agent_card: AgentCard,
    task_id: str,
    message: Message,
    key_manager: KeyManager,
    mcp_context: Optional[Dict[str, Any]] = None
) -> bool
```
Sends a message to an existing task.

**Parameters:**
- `agent_card` (AgentCard): Agent metadata
- `task_id` (str): ID of the existing task
- `message` (Message): Message to send
- `key_manager` (KeyManager): Credential manager
- `mcp_context` (Optional[Dict]): MCP context data

**Returns:**
- `bool`: True if message was sent successfully

#### get_task_status
```python
async def get_task_status(
    self,
    agent_card: AgentCard,
    task_id: str,
    key_manager: KeyManager
) -> Task
```
Retrieves current status and history of a task.

**Parameters:**
- `agent_card` (AgentCard): Agent metadata
- `task_id` (str): Task ID to query
- `key_manager` (KeyManager): Credential manager

**Returns:**
- `Task`: Complete task object with state, messages, and artifacts

#### terminate_task
```python
async def terminate_task(
    self,
    agent_card: AgentCard,
    task_id: str,
    key_manager: KeyManager
) -> bool
```
Requests cancellation of a running task.

**Parameters:**
- `agent_card` (AgentCard): Agent metadata
- `task_id` (str): Task ID to cancel
- `key_manager` (KeyManager): Credential manager

**Returns:**
- `bool`: True if cancellation was acknowledged

#### receive_messages
```python
async def receive_messages(
    self,
    agent_card: AgentCard,
    task_id: str,
    key_manager: KeyManager
) -> AsyncGenerator[A2AEvent, None]
```
Subscribes to Server-Sent Events for a task.

**Parameters:**
- `agent_card` (AgentCard): Agent metadata
- `task_id` (str): Task ID to subscribe to
- `key_manager` (KeyManager): Credential manager

**Yields:**
- `A2AEvent`: Stream of task events (status updates, messages, artifacts)

**Example:**
```python
async with AgentVaultClient() as client:
    async for event in client.receive_messages(agent_card, task_id, key_manager):
        if isinstance(event, TaskStatusUpdateEvent):
            print(f"Status: {event.state}")
        elif isinstance(event, TaskMessageEvent):
            print(f"Message: {event.message}")
```

## KeyManager Module

### KeyManager

Manages API keys and OAuth credentials from multiple sources.

```python
class KeyManager:
    def __init__(
        self,
        key_file_path: Optional[Union[str, pathlib.Path]] = None,
        use_env_vars: bool = True,
        use_keyring: bool = False,
        env_prefix: Optional[str] = None,
        oauth_env_prefix: Optional[str] = None
    )
```

**Parameters:**
- `key_file_path` (Optional[Union[str, Path]]): Path to .env or .json file
- `use_env_vars` (bool): Enable loading from environment variables
- `use_keyring` (bool): Enable OS keyring integration
- `env_prefix` (Optional[str]): Custom prefix for API key env vars
- `oauth_env_prefix` (Optional[str]): Custom prefix for OAuth env vars

**Methods:**

#### get_key
```python
def get_key(self, service_id: str) -> Optional[str]
```
Retrieves an API key for the given service.

**Parameters:**
- `service_id` (str): Service identifier (e.g., "openai")

**Returns:**
- `Optional[str]`: API key if found, None otherwise

#### get_key_source
```python
def get_key_source(self, service_id: str) -> Optional[str]
```
Returns the source where the key was loaded from.

**Returns:**
- `Optional[str]`: "file", "env", "keyring", or None

#### set_key_in_keyring
```python
def set_key_in_keyring(self, service_id: str, key_value: str) -> None
```
Stores an API key in the OS keyring.

**Raises:**
- `KeyManagementError`: If keyring is not available or operation fails

#### get_oauth_client_id / get_oauth_client_secret
```python
def get_oauth_client_id(self, service_id: str) -> Optional[str]
def get_oauth_client_secret(self, service_id: str) -> Optional[str]
```
Retrieves OAuth credentials for a service.

#### set_oauth_creds_in_keyring
```python
def set_oauth_creds_in_keyring(
    self,
    service_id: str,
    client_id: str,
    client_secret: str
) -> None
```
Stores OAuth credentials in the OS keyring.

## Models

### Message Components

#### Message
```python
class Message(BaseModel):
    role: Literal['user', 'assistant', 'system', 'tool']
    parts: List[Part]  # List of TextPart, FilePart, or DataPart
    metadata: Optional[Dict[str, Any]] = None
```

#### TextPart
```python
class TextPart(BaseModel):
    type: Literal['text'] = "text"
    content: str
```

#### FilePart
```python
class FilePart(BaseModel):
    type: Literal['file'] = "file"
    url: HttpUrl
    media_type: Optional[str] = None
    filename: Optional[str] = None
```

#### DataPart
```python
class DataPart(BaseModel):
    type: Literal['data'] = "data"
    content: Dict[str, Any]
    media_type: str = "application/json"
```

### Task and State

#### Task
```python
class Task(BaseModel):
    id: str
    state: TaskState
    created_at: datetime.datetime
    updated_at: datetime.datetime
    messages: List[Message] = []
    artifacts: List[Artifact] = []
    metadata: Optional[Dict[str, Any]] = None
```

#### TaskState
```python
class TaskState(str, Enum):
    SUBMITTED = "SUBMITTED"
    WORKING = "WORKING"
    INPUT_REQUIRED = "INPUT_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
```

#### Artifact
```python
class Artifact(BaseModel):
    id: str
    type: str
    content: Optional[Any] = None
    url: Optional[HttpUrl] = None
    media_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### Events

#### TaskStatusUpdateEvent
```python
class TaskStatusUpdateEvent(BaseModel):
    task_id: str  # alias="taskId"
    state: TaskState
    timestamp: datetime.datetime
    message: Optional[str] = None
```

#### TaskMessageEvent
```python
class TaskMessageEvent(BaseModel):
    task_id: str  # alias="taskId"
    message: Message
    timestamp: datetime.datetime
```

#### TaskArtifactUpdateEvent
```python
class TaskArtifactUpdateEvent(BaseModel):
    task_id: str  # alias="taskId"
    artifact: Artifact
    timestamp: datetime.datetime
```

### Agent Card

#### AgentCard
```python
class AgentCard(BaseModel):
    schema_version: str  # alias="schemaVersion"
    human_readable_id: str  # alias="humanReadableId"
    agent_version: str  # alias="agentVersion"
    name: str
    description: str
    url: AnyUrl
    provider: AgentProvider
    capabilities: AgentCapabilities
    auth_schemes: List[AgentAuthentication]  # alias="authSchemes"
    skills: Optional[List[AgentSkill]] = None
    tags: Optional[List[str]] = None
    privacy_policy_url: Optional[HttpUrl] = None
    terms_of_service_url: Optional[HttpUrl] = None
    icon_url: Optional[HttpUrl] = None
    last_updated: Optional[str] = None
```

#### AgentAuthentication
```python
class AgentAuthentication(BaseModel):
    scheme: Literal['apiKey', 'bearer', 'oauth2', 'none']
    description: Optional[str] = None
    token_url: Optional[HttpUrl] = None  # Required for oauth2
    scopes: Optional[List[str]] = None
    service_identifier: Optional[str] = None
```

#### AgentCapabilities
```python
class AgentCapabilities(BaseModel):
    a2a_version: str  # alias="a2aVersion"
    mcp_version: Optional[str] = None  # alias="mcpVersion"
    supported_message_parts: Optional[List[str]] = None
    tee_details: Optional[TeeDetails] = None
    supports_push_notifications: Optional[bool] = None
```

## Utility Functions

### agent_card_utils

#### parse_agent_card_from_dict
```python
def parse_agent_card_from_dict(data: Dict[str, Any]) -> AgentCard
```
Parses an agent card from a dictionary.

**Raises:**
- `AgentCardValidationError`: If validation fails

#### load_agent_card_from_file
```python
def load_agent_card_from_file(
    file_path: Union[str, pathlib.Path]
) -> AgentCard
```
Loads an agent card from a JSON file.

**Raises:**
- `AgentCardError`: If file cannot be read
- `AgentCardValidationError`: If parsing fails

#### fetch_agent_card_from_url
```python
async def fetch_agent_card_from_url(
    url: str,
    http_client: Optional[httpx.AsyncClient] = None,
    timeout: float = 30.0
) -> AgentCard
```
Fetches an agent card from a URL.

**Raises:**
- `AgentCardFetchError`: If fetch fails
- `AgentCardValidationError`: If parsing fails

### mcp_utils

#### format_mcp_context
```python
def format_mcp_context(context_data: Dict[str, Any]) -> Optional[Dict[str, Any]]
```
Formats MCP context data for embedding in messages.

**Parameters:**
- `context_data` (Dict[str, Any]): Raw MCP context

**Returns:**
- `Optional[Dict[str, Any]]`: Formatted context or None if invalid

### onboarding

#### register_agent_with_bootstrap_token
```python
async def register_agent_with_bootstrap_token(
    registry_url: str,
    bootstrap_token: str,
    agent_card: AgentCard,
    http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]
```
Registers an agent with a registry using a bootstrap token.

**Returns:**
Dictionary containing:
- `api_key`: Generated API key for the agent
- `agent_did`: Assigned DID for the agent

**Raises:**
- `OnboardingError`: If registration fails

### staking

#### stake_tokens
```python
async def stake_tokens(
    teg_url: str,
    api_key: str,
    amount: float,
    agent_did: str,
    http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]
```
Stakes AVT tokens for an agent.

#### unstake_tokens
```python
async def unstake_tokens(
    teg_url: str,
    api_key: str,
    amount: float,
    agent_did: str,
    http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]
```
Unstakes AVT tokens.

#### get_staking_balance
```python
async def get_staking_balance(
    teg_url: str,
    api_key: str,
    agent_did: str,
    http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]
```
Retrieves current staking balance.

### governance

#### create_proposal
```python
async def create_proposal(
    teg_url: str,
    api_key: str,
    title: str,
    description: str,
    proposal_type: str = "general",
    http_client: Optional[httpx.AsyncClient] = None
) -> str
```
Creates a governance proposal.

**Returns:**
- `str`: Proposal ID

#### cast_vote
```python
async def cast_vote(
    teg_url: str,
    api_key: str,
    proposal_id: str,
    vote: VoteChoice,
    http_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]
```
Casts a vote on a proposal.

**Parameters:**
- `vote` (VoteChoice): FOR, AGAINST, or ABSTAIN

## Exceptions

### Base Exception
```python
class AgentVaultError(Exception):
    """Base exception for all library errors"""
```

### Agent Card Exceptions
```python
class AgentCardError(AgentVaultError):
    """Base for agent card related errors"""

class AgentCardValidationError(AgentCardError):
    """Raised when agent card validation fails"""

class AgentCardFetchError(AgentCardError):
    """Raised when fetching agent card fails"""
```

### A2A Protocol Exceptions
```python
class A2AError(AgentVaultError):
    """Base for A2A protocol errors"""

class A2AConnectionError(A2AError):
    """Network connection failures"""

class A2AAuthenticationError(A2AError):
    """Authentication failures"""

class A2ARemoteAgentError(A2AError):
    """Agent returned an error"""
    status_code: Optional[int]
    response_body: Optional[Any]

class A2ATimeoutError(A2AError):
    """Request timed out"""

class A2AMessageError(A2AError):
    """Invalid message format"""
```

### Other Exceptions
```python
class KeyManagementError(AgentVaultError):
    """Key management operation failed"""

class OnboardingError(AgentVaultError):
    """Agent onboarding failed"""
```

## Type Aliases

```python
# Union type for events
A2AEvent = Union[
    TaskStatusUpdateEvent,
    TaskMessageEvent,
    TaskArtifactUpdateEvent
]

# Union type for message parts
Part = Union[TextPart, FilePart, DataPart]
```

## Constants

### Environment Variable Prefixes
- `AGENTVAULT_KEY_` - Default prefix for API keys
- `AGENTVAULT_OAUTH_` - Default prefix for OAuth credentials

### Keyring Service Names
- `agentvault:<service_id>` - API keys
- `agentvault:oauth:<service_id>` - OAuth credentials

### Default Values
- Request timeout: 30 seconds
- Token cache expiry buffer: 60 seconds
- SSE stream timeout: None (unlimited)
