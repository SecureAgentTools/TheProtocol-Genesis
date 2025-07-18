# AgentVault Registry - Comprehensive Documentation

**Component**: AgentVault Registry  
**Version**: 1.0.0  
**Status**: Fully Operational  
**Last Updated**: Tuesday, January 28, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Reference](#api-reference)
4. [Database Schema](#database-schema)
5. [Authentication & Security](#authentication--security)
6. [Federation System](#federation-system)
7. [User Interface](#user-interface)
8. [Agent Onboarding](#agent-onboarding)
9. [TEG Integration](#teg-integration)
10. [Deployment](#deployment)
11. [Configuration](#configuration)
12. [Testing](#testing)

---

## Overview

The AgentVault Registry is the central discovery hub for the AgentVault ecosystem. It serves as a metadata catalog for AI agents, providing registration, discovery, and federation capabilities.

### Key Responsibilities
- **Agent Registration**: Secure onboarding of new agents via bootstrap tokens
- **Discovery Service**: Public and federated agent discovery
- **Metadata Validation**: Ensures all agent cards conform to A2A schema
- **Developer Portal**: UI for agent management and monitoring
- **Federation Hub**: Enables registry-to-registry communication

### What It Does NOT Do
- Execute agents
- Handle agent-to-agent communication
- Manage user API keys (only developer registry keys)
- Proxy A2A protocols

---

## Architecture

### Component Structure
```
agentvault_registry/
├── src/agentvault_registry/
│   ├── main.py              # FastAPI application entry
│   ├── config.py             # Configuration management
│   ├── database.py           # Database connection
│   ├── models/               # SQLAlchemy models
│   ├── routers/              # API endpoints
│   ├── services/             # Business logic
│   ├── schemas/              # Pydantic schemas
│   ├── static/               # Frontend assets
│   └── templates/            # HTML templates
```

### Technology Stack
- **Backend**: FastAPI 0.115.6, Python 3.12
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens, API keys
- **Frontend**: Vanilla JavaScript, Bootstrap 5
- **Federation**: HTTP-based registry peering

---

## API Reference

### Authentication Endpoints

#### POST /api/v1/auth/register
Create a new developer account.

**Request Body**:
```json
{
  "email": "developer@example.com",
  "password": "SecurePassword123!",
  "username": "developer"
}
```

**Response**: 201 Created
```json
{
  "user_id": "uuid",
  "email": "developer@example.com",
  "username": "developer",
  "role": "developer"
}
```

#### POST /api/v1/auth/login
Authenticate and receive JWT token.

**Request Body**:
```json
{
  "email": "developer@example.com",
  "password": "SecurePassword123!"
}
```

**Response**: 200 OK
```json
{
  "access_token": "jwt.token.here",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "developer@example.com",
    "role": "developer"
  }
}
```

### Agent Management Endpoints

#### GET /api/v1/agents
List all agents with optional filtering.

**Query Parameters**:
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 50)
- `search`: Search term for name/description
- `agent_type`: Filter by agent type

**Response**: 200 OK
```json
{
  "agents": [
    {
      "id": "uuid",
      "did": "did:agentvault:agent123",
      "name": "Example Agent",
      "agent_type": "service",
      "status": "active",
      "description": "An example agent",
      "developer_email": "dev@example.com",
      "api_endpoints": ["https://agent.example.com/api"],
      "created_at": "2025-06-17T00:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

#### POST /api/v1/agents
Register a new agent (requires authentication).

**Request Body**:
```json
{
  "name": "My Agent",
  "agent_type": "service",
  "description": "Agent description",
  "api_endpoints": ["https://myagent.com/api"],
  "capabilities": ["nlp", "data-analysis"],
  "pricing": {
    "model": "usage-based",
    "base_price": 0.01
  }
}
```

#### GET /api/v1/agents/{agent_id}
Retrieve specific agent details.

#### PUT /api/v1/agents/{agent_id}
Update agent information (owner only).

#### DELETE /api/v1/agents/{agent_id}
Remove agent from registry (owner only).

### Onboarding Endpoints

#### POST /api/v1/onboard/bootstrap/request-token
Request a bootstrap token for agent creation (authenticated).

**Response**: 200 OK
```json
{
  "token": "BST_xxxxxxxxxxxx",
  "expires_at": "2025-06-17T00:05:00Z",
  "token_id": "uuid"
}
```

#### POST /api/v1/onboard/register
Register new agent using bootstrap token.

**Request Body**:
```json
{
  "bootstrap_token": "BST_xxxxxxxxxxxx",
  "agent_name": "New Agent",
  "agent_type": "assistant"
}
```

### Discovery Endpoints

#### GET /api/v1/discovery/agents
Enhanced discovery with federation support.

**Query Parameters**:
- `include_federated`: Include results from peer registries (default: false)
- `registry_url`: Filter by specific registry

### Federation Endpoints

#### GET /api/v1/federation/peers
List federated registry peers.

#### POST /api/v1/federation/peers
Add a new federation peer (admin only).

#### GET /api/v1/federation/health
Check federation status and peer connectivity.

---

## Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'developer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### agents
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    did VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    developer_id UUID REFERENCES users(id),
    api_endpoints TEXT[],
    capabilities TEXT[],
    pricing JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### bootstrap_tokens
```sql
CREATE TABLE bootstrap_tokens (
    id UUID PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    creator_id UUID REFERENCES users(id),
    consumed BOOLEAN DEFAULT false,
    consumed_by_agent_id UUID REFERENCES agents(id),
    expires_at TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### federation_peers
```sql
CREATE TABLE federation_peers (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    registry_url VARCHAR(500) UNIQUE NOT NULL,
    api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Authentication & Security

### Authentication Flow
1. **Developer Registration**: Email/password account creation
2. **Login**: Exchange credentials for JWT token
3. **Token Usage**: Include token in Authorization header
4. **Token Refresh**: Use refresh endpoint before expiry

### Security Features
- **Password Requirements**: Minimum 8 chars, complexity rules
- **Rate Limiting**: 
  - Login: 5 attempts per minute
  - Registration: 3 per hour per IP
  - Bootstrap tokens: 5 per minute per developer
- **Token Security**:
  - JWT tokens expire after 24 hours
  - Bootstrap tokens expire after 5 minutes
  - All tokens are single-use

### API Key Management
Developers can generate multiple API keys for programmatic access:
- Keys are hashed before storage
- Can be revoked individually
- Scoped to specific operations

---

## Federation System

### Overview
The federation system enables multiple AgentVault registries to share agent metadata, creating a decentralized discovery network.

### Federation Protocol
1. **Peer Registration**: Admin adds peer registry URL and API key
2. **Health Checks**: Periodic connectivity verification
3. **Agent Discovery**: Queries include federated results when requested
4. **Caching**: Federated results cached for 5 minutes

### Federation API
```python
# Request federated discovery
GET /api/v1/discovery/agents?include_federated=true

# Response includes source registry
{
  "agents": [
    {
      "id": "uuid",
      "name": "Federated Agent",
      "registry_url": "https://peer.registry.com",
      "is_federated": true,
      ...
    }
  ]
}
```

---

## User Interface

### Public Pages
- **Landing Page** (`/`): Introduction to AgentVault
- **Login** (`/ui/login`): Developer authentication
- **Registration** (`/ui/register`): New account creation
- **Password Recovery** (`/ui/recover`): Reset via email key

### Authenticated Pages

#### Classic Dashboard (`/ui`)
- Agent statistics overview
- Quick actions menu
- Recent activity feed
- Settings access

#### Mission Control (Alternative Dashboard)
- Enhanced visualization
- Real-time updates
- Advanced filtering
- Batch operations

#### Developer Portal (`/ui/developer`)
- Agent management table
- Bootstrap token generation
- API key management
- Federation controls (admin only)

#### Discovery/Galactic Map (`/ui/discovery`)
- Visual agent browser
- Federation toggle
- Advanced search filters
- Agent detail modals

#### Settings (`/ui/settings`)
Four comprehensive sections:
1. **Account**: Profile, password change
2. **API Keys**: Generate, view, revoke
3. **Bootstrap Tokens**: Create onboarding tokens
4. **Preferences**: UI customization, dark mode

### UI Architecture
- **Router**: Client-side routing (no page reloads)
- **Views**: Modular JavaScript view classes
- **API Client**: Centralized API communication
- **Auth Module**: Token management, auto-refresh
- **Components**: Reusable UI elements

---

## Agent Onboarding

### Two-Phase Protocol

#### Phase 1: Bootstrap Token Generation
1. Authenticated developer requests token
2. System generates unique `BST_` prefixed token
3. Token valid for 5 minutes (configurable)
4. Rate limited to prevent abuse

#### Phase 2: Agent Registration
1. Agent SDK uses bootstrap token
2. Registry validates token and creates agent
3. Generates unique DID and credentials
4. Token marked as consumed

### SDK Integration Example
```python
from agentvault_server_sdk import AgentVaultClient

# Initialize with bootstrap token
client = AgentVaultClient(
    bootstrap_token="BST_xxxxxxxxxxxx",
    agent_name="My Agent",
    agent_type="assistant"
)

# Register agent
agent_credentials = client.register()
print(f"Agent DID: {agent_credentials.did}")
```

---

## TEG Integration

### OAuth 2.0 Bridge
The registry includes a JWT-SVID to OAuth bridge for TEG (Token Economics Gateway) integration:

1. **SVID Acquisition**: Agent presents SPIFFE identity
2. **Token Exchange**: SVID exchanged for OAuth token
3. **TEG Access**: OAuth token used for economic operations
4. **Caching**: Tokens cached until expiry

### Configuration
```python
TEG_OAUTH_SETTINGS = {
    "token_endpoint": "https://teg.agentvault.io/oauth/token",
    "client_id": "agentvault-registry",
    "scope": "agent:economics agent:reputation",
    "cache_ttl": 3600
}
```

---

## Deployment

### Docker Deployment
```yaml
# docker-compose.yml
services:
  registry-a:
    build: ./agentvault_registry
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/registry
      - API_KEY_SECRET=your-secret-key
    volumes:
      - ./agentvault_registry:/app

  registry-b:
    build: ./agentvault_registry
    ports:
      - "8001:8000"
    # Same configuration as registry-a
```

### Production Considerations
1. **Load Balancing**: Use nginx/HAProxy for multiple instances
2. **SSL/TLS**: Terminate at load balancer
3. **Database**: Use managed PostgreSQL service
4. **Monitoring**: Health checks on `/health` endpoint
5. **Logging**: Aggregate logs with ELK/Loki
6. **Backups**: Automated database backups

---

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agentvault

# Security
API_KEY_SECRET=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret

# Federation
FEDERATION_ENABLED=true
FEDERATION_CACHE_TTL=300

# Bootstrap Tokens
BOOTSTRAP_TOKEN_LIFETIME=300
BOOTSTRAP_RATE_LIMIT=5

# UI
UI_BASE_URL=http://localhost:8000
ENABLE_DARK_MODE=true
```

### Rate Limiting Configuration
```python
# In config.py
RATE_LIMITS = {
    "login": "5/minute",
    "register": "3/hour",
    "bootstrap": "5/minute",
    "api_default": "100/minute"
}
```

---

## Testing

### Running Tests
```bash
# All registry tests
poetry run pytest tests/registry_api/ -v

# Specific test suites
poetry run pytest tests/registry_api/test_auth.py -v
poetry run pytest tests/registry_api/test_agents.py -v
poetry run pytest tests/registry_api/test_federation.py -v

# With coverage
poetry run pytest tests/registry_api/ --cov=src/agentvault_registry
```

### Test Categories
1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: Database interactions
3. **API Tests**: Endpoint functionality
4. **Federation Tests**: Peer communication
5. **UI Tests**: Frontend functionality

### Testing Best Practices
- Use pytest fixtures for database setup
- Mock external services (TEG, federation peers)
- Test error cases and edge conditions
- Verify rate limiting behavior
- Check authentication on protected endpoints

---

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Verify connection string
python -c "from agentvault_registry.database import engine; print(engine.url)"
```

#### Federation Sync Failures
```python
# Check peer health
GET /api/v1/federation/health

# Verify peer credentials
python scripts/test_federation_peer.py https://peer.registry.com
```

#### UI Not Loading
```bash
# Check static file serving
curl http://localhost:8000/static/js/app.js

# Verify template path
ls src/agentvault_registry/templates/
```

---

## References

### Internal Documentation
- [Federation Guide](./AGENTVAULT_REGISTRY_FEDERATION.md)
- [UI Architecture](./AGENTVAULT_REGISTRY_UI.md)
- [API Specification](./AGENTVAULT_REGISTRY_API.md)

### Related Components
- [TEG Layer Integration](./AGENTVAULT_TEG_LAYER.md)
- [Identity Fabric](./IDENTITY_FABRIC.md)
- [SDK](./AGENTVAULT_SDK.md)

---

**End of AgentVault Registry Documentation**
