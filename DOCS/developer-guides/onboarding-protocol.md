# Onboarding Protocol

## Overview

The AgentVault Onboarding Protocol is a secure, two-phase process that enables controlled agent creation while preventing abuse. It ensures every agent can be traced to an authenticated creator, provides Sybil resistance through rate limiting, and establishes a chain of accountability.

## Why Two-Phase Onboarding?

Traditional agent creation faces several challenges:

1. **Sybil Attacks**: Bad actors creating thousands of fake agents
2. **Accountability**: No way to trace who created which agents
3. **Resource Abuse**: Unchecked creation overwhelming the network
4. **Initial Funding**: How to bootstrap new agents with tokens

The two-phase protocol solves these issues elegantly:

```
Phase 1: Creator Authentication → Bootstrap Token
Phase 2: Agent Self-Registration → DID + Credentials
```

## Phase 1: Bootstrap Token Creation

### Prerequisites

- Authenticated developer account
- Verified email address
- Valid JWT access token

### Process

1. **Developer Authentication**
   ```bash
   # Using the CLI
   agentvault agent onboard --agent-type "trading-bot"
   
   # This initiates OAuth device flow:
   # 1. CLI requests device code
   # 2. User authenticates in browser
   # 3. CLI receives access token
   ```

2. **Token Request**
   ```http
   POST /api/v1/onboard/bootstrap/request-token
   Authorization: Bearer <developer_jwt_token>
   Content-Type: application/json
   
   {
     "agent_type_hint": "trading-bot",
     "requested_by": "alice@example.com"
   }
   ```

3. **Token Response**
   ```json
   {
     "bootstrap_token": "bst_a1b2c3d4_e5f6g7h8",
     "expires_in": 300,
     "expires_at": "2024-01-01T12:05:00Z"
   }
   ```

### Security Features

- **Rate Limiting**: 5 tokens/minute per developer
- **Short Lifetime**: 5-minute expiration
- **Single Use**: Token consumed on successful registration
- **Audit Trail**: All tokens linked to creator

## Phase 2: Agent Registration

### Prerequisites

- Valid bootstrap token
- Agent code ready to run
- Optional: Public key for identity

### Process

1. **Agent Initialization**
   ```python
   from agentvault import register_agent_with_bootstrap_token
   
   # Received from creator
   bootstrap_token = "bst_a1b2c3d4_e5f6g7h8"
   
   # Register with registry
   agent_did, client_id, client_secret = await register_agent_with_bootstrap_token(
       registry_onboarding_url="https://registry.agentvault.com/api/v1/onboard/register",
       bootstrap_token=bootstrap_token,
       did_method="cos"  # Concierge-OS native DID
   )
   
   # Store credentials securely
   save_agent_credentials(agent_did, client_id, client_secret)
   ```

2. **Registration Request**
   ```http
   POST /api/v1/onboard/register
   Bootstrap-Token: bst_a1b2c3d4_e5f6g7h8
   Content-Type: application/json
   
   {
     "agent_did_method": "cos",
     "public_key_jwk": {
       "kty": "EC",
       "crv": "P-256",
       "x": "base64_x_coordinate",
       "y": "base64_y_coordinate"
     },
     "proof_of_work_solution": "0x0000abcd..."  // Optional
   }
   ```

3. **Registration Response**
   ```json
   {
     "agent_did": "did:cos:1234abcd-5678-efgh-9012-ijkl",
     "client_id": "agent-1a2b3c4d5e6f7g8h",
     "client_secret": "cos_secret_<64-char-hex>",
     "account_status": "active",
     "initial_funding_status": "pending",
     "faucet_transaction_id": "tx_faucet_abc123"
   }
   ```

### DID Methods

Currently supported:
- **`cos`**: Concierge-OS native DIDs (format: `did:cos:<uuid-style>`)

Future support planned:
- **`key`**: Self-describing key-based DIDs
- **`web`**: Domain-linked DIDs
- **`ion`**: Decentralized identifiers on Bitcoin

## Implementation Guide

### For Creators (Phase 1)

#### Using the CLI

```bash
# Simple onboarding
agentvault agent onboard

# With metadata
agentvault agent onboard \
  --agent-type "market-maker" \
  --requested-by "team-alpha"

# Output:
# Bootstrap Token: bst_xxx_yyy
# Expires in: 300 seconds
# Share this token with your agent!
```

#### Using the API

```python
import httpx
from datetime import datetime

async def create_bootstrap_token(access_token: str, agent_type: str = None):
    """Request a bootstrap token for agent creation."""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://registry.agentvault.com/api/v1/onboard/bootstrap/request-token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "agent_type_hint": agent_type,
                "requested_by": "my-automation-script"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Token: {data['bootstrap_token']}")
            print(f"Expires: {data['expires_at']}")
            return data['bootstrap_token']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
```

### For Agents (Phase 2)

#### Basic Registration

```python
# agent_startup.py
import asyncio
import os
from agentvault import register_agent_with_bootstrap_token

async def initialize_agent():
    """Complete agent registration on first startup."""
    
    # Check if already registered
    if os.path.exists(".agent_credentials"):
        print("Agent already registered")
        return load_existing_credentials()
    
    # Get bootstrap token (from env, file, or input)
    bootstrap_token = os.getenv("BOOTSTRAP_TOKEN")
    if not bootstrap_token:
        bootstrap_token = input("Enter bootstrap token: ")
    
    try:
        # Register with registry
        agent_did, client_id, client_secret = await register_agent_with_bootstrap_token(
            registry_onboarding_url="https://registry.agentvault.com/api/v1/onboard/register",
            bootstrap_token=bootstrap_token
        )
        
        # Save credentials securely
        save_credentials(agent_did, client_id, client_secret)
        
        print(f"✅ Registration successful!")
        print(f"Agent DID: {agent_did}")
        print(f"Client ID: {client_id}")
        
        return agent_did, client_id, client_secret
        
    except OnboardingError as e:
        print(f"❌ Registration failed: {e}")
        if "expired" in str(e):
            print("Token has expired. Request a new one from your creator.")
        elif "already used" in str(e):
            print("Token was already used. Each token is single-use only.")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_agent())
```

#### Advanced Registration with Public Key

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import json
import base64

def generate_agent_keypair():
    """Generate an EC keypair for the agent."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Convert to JWK format
    public_numbers = public_key.public_numbers()
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": base64.urlsafe_b64encode(
            public_numbers.x.to_bytes(32, 'big')
        ).decode().rstrip('='),
        "y": base64.urlsafe_b64encode(
            public_numbers.y.to_bytes(32, 'big')
        ).decode().rstrip('=')
    }
    
    return private_key, jwk

async def register_with_identity():
    """Register agent with cryptographic identity."""
    
    # Generate keypair
    private_key, public_jwk = generate_agent_keypair()
    
    # Register with public key
    agent_did, client_id, client_secret = await register_agent_with_bootstrap_token(
        registry_onboarding_url="https://registry.agentvault.com/api/v1/onboard/register",
        bootstrap_token=bootstrap_token,
        did_method="cos",
        public_key_jwk=public_jwk
    )
    
    # Save private key securely
    save_private_key(private_key, agent_did)
    
    return agent_did, client_id, client_secret
```

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `401: Invalid token` | Token expired or wrong | Request new token |
| `400: Token already used` | Token was consumed | Each token is single-use |
| `429: Rate limit exceeded` | Too many requests | Wait and retry |
| `403: Not verified` | Creator not verified | Verify email first |
| `400: Invalid DID method` | Unsupported method | Use "cos" |

### Retry Strategy

```python
import asyncio
from typing import Optional

async def register_with_retry(
    token: str, 
    max_retries: int = 3,
    backoff_base: float = 2.0
) -> tuple[str, str, str]:
    """Register with exponential backoff retry."""
    
    last_error: Optional[Exception] = None
    
    for attempt in range(max_retries):
        try:
            return await register_agent_with_bootstrap_token(
                registry_onboarding_url=REGISTRY_URL,
                bootstrap_token=token
            )
        except OnboardingError as e:
            last_error = e
            
            # Don't retry on permanent failures
            if e.status_code in [400, 401]:
                raise
            
            # Exponential backoff for temporary failures
            if attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                print(f"Retry {attempt + 1} after {wait_time}s...")
                await asyncio.sleep(wait_time)
    
    raise last_error or OnboardingError("Registration failed after retries")
```

## Security Considerations

### For Creators

1. **Token Handling**
   - Never share tokens in public channels
   - Use secure communication for token transfer
   - Consider automating token injection

2. **Rate Limit Management**
   - Implement token request queuing
   - Monitor usage patterns
   - Plan for burst creation needs

3. **Audit Trail**
   - Log all token creations
   - Track which agents use which tokens
   - Monitor for anomalies

### For Agents

1. **Credential Storage**
   ```python
   import keyring
   from cryptography.fernet import Fernet
   
   def save_credentials_securely(agent_did: str, client_id: str, client_secret: str):
       """Store credentials using OS keyring or encrypted file."""
       
       # Option 1: OS Keyring (preferred)
       try:
           keyring.set_password("agentvault", f"{agent_did}_client_id", client_id)
           keyring.set_password("agentvault", f"{agent_did}_client_secret", client_secret)
           return
       except Exception:
           pass
       
       # Option 2: Encrypted file (fallback)
       key = Fernet.generate_key()
       cipher = Fernet(key)
       
       credentials = {
           "agent_did": agent_did,
           "client_id": client_id,
           "client_secret": cipher.encrypt(client_secret.encode()).decode()
       }
       
       # Save encrypted
       with open(".agent_credentials", "w") as f:
           json.dump(credentials, f)
       
       # Save key separately (or derive from passphrase)
       with open(".agent_key", "wb") as f:
           f.write(key)
   ```

2. **Bootstrap Token Security**
   - Never hardcode tokens
   - Clear from memory after use
   - Don't log token values

3. **Network Security**
   - Always use HTTPS
   - Verify SSL certificates
   - Implement request timeouts

## Best Practices

### Automated Agent Deployment

```python
# deploy_agent.py
import asyncio
import subprocess
import os

async def deploy_new_agent(agent_config: dict):
    """Automated agent deployment pipeline."""
    
    # Step 1: Request bootstrap token
    token = await request_bootstrap_token(
        agent_type=agent_config["type"]
    )
    
    # Step 2: Deploy agent container
    env_vars = {
        "BOOTSTRAP_TOKEN": token,
        "AGENT_NAME": agent_config["name"],
        "REGISTRY_URL": "https://registry.agentvault.com"
    }
    
    subprocess.run([
        "docker", "run", "-d",
        "--name", agent_config["name"],
        *[f"-e {k}={v}" for k, v in env_vars.items()],
        agent_config["image"]
    ])
    
    # Step 3: Monitor registration
    await monitor_agent_startup(agent_config["name"])
```

### Multi-Agent Orchestration

```python
class AgentFleet:
    """Manage multiple agent deployments."""
    
    def __init__(self, creator_token: str):
        self.creator_token = creator_token
        self.agents = {}
    
    async def spawn_agent(self, agent_type: str, config: dict):
        """Spawn a new agent in the fleet."""
        
        # Request bootstrap token
        token = await self.request_bootstrap_token(agent_type)
        
        # Create agent instance
        agent = Agent(config)
        
        # Register agent
        credentials = await agent.register(token)
        
        # Track in fleet
        self.agents[credentials.agent_did] = agent
        
        return agent
    
    async def spawn_fleet(self, fleet_config: list[dict]):
        """Spawn multiple agents concurrently."""
        
        tasks = []
        for config in fleet_config:
            task = self.spawn_agent(
                config["type"], 
                config["settings"]
            )
            tasks.append(task)
        
        # Concurrent spawning with rate limit respect
        agents = []
        for task in asyncio.as_completed(tasks):
            agent = await task
            agents.append(agent)
            await asyncio.sleep(12)  # Respect 5/minute limit
        
        return agents
```

## Monitoring and Analytics

### Token Usage Tracking

```sql
-- Token creation and usage analytics
SELECT 
    d.name as creator_name,
    COUNT(bt.id) as tokens_created,
    COUNT(CASE WHEN bt.used_at IS NOT NULL THEN 1 END) as tokens_used,
    COUNT(CASE WHEN bt.expires_at < NOW() AND bt.used_at IS NULL THEN 1 END) as tokens_expired,
    AVG(EXTRACT(EPOCH FROM (bt.used_at - bt.created_at))) as avg_time_to_use_seconds
FROM bootstrap_tokens bt
JOIN developers d ON bt.creator_developer_id = d.id
WHERE bt.created_at > NOW() - INTERVAL '7 days'
GROUP BY d.id, d.name
ORDER BY tokens_created DESC;
```

### Agent Creation Patterns

```python
import pandas as pd
import matplotlib.pyplot as plt

def analyze_onboarding_patterns(registry_api_url: str, api_key: str):
    """Analyze agent creation patterns over time."""
    
    # Fetch data
    response = requests.get(
        f"{registry_api_url}/api/v1/analytics/onboarding",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data["daily_stats"])
    df['date'] = pd.to_datetime(df['date'])
    
    # Plot creation patterns
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Daily creations
    ax1.plot(df['date'], df['agents_created'], label='Agents Created')
    ax1.plot(df['date'], df['tokens_created'], label='Tokens Created')
    ax1.set_title('Daily Agent Creation Activity')
    ax1.legend()
    
    # Success rate
    df['success_rate'] = df['tokens_used'] / df['tokens_created'] * 100
    ax2.plot(df['date'], df['success_rate'])
    ax2.set_title('Token Usage Success Rate (%)')
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    return fig
```

## Future Enhancements

1. **Delegated Creation**
   - Allow agents to create sub-agents
   - Hierarchical accountability chains
   - Resource inheritance

2. **Proof-of-Work Integration**
   - Adaptive difficulty based on network load
   - GPU-resistant algorithms
   - Economic incentives for computation

3. **Batch Onboarding**
   - Create multiple agents with one token
   - Fleet deployment optimization
   - Atomic group creation

4. **Cross-Registry Federation**
   - Portable agent identities
   - Registry-to-registry transfers
   - Unified reputation system

---

The Onboarding Protocol ensures that every agent in the Sovereign Stack has a verified creator, preventing spam while enabling innovation. By separating authentication from registration, it provides security without sacrificing autonomy - a foundational principle of the decentralized agent economy.
