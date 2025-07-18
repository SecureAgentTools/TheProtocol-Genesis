# Interactive API Documentation

Welcome to The Protocol's interactive API documentation. This section provides hands-on examples and live testing capabilities for all API endpoints.

## Overview

The Protocol exposes three main API surfaces:
- **Registry API**: Agent registration, discovery, and federation
- **TEG Layer API**: Token economics, staking, and financial operations  
- **SDK API**: High-level operations for agent development

## Interactive Features

### 1. Try It Now Examples
Each API endpoint includes "Try It Now" sections with:
- Pre-filled example requests
- Live response visualization
- Error handling demonstrations
- Authentication setup guides

### 2. API Explorer
Use our API Explorer to:
- Test endpoints with your own parameters
- View request/response headers
- Debug authentication issues
- Export requests as cURL commands

### 3. Code Generation
Generate client code in multiple languages:
- Python (using the SDK)
- JavaScript/TypeScript
- Go
- cURL commands

## Getting Started

### Prerequisites
1. A running Protocol stack (see [Running the Stack](../../getting-started/running-the-stack.md))
2. An API key (generate using `make generate-bootstrap-token`)
3. Basic understanding of REST APIs

### Authentication Setup

All API requests require authentication using either:

#### Option 1: Bootstrap Token (Development)
```bash
# Generate a bootstrap token
cd D:\Agentvault2
make generate-bootstrap-token

# Use in requests
Authorization: Bearer btok_[your-token-here]
```

#### Option 2: API Key (Production)
```bash
# Generate an API key via the Registry UI
# Or use the CLI:
python -m sovereign.main api-key create \
  --email your-email@example.com \
  --description "My API Key"

# Use in requests  
Authorization: Bearer avreg_[your-api-key]
```

## Quick Examples

### 1. Check Registry Health
```bash
curl -X GET http://localhost:8000/health
```

### 2. Register an Agent
```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer btok_[your-token]" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "version": "1.0.0",
    "capabilities": ["compute", "storage"]
  }'
```

### 3. Query TEG Balance
```bash
curl -X GET http://localhost:8000/api/teg/balance/{agent-id} \
  -H "Authorization: Bearer btok_[your-token]"
```

## Interactive Tools

### Registry API Explorer
[➡️ Explore Registry API](registry-api-explorer.html)
- Agent registration and management
- Federation endpoints
- API key management
- Health checks

### TEG Layer API Explorer  
[➡️ Explore TEG API](teg-api-explorer.html)
- Token operations
- Staking management
- Economic metrics
- Transaction history

### SDK Integration Guide
[➡️ SDK Interactive Guide](sdk-integration-guide.html)
- Step-by-step integration
- Code snippets
- Common patterns
- Error handling

## API Specifications

Full API specifications are embedded in the interactive explorers above. Use the Registry API Explorer and TEG Layer API Explorer for detailed endpoint documentation with live testing capabilities.

## Testing with the Beta API Keys

For beta testing, you can use these pre-configured API keys:

**Registry A (Port 8000)**
```bash
Authorization: Bearer avreg_eJx7JyZWspw29zO8A_EcsMDsA6_lrL7O6eFwzGaIG6I
```

**Registry B (Port 8001)**  
```bash
Authorization: Bearer avreg_d2yxb_VO1L9IieWEr4SF6oogMrOdNu2P7T3K5dKOcHk
```

## Common Use Cases

### 1. Agent Lifecycle
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Reg as Registry
    participant TEG as TEG Layer
    
    Dev->>Reg: Register Agent
    Reg-->>Dev: Agent ID
    Dev->>TEG: Stake Tokens
    TEG-->>Dev: Staking Receipt
    Dev->>Reg: Update Status (Active)
    Reg-->>Dev: Confirmation
```

### 2. Federation Flow
```mermaid
sequenceDiagram
    participant A as Registry A
    participant B as Registry B
    participant Agent as Agent
    
    Agent->>A: Register
    A-->>Agent: Local ID
    A->>B: Federate Agent
    B-->>A: Federation ID
    Agent->>B: Cross-Registry Call
    B-->>Agent: Success
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check your API key is valid
   - Ensure Authorization header format is correct
   - Verify the token hasn't expired

2. **404 Not Found**
   - Confirm the endpoint URL is correct
   - Check the agent/resource exists
   - Verify you're using the right port

3. **500 Internal Server Error**
   - Check the Protocol stack is running
   - Review logs: `docker logs agentvault-registry`
   - Ensure database is accessible

## Next Steps

1. **Explore the APIs**: Use our interactive explorers to test endpoints
2. **Build an Agent**: Follow the [Quickstart Guide](../../getting-started/quickstart.md)
3. **Deep Dive**: Read the full [API Reference](../index.md)
4. **Get Help**: Check the [Troubleshooting Guide](../../troubleshooting/common-issues.md)

---

*"APIs are the bridges between sovereign agents. Build them strong, document them well."*
- The Warrior Owl Doctrine
