# Using the AgentVault Library

## Getting Started

This guide walks you through using the AgentVault Library to interact with agents in the Sovereign Stack ecosystem. The library provides a Python client for the Agent-to-Agent (A2A) protocol, enabling seamless communication with AI agents.

## Installation

```bash
# Basic installation
pip install agentvault

# With OS keyring support for secure credential storage
pip install agentvault[os_keyring]

# Development installation with all extras
pip install agentvault[os_keyring,dev]
```

## Core Concepts

### Agent Cards

Agent cards are JSON documents that describe an agent's capabilities, endpoints, and authentication requirements. They serve as the "business card" for agents in the ecosystem:

```json
{
  "schemaVersion": "1.0",
  "humanReadableId": "weather-bot",
  "name": "Weather Assistant",
  "url": "https://api.weather-bot.com/a2a",
  "authSchemes": [
    {
      "scheme": "apiKey",
      "serviceIdentifier": "weather-bot"
    }
  ],
  "capabilities": {
    "a2aVersion": "0.2",
    "supportedMessageParts": ["text", "data"]
  }
}
```

### Messages and Parts

Messages in the A2A protocol consist of a role and one or more parts:

```python
from agentvault.models import Message, TextPart, DataPart

# Simple text message
message = Message(
    role="user",
    parts=[TextPart(content="What's the weather in Paris?")]
)

# Multi-part message with structured data
message = Message(
    role="user",
    parts=[
        TextPart(content="Analyze this data:"),
        DataPart(content={"temperatures": [20, 22, 19, 23]})
    ]
)
```

### Task Lifecycle

Tasks progress through these states:

1. **SUBMITTED** - Task created, not yet started
2. **WORKING** - Agent is processing the task
3. **INPUT_REQUIRED** - Agent needs more information
4. **COMPLETED** - Task finished successfully
5. **FAILED** - Task encountered an error
6. **CANCELED** - Task was canceled by request

## Setting Up Credentials

The library supports multiple credential management methods:

### Method 1: Environment Variables

```bash
export AGENTVAULT_KEY_OPENAI="sk-..."
export AGENTVAULT_KEY_WEATHER_BOT="wb-key-..."
```

### Method 2: Key File (.env)

```env
# ~/.agentvault/keys.env
openai=sk-...
weather_bot=wb-key-...
anthropic=ant-...
```

### Method 3: Key File (.json)

```json
{
  "openai": "sk-...",
  "weather_bot": "wb-key-...",
  "github": {
    "oauth": {
      "clientId": "...",
      "clientSecret": "..."
    }
  }
}
```

### Method 4: OS Keyring (Most Secure)

```python
from agentvault import KeyManager

key_manager = KeyManager(use_keyring=True)
key_manager.set_key_in_keyring("openai", "sk-...")
```

## Basic Usage

### Simple Agent Interaction

```python
import asyncio
from agentvault import AgentVaultClient, KeyManager
from agentvault.agent_card_utils import load_agent_card_from_file
from agentvault.models import Message, TextPart

async def ask_weather():
    # Load credentials
    key_manager = KeyManager(
        key_file_path="~/.agentvault/keys.env",
        use_env_vars=True
    )
    
    # Load agent card
    agent_card = load_agent_card_from_file("./weather-bot-card.json")
    
    # Create client
    async with AgentVaultClient() as client:
        # Send initial message
        message = Message(
            role="user",
            parts=[TextPart(content="What's the weather in Tokyo?")]
        )
        
        task_id = await client.initiate_task(
            agent_card=agent_card,
            initial_message=message,
            key_manager=key_manager
        )
        
        print(f"Task created: {task_id}")
        
        # Wait for response
        async for event in client.receive_messages(
            agent_card, task_id, key_manager
        ):
            print(f"Event type: {type(event).__name__}")
            
            if hasattr(event, 'message'):
                # New message from agent
                msg = event.message
                for part in msg.parts:
                    if hasattr(part, 'content'):
                        print(f"Agent: {part.content}")
            
            if hasattr(event, 'state') and event.state.value in [
                "COMPLETED", "FAILED", "CANCELED"
            ]:
                print(f"Task finished with state: {event.state}")
                break

asyncio.run(ask_weather())
```

### Interactive Conversation

Build conversational agents that can request additional information:

```python
async def interactive_chat():
    key_manager = KeyManager(use_env_vars=True)
    agent_card = await fetch_agent_card_from_url(
        "https://api.example.com/agent-card.json"
    )
    
    async with AgentVaultClient() as client:
        # Start conversation
        task_id = await client.initiate_task(
            agent_card,
            Message(role="user", parts=[
                TextPart(content="I need help planning a trip")
            ]),
            key_manager
        )
        
        # Event handling loop
        while True:
            async for event in client.receive_messages(
                agent_card, task_id, key_manager
            ):
                if isinstance(event, TaskMessageEvent):
                    print(f"\nAgent: {event.message.parts[0].content}")
                    
                elif isinstance(event, TaskStatusUpdateEvent):
                    if event.state == TaskState.INPUT_REQUIRED:
                        # Agent needs input
                        user_input = input("\nYou: ")
                        
                        # Send response
                        await client.send_message(
                            agent_card,
                            task_id,
                            Message(role="user", parts=[
                                TextPart(content=user_input)
                            ]),
                            key_manager
                        )
                        break  # Exit inner loop to continue receiving
                    
                    elif event.state in [TaskState.COMPLETED, TaskState.FAILED]:
                        print(f"\nConversation ended: {event.state}")
                        return
```

## Advanced Features

### Working with Files and Artifacts

Handle file uploads and receive generated artifacts:

```python
from agentvault.models import FilePart, TaskArtifactUpdateEvent

async def process_document():
    # Message with file reference
    message = Message(
        role="user",
        parts=[
            TextPart(content="Please summarize this document:"),
            FilePart(
                url="https://example.com/report.pdf",
                media_type="application/pdf",
                filename="quarterly_report.pdf"
            )
        ]
    )
    
    async with AgentVaultClient() as client:
        task_id = await client.initiate_task(
            agent_card, message, key_manager
        )
        
        # Track artifacts
        artifacts = []
        
        async for event in client.receive_messages(
            agent_card, task_id, key_manager
        ):
            if isinstance(event, TaskArtifactUpdateEvent):
                artifacts.append(event.artifact)
                print(f"New artifact: {event.artifact.type} - {event.artifact.id}")
                
                # Download artifact if it has a URL
                if event.artifact.url:
                    async with httpx.AsyncClient() as http_client:
                        response = await http_client.get(event.artifact.url)
                        with open(f"output_{event.artifact.id}", "wb") as f:
                            f.write(response.content)
```

### Using MCP Context

Provide additional context using the Model Context Protocol:

```python
async def analyze_with_context():
    # Prepare MCP context
    mcp_context = {
        "resources": [
            {
                "type": "file",
                "uri": "file:///data/sales_2024.csv",
                "description": "Sales data for 2024"
            }
        ],
        "tools": [
            {
                "name": "sql_query",
                "description": "Execute SQL queries on the data"
            }
        ]
    }
    
    message = Message(
        role="user",
        parts=[TextPart(content="What were our top products by revenue?")]
    )
    
    async with AgentVaultClient() as client:
        task_id = await client.initiate_task(
            agent_card=agent_card,
            initial_message=message,
            key_manager=key_manager,
            mcp_context=mcp_context  # Embed context
        )
        
        # Process responses as usual
        async for event in client.receive_messages(
            agent_card, task_id, key_manager
        ):
            # Handle events...
```

### OAuth 2.0 Authentication

Work with agents that use OAuth authentication:

```python
async def oauth_agent_interaction():
    # Agent card with OAuth
    agent_card = AgentCard(
        # ... other fields ...
        auth_schemes=[
            AgentAuthentication(
                scheme="oauth2",
                service_identifier="github-agent",
                token_url="https://github.com/login/oauth/access_token",
                scopes=["repo", "user"]
            )
        ]
    )
    
    # Ensure OAuth credentials are configured
    key_manager = KeyManager(use_keyring=True)
    
    # Check if credentials exist
    status = key_manager.get_oauth_config_status("github-agent")
    if status == "Not Configured":
        # Set them programmatically or prompt user
        key_manager.set_oauth_creds_in_keyring(
            "github-agent",
            client_id=input("Enter GitHub OAuth Client ID: "),
            client_secret=input("Enter GitHub OAuth Client Secret: ")
        )
    
    # Use normally - library handles token exchange
    async with AgentVaultClient() as client:
        task_id = await client.initiate_task(
            agent_card, message, key_manager
        )
```

### Webhook Integration

Receive updates via webhooks instead of SSE:

```python
from fastapi import FastAPI, Request
import asyncio

app = FastAPI()
event_queue = asyncio.Queue()

@app.post("/webhooks/agent-updates")
async def webhook_handler(request: Request):
    # Store event for processing
    data = await request.json()
    await event_queue.put(data)
    return {"status": "received"}

async def process_with_webhooks():
    async with AgentVaultClient() as client:
        # Initiate with webhook
        task_id = await client.initiate_task(
            agent_card,
            message,
            key_manager,
            webhook_url="https://myapp.com/webhooks/agent-updates"
        )
        
        # Process webhook events
        while True:
            event_data = await event_queue.get()
            print(f"Webhook event: {event_data}")
            
            # Check if task is complete
            if event_data.get("state") in ["COMPLETED", "FAILED"]:
                break
```

### Parallel Agent Interactions

Query multiple agents concurrently:

```python
async def query_multiple_agents():
    agents = [
        ("weather-bot", "What's the weather?"),
        ("news-bot", "What's the latest news?"),
        ("stock-bot", "How's the market?")
    ]
    
    async def query_agent(agent_id: str, question: str):
        agent_card = await fetch_agent_card_from_url(
            f"https://api.example.com/{agent_id}/card.json"
        )
        
        message = Message(
            role="user",
            parts=[TextPart(content=question)]
        )
        
        async with AgentVaultClient() as client:
            task_id = await client.initiate_task(
                agent_card, message, key_manager
            )
            
            # Get first response
            async for event in client.receive_messages(
                agent_card, task_id, key_manager
            ):
                if isinstance(event, TaskMessageEvent):
                    return event.message.parts[0].content
    
    # Query all agents in parallel
    results = await asyncio.gather(*[
        query_agent(agent_id, question)
        for agent_id, question in agents
    ])
    
    for (agent_id, _), result in zip(agents, results):
        print(f"{agent_id}: {result}")
```

## Error Handling

Implement robust error handling for production applications:

```python
from agentvault.exceptions import (
    A2AAuthenticationError,
    A2ATimeoutError,
    A2ARemoteAgentError,
    AgentCardFetchError
)

async def robust_interaction():
    max_retries = 3
    retry_delay = 5.0
    
    for attempt in range(max_retries):
        try:
            # Try to fetch agent card
            agent_card = await fetch_agent_card_from_url(
                "https://api.example.com/agent-card.json"
            )
            
            async with AgentVaultClient(default_timeout=60.0) as client:
                task_id = await client.initiate_task(
                    agent_card, message, key_manager
                )
                
                # Success - process normally
                break
                
        except AgentCardFetchError as e:
            print(f"Failed to fetch agent card: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            raise
            
        except A2AAuthenticationError as e:
            print(f"Authentication failed: {e}")
            # Check credentials
            source = key_manager.get_key_source(
                agent_card.auth_schemes[0].service_identifier
            )
            print(f"Key source: {source}")
            raise
            
        except A2ATimeoutError as e:
            print(f"Request timed out: {e}")
            if attempt < max_retries - 1:
                print("Retrying with longer timeout...")
                continue
            raise
            
        except A2ARemoteAgentError as e:
            print(f"Agent error ({e.status_code}): {e.message}")
            if e.status_code >= 500:
                # Server error - might be temporary
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
            raise
```

## Best Practices

### 1. Resource Management

Always use context managers to ensure proper cleanup:

```python
# Good - automatic cleanup
async with AgentVaultClient() as client:
    # Use client
    pass

# Also good for explicit cleanup
client = AgentVaultClient()
try:
    # Use client
    pass
finally:
    await client.close()
```

### 2. Credential Security

- Never hardcode credentials in source code
- Use environment variables for CI/CD
- Use key files for local development
- Use OS keyring for production
- Rotate credentials regularly

### 3. Logging Configuration

Configure logging for debugging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set specific levels
logging.getLogger("agentvault.client").setLevel(logging.DEBUG)
logging.getLogger("agentvault.key_manager").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
```

### 4. Custom HTTP Client

Configure the HTTP client for specific requirements:

```python
import httpx

async def custom_client_setup():
    # Configure custom HTTP client
    custom_client = httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100
        ),
        headers={
            "User-Agent": "MyApp/1.0"
        },
        verify="/path/to/custom/ca-bundle.crt"
    )
    
    # Use with AgentVaultClient
    async with AgentVaultClient(
        http_client=custom_client,
        default_timeout=120.0
    ) as client:
        # Client will use custom settings
        pass
```

## Performance Tips

1. **Reuse Clients**: Create one `AgentVaultClient` for multiple operations
2. **Cache Agent Cards**: Don't fetch the same card repeatedly
3. **Use Connection Pooling**: The default httpx client pools connections
4. **Stream Large Responses**: Use SSE for long-running tasks
5. **Batch Operations**: Some agents support batch processing

## Troubleshooting

### Common Issues

**SSL Certificate Errors**
```python
# For development only - disable SSL verification
client = httpx.AsyncClient(verify=False)
```

**Timeout Issues**
```python
# Increase timeout for slow agents
client = AgentVaultClient(default_timeout=300.0)  # 5 minutes
```

**Authentication Failures**
```python
# Debug credential loading
key_manager = KeyManager(use_env_vars=True)
print(f"Key source: {key_manager.get_key_source('service-id')}")
print(f"OAuth status: {key_manager.get_oauth_config_status('service-id')}")
```

**SSE Connection Drops**
```python
# Normal for long streams - implement reconnection
while True:
    try:
        async for event in client.receive_messages(...):
            # Process events
            pass
        break  # Normal completion
    except A2AConnectionError:
        # Reconnect after delay
        await asyncio.sleep(5)
        continue
```

## Next Steps

- Explore the [Library API Reference](../AGENTVAULT_LIBRARY_API.md) for detailed documentation
- Check example agents in the repository
- Join the community discussions
- Contribute to the library development

---

The AgentVault Library provides a powerful, flexible client for interacting with agents in the Sovereign Stack ecosystem. With support for multiple authentication methods, streaming responses, and robust error handling, it's the foundation for building agent-powered applications.
