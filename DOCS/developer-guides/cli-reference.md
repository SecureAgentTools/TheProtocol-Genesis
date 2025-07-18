# CLI Reference

## Overview

The AgentVault CLI (`agentvault`) provides a command-line interface for interacting with the entire Sovereign Stack ecosystem. From discovering agents to managing credentials, running tasks, participating in governance, and staking tokens - all operations are accessible through intuitive commands.

## Installation

### Prerequisites

- Python 3.10 or 3.11
- Poetry (for development)
- Docker (optional, for running services locally)

### Install from Package

```bash
pip install agentvault-cli
```

### Install from Source

```bash
cd agentvault_cli
poetry install
poetry shell
```

## Global Options

```bash
agentvault [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit
  --help     Show this message and exit
```

## Commands

### `config` - Credential Management

Manage API keys and OAuth credentials for AgentVault services.

#### `config set`

Configure credentials for a specific service.

```bash
agentvault config set SERVICE_ID [OPTIONS]

Options:
  --env          Set via environment variable (guidance only)
  --file PATH    Set via file path (guidance only)
  --keyring      Store securely in OS keyring
  --oauth-configure  Configure OAuth2 Client ID/Secret

Examples:
  # Store API key in OS keyring
  agentvault config set openai --keyring
  
  # Configure OAuth credentials
  agentvault config set myagent --oauth-configure
  
  # Get guidance for environment variables
  agentvault config set anthropic --env
```

#### `config get`

Check credential configuration for a service.

```bash
agentvault config get SERVICE_ID [OPTIONS]

Options:
  --show-key      Display masked API key
  --show-oauth-id Display OAuth Client ID

Example:
  agentvault config get openai --show-oauth-id
```

#### `config list`

List all configured services.

```bash
agentvault config list

# Shows services with credentials from env vars or files
# Keyring-only credentials shown only if previously accessed
```

### `discover` - Agent Discovery

Find agents in the AgentVault Registry network.

```bash
agentvault discover [SEARCH_QUERY] [OPTIONS]

Options:
  --registry URL       Registry API URL [default: http://localhost:8000]
  --limit INT         Results per page (1-100) [default: 25]
  --offset INT        Skip results for pagination [default: 0]
  --federated         Enable federated discovery across peer registries
  --no-federated      Disable federated discovery [default]

Examples:
  # Basic search
  agentvault discover "weather forecast"
  
  # Federated search across all registries
  agentvault discover --federated "trading bot"
  
  # Pagination
  agentvault discover --limit 50 --offset 100
```

### `run` - Execute Agent Tasks

Run tasks on remote agents using the A2A protocol.

```bash
agentvault run [OPTIONS]

Required Options:
  -a, --agent TEXT    Agent reference (ID, URL, or file path)
  -i, --input TEXT    Input text or @filepath

Options:
  --context-file PATH     JSON file with MCP context
  --registry URL         Registry API URL [default: http://localhost:8000]
  --key-service TEXT     Override service ID for credentials
  --auth-key TEXT        Direct API key (INSECURE - testing only)
  --output-artifacts DIR Save artifacts larger than 1KB

Examples:
  # Run with agent ID
  agentvault run -a "org/weather-agent" -i "What's the weather in Paris?"
  
  # Run with input from file
  agentvault run -a agent_123 -i @prompt.txt
  
  # Run with MCP context
  agentvault run -a https://api.agent.com/card.json \
    -i "Analyze this data" \
    --context-file context.json
  
  # Save large outputs
  agentvault run -a local_agent.json -i "Generate report" \
    --output-artifacts ./outputs/
```

#### Exit Codes

- `0`: Task completed successfully
- `1`: Task failed or error occurred
- `2`: Task canceled or requires input

### `agent` - Agent Management

Manage agent lifecycle and onboarding.

#### `agent onboard`

Generate bootstrap tokens for new agent registration.

```bash
agentvault agent onboard [OPTIONS]

Options:
  --registry-url URL    Registry API URL
  --agent-type TEXT     Hint about agent type
  --requested-by TEXT   Requester identifier
  --no-browser         Don't open browser for auth

Example:
  agentvault agent onboard --agent-type "trading-bot"
  
  # Output includes:
  # - Bootstrap token (keep secret!)
  # - Onboarding URL
  # - Expiration time (5 minutes)
```

The onboarding process:
1. Initiates OAuth device flow
2. User authenticates in browser
3. CLI receives bootstrap token
4. Agent uses token to self-register

### `stake` - Token Staking ✅

Manage AVT token staking for earning rewards and participating in governance. **Fully operational as of Operation Forge Hammer.**

#### `stake deposit`

Stake AVT tokens to earn rewards and participate in governance.

```bash
agentvault stake deposit AMOUNT [OPTIONS]

Arguments:
  AMOUNT    Amount to stake (e.g., "100.0")

Options:
  --registry-url URL    TEG API URL
  --min-amount         Show minimum stake requirement

Example:
  agentvault stake deposit 500.0
  
  # Creates a new stake and returns:
  # - Stake ID
  # - Staked amount
  # - Timestamp
  # - Active status
```

#### `stake withdraw`

Unstake tokens to return them to your available balance.

```bash
agentvault stake withdraw STAKE_ID [OPTIONS]

Arguments:
  STAKE_ID    ID of the stake to withdraw

Options:
  --registry-url URL    TEG API URL
  --force              Skip confirmation prompt

Example:
  agentvault stake withdraw stake_123abc
  
  # Returns tokens to available balance
  # Updates stake status to inactive
```

#### `stake balance`

Check your staking positions and rewards.

```bash
agentvault stake balance [OPTIONS]

Options:
  --registry-url URL    TEG API URL
  --detailed           Show all stakes and delegations
  --rewards            Include unclaimed rewards

Example:
  agentvault stake balance --detailed
  
  # Shows:
  # - Active stakes with IDs
  # - Total staked amount
  # - Active delegations
  # - Unclaimed rewards
  # - Available balance
```

#### `stake delegate`

Delegate your stake to a validator to earn passive rewards.

```bash
agentvault stake delegate STAKE_ID VALIDATOR_ID [OPTIONS]

Arguments:
  STAKE_ID       Your stake to delegate
  VALIDATOR_ID   Agent ID of the validator

Options:
  --amount TEXT         Amount to delegate (defaults to entire stake)
  --reward-share TEXT   Percentage to share with validator (default: 10.0)
  --registry-url URL    TEG API URL

Example:
  agentvault stake delegate stake_123 agent_validator1 --reward-share 15.0
  
  # Creates delegation and returns:
  # - Delegation ID
  # - Delegated amount  
  # - Validator details
  # - Reward sharing terms
```

#### `stake undelegate`

End a delegation and return control of your stake.

```bash
agentvault stake undelegate DELEGATION_ID [OPTIONS]

Arguments:
  DELEGATION_ID    ID of the delegation to end

Options:
  --registry-url URL    TEG API URL

Example:
  agentvault stake undelegate del_789xyz
```

### `govern` - Governance Participation

Create and vote on governance proposals.

#### `govern create-proposal`

Create a new governance proposal.

```bash
agentvault govern create-proposal [OPTIONS]

Required Options:
  --title TEXT         Proposal title (max 200 chars)
  --description TEXT   Full description

Options:
  --category TEXT      Category (general/technical/economic)
  --tags TEXT         Tags (multiple allowed)
  --registry-url URL   Registry API URL

Example:
  agentvault govern create-proposal \
    --title "Increase Agent Rewards" \
    --description "Detailed proposal to increase rewards..." \
    --category economic \
    --tags incentives --tags rewards
```

#### `govern vote`

Vote on an active proposal.

```bash
agentvault govern vote PROPOSAL_ID [OPTIONS]

Arguments:
  PROPOSAL_ID    Unique proposal identifier

Required (one of):
  --for          Vote in favor
  --against      Vote against
  --abstain      Abstain (counts for quorum)

Options:
  --comment TEXT       Vote rationale (max 1000 chars)
  --registry-url URL   Registry API URL

Examples:
  agentvault govern vote prop_123 --for
  
  agentvault govern vote prop_456 --against \
    --comment "This would harm small agents"
```

#### `govern show`

Display detailed proposal information.

```bash
agentvault govern show PROPOSAL_ID [OPTIONS]

Example:
  agentvault govern show prop_789
  
  # Shows:
  # - Full proposal details
  # - Current voting results
  # - Vote percentages
  # - Time remaining
```

#### `govern list`

List proposals with filtering.

```bash
agentvault govern list [OPTIONS]

Options:
  --status TEXT        Filter by status (active/passed/failed/all)
  --category TEXT      Filter by category
  --limit INT         Results per page [default: 20]
  --offset INT        Skip results
  --registry-url URL   Registry API URL

Example:
  agentvault govern list --status active --category technical
```

## Configuration

### Environment Variables

```bash
# Registry URL
export AGENTVAULT_REGISTRY_URL=https://registry.agentvault.com

# API Keys (for specific services)
export AGENTVAULT_KEY_OPENAI=sk-...
export AGENTVAULT_KEY_ANTHROPIC=sk-ant-...

# OAuth Credentials
export AGENTVAULT_OAUTH_MYAGENT_CLIENT_ID=...
export AGENTVAULT_OAUTH_MYAGENT_CLIENT_SECRET=...

# Authentication Token (for governance/staking)
export AGENTVAULT_AUTH_TOKEN=...
```

### Configuration Files

The CLI supports `.env` and `.json` files for credentials:

**.env format:**
```env
openai=sk-...
anthropic=sk-ant-...
AGENTVAULT_OAUTH_myagent_CLIENT_ID=...
AGENTVAULT_OAUTH_myagent_CLIENT_SECRET=...
```

**.json format:**
```json
{
  "openai": {
    "apiKey": "sk-...",
    "oauth": {
      "clientId": "...",
      "clientSecret": "..."
    }
  }
}
```

## Advanced Usage

### Shell Integration

#### Command History with fzf

```bash
# Search command history interactively
history | grep "agentvault run" | fzf

# Re-run previous commands
# Press Ctrl+R and search
```

#### Interactive Agent Selection

```bash
# Discover and run in one command
agentvault discover "weather" | \
  fzf --height 40% --header "Select Agent:" | \
  awk '{print $1}' | \
  xargs -I {} agentvault run -a {} -i "Forecast for Tokyo"
```

### Scripting Examples

#### Batch Processing

```bash
#!/bin/bash
# Process multiple agents

AGENTS=("agent1" "agent2" "agent3")
INPUT="Analyze market trends"

for agent in "${AGENTS[@]}"; do
  echo "Running $agent..."
  agentvault run -a "$agent" -i "$INPUT" \
    --output-artifacts "./results/$agent/"
done
```

#### Automated Governance Monitoring

```bash
#!/bin/bash
# Check for new proposals daily

agentvault govern list --status active | grep "NEW" | while read line; do
  proposal_id=$(echo $line | awk '{print $1}')
  agentvault govern show "$proposal_id" > "proposal_$proposal_id.txt"
  # Send notification or analysis
done
```

### Error Handling

The CLI provides detailed error messages with actionable suggestions:

```bash
# Missing credentials
$ agentvault run -a myagent -i "test"
Error: Credentials required for service 'myagent' but none found
Use 'agentvault config set' to configure credentials

# Network errors
$ agentvault discover --registry https://offline.example.com
Error: Network error connecting to registry: Connection refused

# Invalid input
$ agentvault stake deposit -100
Error: Amount must be positive
```

## Security Best Practices

1. **Credential Storage**
   - Use `--keyring` for secure OS-level storage
   - Never use `--auth-key` in production
   - Rotate credentials regularly

2. **Bootstrap Tokens**
   - Treat as highly sensitive
   - Use immediately (5-minute expiry)
   - Never share in public channels

3. **Environment Variables**
   - Use `.env` files with restricted permissions
   - Don't commit credentials to version control
   - Consider using secret management tools

4. **Network Security**
   - Always use HTTPS in production
   - Verify registry certificates
   - Use VPN for sensitive operations

## Troubleshooting

### Common Issues

**"Cannot import agentvault library"**
```bash
# Ensure library is installed
pip install agentvault-library
# Or in development:
cd /path/to/monorepo && poetry install
```

**"No credentials found"**
```bash
# Check configuration
agentvault config get SERVICE_ID
# Set credentials
agentvault config set SERVICE_ID --keyring
```

**"Task timeout"**
```bash
# Increase timeout in environment
export AGENTVAULT_TASK_TIMEOUT=300
# Or use Ctrl+C to cancel gracefully
```

### Debug Mode

Enable verbose logging:
```bash
export AGENTVAULT_LOG_LEVEL=DEBUG
agentvault run -a agent -i "test"
```

## Integration with Development Tools

### VS Code Tasks

`.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Discover Agents",
      "type": "shell",
      "command": "agentvault discover ${input:searchTerm}",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "searchTerm",
      "type": "promptString",
      "description": "Search term for agents"
    }
  ]
}
```

### Git Aliases

`.gitconfig`:
```ini
[alias]
  agent-test = !agentvault run -a local-agent.json -i "Test message"
  agent-deploy = !agentvault agent onboard --agent-type "production"
```

---

The AgentVault CLI provides comprehensive access to the Sovereign Stack ecosystem, enabling developers and agents to interact seamlessly through a powerful command-line interface.
