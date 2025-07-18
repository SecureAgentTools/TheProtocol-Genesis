# Quickstart: Your First Agent in 15 Minutes

Welcome to The Protocol! This guide will get you from zero to your first working agent in just 15 minutes. We'll use Docker Compose to skip complex setup and jump straight into the action.

## Prerequisites Check (2 minutes)

You'll need:
- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** (3.10 or 3.11) 
- **Git**
- **curl** or a REST client

Quick check:
```bash
docker --version      # Should show 20.10 or higher
docker compose version # Should show 2.0 or higher
python --version      # Should show 3.10 or 3.11
git --version         # Any recent version
```

Missing something? See our [detailed installation guide](installation.md) for setup instructions.

## Step 1: Clone and Start the Stack (3 minutes)

```bash
# Clone the repository
git clone https://github.com/SecureAgentTools/SovereignStack.git
cd SovereignStack

# Start everything with one command
docker compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30

# Verify the stack is running
curl http://localhost:8000/health
```

You should see: `{"status": "healthy", "service": "agentvault-registry"}`

## Step 2: Install the CLI (2 minutes)

```bash
# Install Poetry (if you don't have it)
curl -sSL https://install.python-poetry.org | python3 -

# Install the Sovereign Stack CLI
poetry install

# Enter the Poetry shell
poetry shell

# Verify CLI is working
agentvault_cli --version
```

## Step 3: Create Your Developer Account (2 minutes)

```bash
# Register a new developer account
agentvault_cli auth register \
  --email developer@example.com \
  --password SecurePass123! \
  --registry-url http://localhost:8000

# Login to get your session
agentvault_cli auth login \
  --email developer@example.com \
  --password SecurePass123!
```

You'll see: `✓ Login successful! Token saved.`

## Step 4: Generate a Bootstrap Token (2 minutes)

Bootstrap tokens allow agents to self-register into the network:

```bash
# Request a bootstrap token for your agent
agentvault_cli onboard request-token \
  --agent-type "demo-agent" \
  --stake-amount 10.0
```

You'll receive a token like: `bs_Kz3mFp8nQr5tWx9vYc2dLa7jHg4sBn6u`

Save this token - your agent needs it to join the network!

## Step 5: Deploy the Echo Agent (3 minutes)

Let's deploy a simple echo agent that demonstrates the core functionality:

```bash
# Create a working directory for your agent
mkdir my-first-agent
cd my-first-agent

# Create the agent configuration
cat > agent-config.json << EOF
{
  "name": "My Echo Agent",
  "did": "did:agentvault:my-echo-agent",
  "type": "echo-agent",
  "bootstrap_token": "YOUR_BOOTSTRAP_TOKEN_HERE"
}
EOF

# Create a simple echo agent
cat > echo_agent.py << EOF
#!/usr/bin/env python3
from agentvault_library import AgentVaultClient
import json
import asyncio

async def main():
    # Load configuration
    with open('agent-config.json') as f:
        config = json.load(f)
    
    # Initialize client
    client = AgentVaultClient(
        registry_url="http://localhost:8000",
        agent_did=config['did']
    )
    
    # Self-register using bootstrap token
    print(f"🤖 Registering {config['name']}...")
    await client.register_with_bootstrap_token(
        config['bootstrap_token'],
        config['name'],
        {"description": "A simple echo agent", "version": "1.0.0"}
    )
    
    print("✅ Agent registered successfully!")
    print("📡 Listening for messages...")
    
    # Simple message handler
    async def handle_message(message):
        print(f"📨 Received: {message['content']}")
        return {"echo": message['content'], "timestamp": message.get('timestamp')}
    
    # Start listening
    await client.listen_for_messages(handle_message)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Make it executable
chmod +x echo_agent.py
```

Replace `YOUR_BOOTSTRAP_TOKEN_HERE` with the token from Step 4, then run:

```bash
# Run your agent
python echo_agent.py
```

## Step 6: Interact with Your Agent (1 minute)

In a new terminal, send a message to your agent:

```bash
# Send a test message
curl -X POST http://localhost:8000/api/v1/agents/did:agentvault:my-echo-agent/message \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, Agent!",
    "timestamp": "2025-01-20T10:00:00Z"
  }'
```

Your agent will echo back the message! Check the agent terminal to see the interaction.

## 🎉 Congratulations!

You've just:
- ✅ Deployed the entire Sovereign Stack
- ✅ Created a developer account
- ✅ Generated a bootstrap token with economic stake
- ✅ Built and deployed your first agent
- ✅ Sent a message through the decentralized network

**Total time: ~15 minutes!**

## What Just Happened?

Behind the scenes, you've interacted with:
- **Registry Service**: Managed agent identity and discovery
- **TEG Layer**: Handled economic staking (10 tokens)
- **Identity Fabric**: Secured agent communications
- **Federation Protocol**: Enabled cross-registry discovery

Your echo agent is now:
- Cryptographically identified with a DID
- Economically staked in the network
- Ready to interact with other agents
- Discoverable across federated registries

## Next Steps

### Enhance Your Agent
- Add persistent state management
- Implement custom message protocols
- Connect to external services
- Add dispute handling logic

### Explore the Economics
- Learn about [staking and reputation](../architecture/teg_layer.md)
- Understand [attestations and disputes](../AGENTVAULT_TEG_LAYER_ECONOMICS.md)
- Monitor your agent's economic activity

### Build Something Real
Check out our example agents:
- [Data Processor Agent](../developer-guides/agent-examples/data-processor.md) - Process data with economic guarantees
- [Marketplace Agent](../developer-guides/agent-examples/marketplace-agent.md) - Buy and sell services
- [Federation Gateway](../developer-guides/agent-examples/federation-gateway.md) - Bridge between registries

### Deep Dive
- [Building an Agent](../developer-guides/building-an-agent.md) - Comprehensive agent development
- [Architecture Overview](../architecture/overview.md) - Understand the full system
- [CLI Reference](../developer-guides/cli-reference.md) - Master all commands

## Troubleshooting

**Services not starting?**
```bash
docker compose logs -f  # Check for errors
docker compose down && docker compose up -d  # Restart everything
```

**Can't register agent?**
- Verify your bootstrap token is correct
- Check the token hasn't expired (24 hour validity)
- Ensure you're logged in: `agentvault_cli auth status`

**Connection refused?**
- Verify services are healthy: `curl http://localhost:8000/health`
- Check Docker is running: `docker ps`
- Ensure no firewall is blocking ports

**Need more help?**
- Check our [comprehensive troubleshooting guide](../troubleshooting/common-issues.md)
- Search [GitHub issues](https://github.com/SecureAgentTools/SovereignStack/issues)
- Join our developer community

---

*"The journey of a thousand agents begins with a single echo."*  
**- The Warrior Owl Doctrine**

Remember: You've just deployed a production-grade, cryptographically-secured, economically-incentivized agent network. In 15 minutes. Welcome to the future of autonomous systems!
