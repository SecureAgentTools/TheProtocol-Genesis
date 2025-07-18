# AgentVault Library Documentation

## Overview

The AgentVault Library (`agentvault`) is the core Python client library for interacting with agents in the Sovereign Stack ecosystem. It provides a complete implementation of the A2A (Agent-to-Agent) protocol client, secure credential management, and utilities for working with agent metadata.

## Key Components

### 1. AgentVaultClient

The main client class for communicating with remote agents using the A2A protocol:

```python
from agentvault import AgentVaultClient, AgentCard, KeyManager
from agentvault.models import Message, TextPart

async with AgentVaultClient() as client:
    # Initialize a task
    task_id = await client.initiate_task(
        agent_card=agent_card,
        initial_message=Message(
            role="user",
            parts=[TextPart(content="Analyze this data...")]
        ),
        key_manager=key_manager
    )
    
    # Stream responses
    async for event in client.receive_messages(agent_card, task_id, key_manager):
        print(f"Event: {event}")
```

### 2. KeyManager

Secure credential management supporting multiple sources:

```python
from agentvault import KeyManager

# Initialize with various sources
key_manager = KeyManager(
    key_file_path="./secrets.env",  # .env or .json file
    use_env_vars=True,               # Environment variables
    use_keyring=True                 # OS keyring (optional)
)

# Retrieve credentials
api_key = key_manager.get_key("openai")
client_id = key_manager.get_oauth_client_id("github")
client_secret = key_manager.get_oauth_client_secret("github")
```

### 3. Agent Card Models

Structured representation of agent metadata:

```python
from agentvault import AgentCard
from agentvault.agent_card_utils import load_agent_card_from_file

# Load and parse agent card
agent_card = load_agent_card_from_file("./agent-card.json")

# Access metadata
print(f"Agent: {agent_card.name}")
print(f"Version: {agent_card.agent_version}")
print(f"Endpoint: {agent_card.url}")
print(f"Auth required: {[s.scheme for s in agent_card.auth_schemes]}")
```

### 4. Protocol Models

Comprehensive Pydantic models for the A2A protocol:

```python
from agentvault.models import (
    Message, Task, TaskState,
    TextPart, FilePart, DataPart,
    Artifact, TaskStatusUpdateEvent
)

# Build complex messages
message = Message(
    role="user",
    parts=[
        TextPart(content="Process this file:"),
        FilePart(
            url="https://example.com/data.csv",
            media_type="text/csv"
        )
    ],
    metadata={"priority": "high"}
)
```

## Features

### JSON-RPC Protocol

All client-server communication uses JSON-RPC 2.0:
- Standardized request/response format
- Proper error handling with typed exceptions
- Request ID tracking for debugging

### Server-Sent Events (SSE)

Real-time streaming of task updates:
- Automatic reconnection on network issues
- Event validation and type safety
- Support for status, message, and artifact events

### Multi-Source Credential Management

Priority-based credential loading:
1. **Key Files** (.env or .json) - Highest priority
2. **Environment Variables** - Medium priority
3. **OS Keyring** - Lowest priority (on-demand)

### Authentication Schemes

Supports multiple authentication methods:
- **API Key** - Via X-Api-Key header
- **OAuth 2.0** - Client credentials grant flow
- **Bearer Token** - Direct token auth
- **None** - For public endpoints

### MCP Context Support

Embed Model Context Protocol data in messages:

```python
mcp_context = {
    "resources": [
        {"type": "file", "uri": "file:///data.csv"}
    ],
    "tools": [
        {"name": "calculator", "description": "Math tool"}
    ]
}

task_id = await client.initiate_task(
    agent_card=agent_card,
    initial_message=message,
    key_manager=key_manager,
    mcp_context=mcp_context
)
```

### Webhook Support

Enable push notifications for task updates:

```python
task_id = await client.initiate_task(
    agent_card=agent_card,
    initial_message=message,
    key_manager=key_manager,
    webhook_url="https://myapp.com/webhooks/agent-updates"
)
```

## Architecture

### Client Design

The `AgentVaultClient` uses:
- `httpx` for async HTTP with HTTP/2 support
- Connection pooling for efficiency
- Automatic retry and timeout handling
- Comprehensive logging for debugging

### Credential Storage

KeyManager storage conventions:

**API Keys:**
- Env: `AGENTVAULT_KEY_<SERVICE_ID>`
- File (.env): `service_id=key_value`
- File (.json): `{"service_id": "key_value"}`
- Keyring: service=`agentvault:service_id`

**OAuth Credentials:**
- Env: `AGENTVAULT_OAUTH_<SERVICE_ID>_CLIENT_ID/SECRET`
- File (.env): `AGENTVAULT_OAUTH_service_id_CLIENT_ID=...`
- File (.json): `{"service_id": {"oauth": {"clientId": "...", "clientSecret": "..."}}}`
- Keyring: service=`agentvault:oauth:service_id`

### Error Handling

Hierarchical exception structure:
```
AgentVaultError (base)
├── AgentCardError
│   ├── AgentCardValidationError
│   └── AgentCardFetchError
├── A2AError
│   ├── A2AConnectionError
│   ├── A2AAuthenticationError
│   ├── A2ARemoteAgentError
│   ├── A2ATimeoutError
│   └── A2AMessageError
├── KeyManagementError
└── OnboardingError
```

## Usage Patterns

### Basic Task Interaction

```python
import asyncio
from agentvault import AgentVaultClient, KeyManager
from agentvault.agent_card_utils import fetch_agent_card_from_url
from agentvault.models import Message, TextPart, TaskState

async def interact_with_agent():
    # Setup
    key_manager = KeyManager(use_env_vars=True)
    agent_card = await fetch_agent_card_from_url(
        "https://api.example.com/agent-card.json"
    )
    
    async with AgentVaultClient() as client:
        # Start task
        message = Message(
            role="user",
            parts=[TextPart(content="Summarize recent AI news")]
        )
        
        task_id = await client.initiate_task(
            agent_card, message, key_manager
        )
        
        # Monitor progress
        async for event in client.receive_messages(
            agent_card, task_id, key_manager
        ):
            if hasattr(event, 'state'):
                print(f"Status: {event.state}")
            elif hasattr(event, 'message'):
                print(f"Message: {event.message.parts[0].content}")
            
            # Check completion
            if hasattr(event, 'state') and event.state in [
                TaskState.COMPLETED, TaskState.FAILED
            ]:
                break

asyncio.run(interact_with_agent())
```

### Advanced Credential Setup

```python
from pathlib import Path
from agentvault import KeyManager

# Multi-source configuration
key_manager = KeyManager(
    key_file_path=Path.home() / ".agentvault" / "keys.json",
    use_env_vars=True,
    use_keyring=True,
    env_prefix="MYAPP_KEY_",
    oauth_env_prefix="MYAPP_OAUTH_"
)

# Store credentials securely
if key_manager.use_keyring:
    key_manager.set_key_in_keyring("openai", "sk-...")
    key_manager.set_oauth_creds_in_keyring(
        "github",
        client_id="...",
        client_secret="..."
    )

# Check configuration
print(key_manager.get_key_source("openai"))  # 'keyring'
print(key_manager.get_oauth_config_status("github"))  # 'Configured'
```

### Error Handling Best Practices

```python
from agentvault import AgentVaultClient
from agentvault.exceptions import (
    A2AAuthenticationError,
    A2ATimeoutError,
    A2ARemoteAgentError
)

async def robust_agent_interaction():
    client = AgentVaultClient(default_timeout=60.0)
    
    try:
        task_id = await client.initiate_task(...)
        
    except A2AAuthenticationError as e:
        print(f"Authentication failed: {e}")
        # Check credentials
        
    except A2ATimeoutError as e:
        print(f"Request timed out: {e}")
        # Retry with longer timeout
        
    except A2ARemoteAgentError as e:
        print(f"Agent error ({e.status_code}): {e.message}")
        # Handle based on status code
        
    finally:
        await client.close()
```

## Integration Examples

### With Registry

```python
from agentvault import AgentVaultClient
from agentvault.onboarding import register_agent_with_bootstrap_token

# Register agent
credentials = await register_agent_with_bootstrap_token(
    registry_url="https://registry.example.com",
    bootstrap_token="...",
    agent_card=my_agent_card
)

# Use returned credentials
key_manager.set_key_in_keyring(
    "my-agent-registry",
    credentials["api_key"]
)
```

### With TEG Layer

```python
from agentvault.staking import stake_tokens, get_staking_balance
from agentvault.governance import create_proposal, cast_vote

# Economic operations
await stake_tokens(
    teg_url="https://teg.example.com",
    api_key="...",
    amount=100.0,
    agent_did="did:web:example.com:agents:analyzer"
)

balance = await get_staking_balance(
    teg_url="https://teg.example.com",
    api_key="...",
    agent_did="did:web:example.com:agents:analyzer"
)

# Governance participation
proposal_id = await create_proposal(
    teg_url="https://teg.example.com",
    api_key="...",
    title="Increase staking rewards",
    description="Proposal to increase rewards by 10%"
)
```

## Configuration

### Environment Variables

```bash
# API Keys
export AGENTVAULT_KEY_OPENAI="sk-..."
export AGENTVAULT_KEY_ANTHROPIC="..."

# OAuth Credentials
export AGENTVAULT_OAUTH_GITHUB_CLIENT_ID="..."
export AGENTVAULT_OAUTH_GITHUB_CLIENT_SECRET="..."
```

### Key File Formats

**.env format:**
```env
openai=sk-...
anthropic=...
AGENTVAULT_OAUTH_github_CLIENT_ID=...
AGENTVAULT_OAUTH_github_CLIENT_SECRET=...
```

**.json format:**
```json
{
  "openai": "sk-...",
  "anthropic": {
    "apiKey": "..."
  },
  "github": {
    "oauth": {
      "clientId": "...",
      "clientSecret": "..."
    }
  }
}
```

## Debugging

### Enable Detailed Logging

```python
import logging

# Set library log level
logging.getLogger("agentvault").setLevel(logging.DEBUG)

# Or for specific components
logging.getLogger("agentvault.client").setLevel(logging.DEBUG)
logging.getLogger("agentvault.key_manager").setLevel(logging.INFO)
```

### Common Issues

1. **SSL Certificate Errors**: Ensure system certificates are up to date
2. **Timeout Errors**: Increase `default_timeout` in AgentVaultClient
3. **Authentication Failures**: Check KeyManager sources and priorities
4. **SSE Connection Drops**: Normal for long-running streams, client auto-reconnects

## Performance Optimization

- Reuse `AgentVaultClient` instances for connection pooling
- Use async context managers for proper resource cleanup
- Cache agent cards to avoid repeated fetches
- Enable HTTP/2 for multiplexing (default in httpx)

## Security Considerations

- Never commit credentials to version control
- Use OS keyring for production environments
- Rotate API keys and OAuth credentials regularly
- Validate agent cards before trusting endpoints
- Use HTTPS for all agent communications

## Future Enhancements

- WebRTC support for multimodal agents
- Client-side rate limiting
- Automatic retry with exponential backoff
- Response caching for idempotent operations
- Plugin system for custom authentication schemes
