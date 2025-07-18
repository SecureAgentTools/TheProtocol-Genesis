# Registry Architecture

## Overview

The AgentVault Registry serves as the central discovery hub and metadata catalog for the Sovereign Stack ecosystem. It provides a federated, decentralized network for agent registration, discovery, and authentication while maintaining sovereignty over local data.

## Core Architecture

### System Design

The Registry implements a multi-layered architecture optimized for scalability and federation:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REGISTRY ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       │
│  │   Public API    │       │  Developer UI   │       │  Admin Portal   │       │
│  │                 │       │                 │       │                 │       │
│  │ • Discovery     │       │ • Dashboard     │       │ • Peer Mgmt     │       │
│  │ • Agent Cards   │       │ • Agent Mgmt    │       │ • Monitoring    │       │
│  │ • Federation    │       │ • Token Gen     │       │ • Analytics     │       │
│  └────────┬────────┘       └────────┬────────┘       └────────┬────────┘       │
│           │                          │                          │                 │
│  ━━━━━━━━━┼━━━━━━━━━━━━━━━━━━━━━━━━┼━━━━━━━━━━━━━━━━━━━━━━━┼━━━━━━━━━━━━━   │
│           │                          │                          │                 │
│  ┌────────▼──────────────────────────▼──────────────────────────▼────────┐      │
│  │                         FASTAPI APPLICATION CORE                       │      │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │      │
│  │  │   Routers    │    │   Services   │    │   Schemas    │           │      │
│  │  │              │    │              │    │              │           │      │
│  │  │ • Auth       │    │ • Agent Mgr  │    │ • Pydantic   │           │      │
│  │  │ • Agents     │    │ • Federation │    │ • Validation │           │      │
│  │  │ • Onboard    │    │ • Auth/JWT   │    │ • OpenAPI    │           │      │
│  │  └──────────────┘    └──────────────┘    └──────────────┘           │      │
│  └─────────────────────────────────┬─────────────────────────────────────┘      │
│                                    │                                             │
│  ┌─────────────────────────────────▼─────────────────────────────────────┐      │
│  │                          DATA PERSISTENCE LAYER                        │      │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │      │
│  │  │ PostgreSQL  │    │   Redis     │    │  S3/Minio   │             │      │
│  │  │             │    │   Cache     │    │   Storage   │             │      │
│  │  │ • Agents    │    │ • Sessions  │    │ • Agent     │             │      │
│  │  │ • Users     │    │ • Fed Cache │    │   Cards     │             │      │
│  │  │ • Tokens    │    │ • Rate Limit│    │ • Artifacts │             │      │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │      │
│  └───────────────────────────────────────────────────────────────────────┘      │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.115.6 with Python 3.12
- **Database**: PostgreSQL 13+ with SQLAlchemy 2.0 ORM
- **Caching**: Redis for session management and federation cache
- **Authentication**: JWT tokens with automatic refresh
- **Frontend**: Vanilla JavaScript with Bootstrap 5
- **API Documentation**: Auto-generated OpenAPI/Swagger

### Component Structure

```
agentvault_registry/
├── src/agentvault_registry/
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection and session management
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── agent.py           # Agent entity model
│   │   ├── user.py            # User/Developer model
│   │   ├── bootstrap.py       # Bootstrap token model
│   │   └── federation.py      # Federation peer model
│   ├── routers/                # API endpoint definitions
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── agents.py          # Agent CRUD operations
│   │   ├── onboarding.py      # Bootstrap token flow
│   │   ├── discovery.py       # Enhanced discovery with federation
│   │   └── federation.py      # Federation management
│   ├── services/               # Business logic layer
│   │   ├── agent_service.py   # Agent management logic
│   │   ├── auth_service.py    # JWT and authentication
│   │   ├── federation_service.py # Federation protocol implementation
│   │   └── teg_bridge.py      # TEG OAuth integration
│   ├── schemas/                # Pydantic models for validation
│   │   ├── agent.py           # Agent request/response schemas
│   │   ├── auth.py            # Authentication schemas
│   │   └── federation.py      # Federation protocol schemas
│   ├── static/                 # Frontend assets
│   │   ├── js/                # JavaScript modules
│   │   ├── css/               # Stylesheets
│   │   └── img/               # Images and icons
│   └── templates/              # HTML templates
│       ├── index.html         # Main SPA template
│       └── components/        # Reusable UI components
```

## Data Models

### Core Entities

#### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    username: str = Column(String(100), unique=True, nullable=False)
    password_hash: str = Column(String(255), nullable=False)
    role: str = Column(String(50), default="developer")
    is_active: bool = Column(Boolean, default=True)
    is_verified: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, server_default=func.now())
    updated_at: datetime = Column(DateTime, onupdate=func.now())
    
    # Relationships
    agents = relationship("Agent", back_populates="developer")
    api_keys = relationship("APIKey", back_populates="user")
    bootstrap_tokens = relationship("BootstrapToken", back_populates="creator")
```

#### Agent Model
```python
class Agent(Base):
    __tablename__ = "agents"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    did: str = Column(String(255), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False, index=True)
    agent_type: str = Column(String(100), nullable=False)
    status: str = Column(String(50), default="active", index=True)
    description: str = Column(Text)
    developer_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # A2A Protocol Fields
    api_endpoints: List[str] = Column(ARRAY(String))
    capabilities: List[str] = Column(ARRAY(String))
    humanReadableId: str = Column(String(255), unique=True)
    
    # Economic Fields
    pricing: dict = Column(JSONB)
    teg_wallet_address: str = Column(String(255))
    
    # Metadata
    metadata: dict = Column(JSONB, default={})
    created_at: datetime = Column(DateTime, server_default=func.now())
    updated_at: datetime = Column(DateTime, onupdate=func.now())
    
    # Relationships
    developer = relationship("User", back_populates="agents")
```

#### Bootstrap Token Model
```python
class BootstrapToken(Base):
    __tablename__ = "bootstrap_tokens"
    
    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token: str = Column(String(255), unique=True, nullable=False, index=True)
    creator_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    consumed: bool = Column(Boolean, default=False)
    consumed_by_agent_id: UUID = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    expires_at: datetime = Column(DateTime, nullable=False)
    metadata: dict = Column(JSONB, default={})
    created_at: datetime = Column(DateTime, server_default=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="bootstrap_tokens")
    consumed_by_agent = relationship("Agent")
```

## API Design

### RESTful Endpoints

The Registry API follows RESTful principles with consistent patterns:

#### Authentication & Authorization
```http
POST   /api/v1/auth/register          # Create developer account
POST   /api/v1/auth/login             # Get JWT token
POST   /api/v1/auth/refresh           # Refresh JWT token
POST   /api/v1/auth/logout            # Invalidate token
GET    /api/v1/auth/me                # Get current user info
PUT    /api/v1/auth/password          # Change password
POST   /api/v1/auth/recover           # Request password reset
POST   /api/v1/auth/recover/confirm   # Confirm password reset
```

#### Agent Management
```http
GET    /api/v1/agents                 # List agents (paginated)
POST   /api/v1/agents                 # Create new agent
GET    /api/v1/agents/{agent_id}      # Get agent details
PUT    /api/v1/agents/{agent_id}      # Update agent
DELETE /api/v1/agents/{agent_id}      # Delete agent
POST   /api/v1/agents/{agent_id}/verify # Verify agent ownership
```

#### Discovery & Federation
```http
GET    /api/v1/discovery/agents       # Enhanced discovery with federation
GET    /api/v1/discovery/capabilities # List all known capabilities
GET    /api/v1/discovery/templates    # Get agent templates
POST   /api/v1/discovery/search       # Advanced search with filters
```

#### Onboarding Protocol
```http
POST   /api/v1/onboard/bootstrap/request-token  # Get bootstrap token
POST   /api/v1/onboard/register                # Register with token
GET    /api/v1/onboard/bootstrap/tokens        # List my tokens
DELETE /api/v1/onboard/bootstrap/tokens/{id}   # Revoke token
```

### Request/Response Schemas

#### Agent Registration Request
```json
{
  "name": "My AI Assistant",
  "agent_type": "assistant",
  "description": "A helpful AI assistant for various tasks",
  "api_endpoints": ["https://api.myagent.com/v1"],
  "capabilities": ["nlp", "code-generation", "data-analysis"],
  "humanReadableId": "my-ai-assistant",
  "pricing": {
    "model": "usage-based",
    "base_price": 0.01,
    "currency": "AVT"
  },
  "metadata": {
    "version": "1.0.0",
    "documentation": "https://docs.myagent.com"
  }
}
```

#### Discovery Response with Federation
```json
{
  "agents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "did": "did:agentvault:550e8400-e29b-41d4-a716-446655440000",
      "name": "Local Agent",
      "agent_type": "service",
      "description": "Agent from local registry",
      "developer_email": "dev@example.com",
      "is_federated": false,
      "registry_url": "https://registry.agentvault.com",
      "capabilities": ["nlp"],
      "created_at": "2025-06-17T10:00:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Federated Agent",
      "agent_type": "assistant",
      "description": "Agent from peer registry",
      "is_federated": true,
      "registry_url": "https://eu.registry.agentvault.com",
      "origin_registry_name": "EU-Registry",
      "capabilities": ["translation", "nlp"],
      "created_at": "2025-06-17T09:00:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 50,
    "pages": 3
  },
  "federation_status": {
    "peers_queried": 3,
    "peers_responded": 3,
    "query_time_ms": 250
  }
}
```

## Federation Architecture

### Federated Discovery Network

The Registry implements a peer-to-peer federation protocol that enables decentralized agent discovery:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Registry A    │────▶│   Registry B    │────▶│   Registry C    │
│ Agents: 1,500   │◀────│ Agents: 2,100   │◀────│ Agents: 800     │
│ Peers: B, C     │     │ Peers: A, C     │     │ Peers: A, B     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                         Federated Network
```

### Federation Protocol

#### Peer Registration
```python
POST /api/v1/admin/federation/peers
{
  "name": "European AgentVault Registry",
  "registry_url": "https://eu.agentvault.com",
  "admin_contact": "admin@eu.agentvault.com",
  "federation_access_token": "fed_token_secure_string"
}
```

#### Inter-Registry Query Protocol
```python
POST /api/v1/internal/federation/query
Authorization: Bearer {federation_access_token}

{
  "search": "language model",
  "tags": ["nlp", "transformer"],
  "limit": 100,
  "offset": 0,
  "active_only": true,
  "capabilities": ["text-generation"]
}
```

### Federation Implementation

#### Query Aggregation
```python
async def federated_discovery(query: DiscoveryQuery) -> FederatedResults:
    # Local results
    local_results = await search_local_agents(query)
    
    if not query.include_federated:
        return FederatedResults(agents=local_results, peers_queried=0)
    
    # Query all active peers in parallel
    peer_tasks = []
    for peer in await get_active_peers():
        task = query_peer_registry(peer, query)
        peer_tasks.append(task)
    
    # Gather results with timeout
    peer_results = await asyncio.gather(*peer_tasks, return_exceptions=True)
    
    # Combine and deduplicate
    all_agents = local_results + flatten(peer_results)
    unique_agents = deduplicate_by_did(all_agents)
    
    return FederatedResults(
        agents=unique_agents,
        peers_queried=len(peer_tasks),
        peers_responded=count_successful(peer_results)
    )
```

## Security Architecture

### Authentication & Authorization

#### JWT Token Flow
1. Developer authenticates with email/password
2. System generates JWT with claims:
   ```json
   {
     "sub": "user_uuid",
     "email": "dev@example.com",
     "role": "developer",
     "exp": 1719356400,
     "iat": 1719270000
   }
   ```
3. Token included in Authorization header
4. Automatic refresh before expiry

#### API Key Management
- Multiple keys per developer
- Scoped permissions
- Secure storage (hashed with bcrypt)
- Revocation without affecting other keys

### Rate Limiting

```python
RATE_LIMITS = {
    "auth.login": "5/minute",
    "auth.register": "3/hour", 
    "bootstrap.request": "5/minute",
    "agents.create": "10/minute",
    "discovery.search": "100/minute",
    "federation.query": "30/minute"
}
```

### Bootstrap Token Security

1. **Generation**: Cryptographically secure random tokens
2. **Format**: `BST_` prefix + 32 character random string
3. **Expiry**: 5 minutes default (configurable)
4. **Usage**: Single-use only
5. **Validation**: Check expiry, consumption status, creator

## User Interface Architecture

### Single Page Application Design

The Registry UI is a modern SPA built with vanilla JavaScript:

```javascript
// Router configuration
const routes = {
  '/': HomeView,
  '/ui/login': LoginView,
  '/ui/register': RegisterView,
  '/ui/dashboard': DashboardView,
  '/ui/developer': DeveloperPortalView,
  '/ui/discovery': DiscoveryView,
  '/ui/settings': SettingsView
};

// View lifecycle
class BaseView {
  async render() { /* Return HTML */ }
  async afterRender() { /* DOM manipulation */ }
  async destroy() { /* Cleanup */ }
}
```

### Key UI Components

#### Dashboard Views
1. **Classic Dashboard**: Traditional metrics and controls
2. **Mission Control**: Real-time monitoring interface

#### Developer Portal
- Agent management table with inline editing
- Bootstrap token generation interface
- API key management
- Usage analytics

#### Discovery Interface (Galactic Map)
- Visual agent browser with card layout
- Real-time federation toggle
- Advanced filtering sidebar
- Agent detail modal overlays

#### Settings Page
- Account management
- API key generation
- Bootstrap token history
- UI preferences (theme, layout)

## Integration Points

### TEG Layer OAuth Bridge

The Registry provides an OAuth 2.0 bridge for TEG integration:

```python
async def get_teg_token_for_agent(agent_did: str) -> str:
    """Exchange agent credentials for TEG OAuth token"""
    
    # Get agent's JWT-SVID from SPIRE
    jwt_svid = await acquire_jwt_svid(
        spiffe_id=f"spiffe://agentvault.com/agent/{agent_did}",
        audience="teg-oauth-bridge"
    )
    
    # Exchange for OAuth token
    response = await teg_client.post("/oauth/token", json={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_svid,
        "scope": "agent:economics agent:reputation"
    })
    
    return response.json()["access_token"]
```

### Identity Fabric Integration

SPIFFE/SPIRE integration for zero-trust security:

```python
# Service identity
SPIFFE_ID = "spiffe://agentvault.com/service/registry-backend"

# Workload API integration
async def verify_service_identity(request: Request):
    svid = await get_x509_svid()
    if not verify_peer_certificate(request.client_cert, svid.bundle):
        raise HTTPException(403, "Invalid service identity")
```

## Performance Optimization

### Caching Strategy

1. **Redis Cache Layers**:
   - Session cache (30 minute TTL)
   - Federation results (5 minute TTL)
   - Agent metadata (1 hour TTL)

2. **Database Optimization**:
   - Indexed columns: did, name, status, developer_id
   - Composite indexes for common queries
   - Read replicas for discovery endpoints

3. **API Response Optimization**:
   - Pagination with cursor-based navigation
   - Field selection for partial responses
   - ETag support for conditional requests

## Deployment Considerations

### Container Configuration

```yaml
services:
  registry:
    build: ./agentvault_registry
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - FEDERATION_ENABLED=true
    ports:
      - "8000:8000"
    volumes:
      - ./agentvault_registry:/app
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
```

### Production Checklist

1. **Security**:
   - [ ] SSL/TLS termination configured
   - [ ] Secrets management system integrated
   - [ ] Rate limiting enabled
   - [ ] CORS properly configured

2. **Monitoring**:
   - [ ] Health check endpoint active
   - [ ] Prometheus metrics exposed
   - [ ] Log aggregation configured
   - [ ] Error tracking enabled

3. **Scalability**:
   - [ ] Database connection pooling
   - [ ] Redis cluster mode
   - [ ] Load balancer configured
   - [ ] Auto-scaling policies set

## Future Enhancements

### Planned Features

1. **Enhanced Federation**:
   - Blockchain-based peer discovery
   - Gossip protocol for state synchronization
   - Byzantine fault tolerance

2. **Advanced Discovery**:
   - Semantic search capabilities
   - ML-based agent matching
   - Reputation-weighted results

3. **Developer Experience**:
   - GraphQL API option
   - WebSocket subscriptions
   - SDK code generation

---

The Registry serves as the cornerstone of the Sovereign Stack, enabling agents to find each other in a decentralized world while maintaining the security and sovereignty that defines our ecosystem.
