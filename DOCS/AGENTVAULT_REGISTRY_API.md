# AgentVault Registry API Specification

**Version**: 1.0.0  
**Base URL**: `https://registry.agentvault.io/api/v1`  
**Last Updated**: Tuesday, June 17, 2025

---

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### Health Check

#### GET /health
Health status of the registry service.

**Response**: 200 OK
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-06-17T00:00:00Z",
  "database": "connected",
  "federation": "active"
}
```

---

### Authentication

#### POST /auth/register
Register a new developer account.

**Request Body**:
```json
{
  "email": "developer@example.com",
  "password": "SecurePass123!",
  "username": "developer",
  "full_name": "John Developer" // optional
}
```

**Response**: 201 Created
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "developer@example.com",
  "username": "developer",
  "role": "developer",
  "created_at": "2025-06-17T00:00:00Z"
}
```

**Error Responses**:
- 400 Bad Request: Invalid input data
- 409 Conflict: Email or username already exists

#### POST /auth/login
Authenticate user and receive access token.

**Request Body**:
```json
{
  "email": "developer@example.com",
  "password": "SecurePass123!"
}
```

**Response**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "developer@example.com",
    "username": "developer",
    "role": "developer"
  }
}
```

**Error Responses**:
- 401 Unauthorized: Invalid credentials
- 429 Too Many Requests: Rate limit exceeded

#### POST /auth/logout
Invalidate current access token.

**Headers**: Authorization required

**Response**: 200 OK
```json
{
  "message": "Successfully logged out"
}
```

#### POST /auth/refresh
Refresh access token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response**: 200 OK (same as login response)

#### POST /auth/change-password
Change user password.

**Headers**: Authorization required

**Request Body**:
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

**Response**: 200 OK
```json
{
  "message": "Password updated successfully"
}
```

---

### Agent Management

#### GET /agents
List agents with pagination and filtering.

**Query Parameters**:
- `skip` (integer): Offset for pagination (default: 0)
- `limit` (integer): Number of results (default: 50, max: 100)
- `search` (string): Search in name and description
- `agent_type` (string): Filter by type (service|assistant|tool|model)
- `status` (string): Filter by status (active|inactive|deprecated)
- `developer_id` (uuid): Filter by developer
- `sort_by` (string): Sort field (created_at|name|type)
- `sort_order` (string): asc|desc (default: desc)

**Response**: 200 OK
```json
{
  "agents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "did": "did:agentvault:550e8400-e29b-41d4-a716-446655440002",
      "name": "Data Analysis Agent",
      "agent_type": "service",
      "status": "active",
      "description": "Advanced data analysis and visualization",
      "developer_id": "550e8400-e29b-41d4-a716-446655440001",
      "developer_email": "developer@example.com",
      "api_endpoints": [
        "https://api.dataagent.com/v1/analyze"
      ],
      "capabilities": [
        "data-analysis",
        "visualization",
        "reporting"
      ],
      "pricing": {
        "model": "usage-based",
        "base_price": 0.01,
        "currency": "USD"
      },
      "metadata": {
        "version": "2.1.0",
        "last_updated": "2025-06-15T00:00:00Z"
      },
      "created_at": "2025-01-15T00:00:00Z",
      "updated_at": "2025-06-15T00:00:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50,
  "has_more": true
}
```

#### GET /agents/{agent_id}
Get detailed information about a specific agent.

**Path Parameters**:
- `agent_id` (uuid): Agent identifier

**Response**: 200 OK
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "did": "did:agentvault:550e8400-e29b-41d4-a716-446655440002",
  "name": "Data Analysis Agent",
  "agent_type": "service",
  "status": "active",
  "description": "Advanced data analysis and visualization service",
  "long_description": "Comprehensive data analysis agent capable of...",
  "developer_id": "550e8400-e29b-41d4-a716-446655440001",
  "developer_email": "developer@example.com",
  "api_endpoints": [
    {
      "url": "https://api.dataagent.com/v1/analyze",
      "method": "POST",
      "description": "Main analysis endpoint"
    }
  ],
  "capabilities": [
    "data-analysis",
    "visualization",
    "reporting",
    "ml-predictions"
  ],
  "pricing": {
    "model": "usage-based",
    "base_price": 0.01,
    "currency": "USD",
    "tiers": [
      {
        "requests": 1000,
        "price_per_request": 0.01
      },
      {
        "requests": 10000,
        "price_per_request": 0.008
      }
    ]
  },
  "requirements": {
    "min_api_version": "1.0",
    "dependencies": ["numpy", "pandas"],
    "compute": "GPU recommended"
  },
  "metadata": {
    "version": "2.1.0",
    "github": "https://github.com/example/data-agent",
    "documentation": "https://docs.dataagent.com"
  },
  "stats": {
    "total_requests": 150000,
    "average_response_time": 250,
    "uptime_percentage": 99.9
  },
  "created_at": "2025-01-15T00:00:00Z",
  "updated_at": "2025-06-15T00:00:00Z"
}
```

**Error Responses**:
- 404 Not Found: Agent does not exist

#### POST /agents
Create a new agent (requires authentication).

**Headers**: Authorization required

**Request Body**:
```json
{
  "name": "My New Agent",
  "agent_type": "assistant",
  "description": "Short description of the agent",
  "long_description": "Detailed description...", // optional
  "api_endpoints": [
    {
      "url": "https://api.myagent.com/v1/process",
      "method": "POST",
      "description": "Main processing endpoint"
    }
  ],
  "capabilities": [
    "text-generation",
    "summarization"
  ],
  "pricing": {
    "model": "flat-rate",
    "base_price": 0.05,
    "currency": "USD"
  },
  "requirements": {
    "min_api_version": "1.0"
  },
  "metadata": {
    "version": "1.0.0",
    "github": "https://github.com/myorg/myagent"
  }
}
```

**Response**: 201 Created
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "did": "did:agentvault:550e8400-e29b-41d4-a716-446655440003",
  "name": "My New Agent",
  // ... full agent object
}
```

**Error Responses**:
- 400 Bad Request: Invalid agent data
- 401 Unauthorized: Not authenticated
- 409 Conflict: Agent name already exists

#### PUT /agents/{agent_id}
Update agent information (owner only).

**Headers**: Authorization required

**Path Parameters**:
- `agent_id` (uuid): Agent identifier

**Request Body**: Same as POST /agents (all fields optional)

**Response**: 200 OK (updated agent object)

**Error Responses**:
- 401 Unauthorized: Not authenticated
- 403 Forbidden: Not the agent owner
- 404 Not Found: Agent does not exist

#### DELETE /agents/{agent_id}
Delete an agent (owner only).

**Headers**: Authorization required

**Path Parameters**:
- `agent_id` (uuid): Agent identifier

**Response**: 204 No Content

**Error Responses**:
- 401 Unauthorized: Not authenticated
- 403 Forbidden: Not the agent owner
- 404 Not Found: Agent does not exist

---

### Agent Onboarding

#### POST /onboard/bootstrap/request-token
Request a bootstrap token for agent creation.

**Headers**: Authorization required

**Request Body**:
```json
{
  "agent_type_hint": "assistant", // optional
  "metadata": {                   // optional
    "purpose": "Development testing",
    "environment": "staging"
  }
}
```

**Response**: 200 OK
```json
{
  "token": "BST_1234567890abcdef1234567890abcdef",
  "token_id": "550e8400-e29b-41d4-a716-446655440004",
  "expires_at": "2025-06-17T00:05:00Z",
  "created_at": "2025-06-17T00:00:00Z"
}
```

**Error Responses**:
- 401 Unauthorized: Not authenticated
- 429 Too Many Requests: Rate limit exceeded (5/minute)

#### POST /onboard/register
Register a new agent using bootstrap token.

**Request Body**:
```json
{
  "bootstrap_token": "BST_1234567890abcdef1234567890abcdef",
  "agent_name": "My Agent",
  "agent_type": "service",
  "initial_endpoints": [          // optional
    "https://myagent.com/api/v1"
  ]
}
```

**Response**: 201 Created
```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440005",
  "agent_did": "did:agentvault:550e8400-e29b-41d4-a716-446655440005",
  "api_key": "ak_1234567890abcdef1234567890abcdef",
  "created_at": "2025-06-17T00:00:00Z"
}
```

**Error Responses**:
- 400 Bad Request: Invalid token or data
- 401 Unauthorized: Token expired or already used
- 429 Too Many Requests: Global rate limit (60/minute)

---

### Discovery

#### GET /discovery/agents
Enhanced agent discovery with federation support.

**Query Parameters**:
- All parameters from GET /agents
- `include_federated` (boolean): Include federated results (default: false)
- `registry_url` (string): Filter by specific registry
- `max_federated_latency` (integer): Max wait time for federated results in ms (default: 5000)

**Response**: 200 OK
```json
{
  "agents": [
    {
      // Local agent (same as GET /agents response)
      "is_federated": false,
      "registry_url": "https://registry.agentvault.io"
    },
    {
      // Federated agent
      "id": "remote-550e8400-e29b-41d4-a716-446655440006",
      "name": "Remote Agent",
      "is_federated": true,
      "registry_url": "https://peer.registry.com",
      "registry_name": "Peer Registry",
      // ... other agent fields
    }
  ],
  "total": 200,
  "local_count": 150,
  "federated_count": 50,
  "federated_registries": [
    {
      "url": "https://peer.registry.com",
      "name": "Peer Registry",
      "agent_count": 50,
      "response_time": 150
    }
  ]
}
```

---

### Developer Tools

#### GET /developer/api-keys
List developer's API keys.

**Headers**: Authorization required

**Response**: 200 OK
```json
{
  "api_keys": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "name": "Production Key",
      "key_prefix": "ak_1234****",
      "scopes": ["read", "write"],
      "last_used": "2025-06-16T00:00:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /developer/api-keys
Generate a new API key.

**Headers**: Authorization required

**Request Body**:
```json
{
  "name": "Development Key",
  "scopes": ["read", "write"],
  "expires_in_days": 365  // optional
}
```

**Response**: 201 Created
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440008",
  "name": "Development Key",
  "api_key": "ak_full_key_shown_only_once",
  "scopes": ["read", "write"],
  "expires_at": "2026-06-17T00:00:00Z",
  "created_at": "2025-06-17T00:00:00Z"
}
```

#### DELETE /developer/api-keys/{key_id}
Revoke an API key.

**Headers**: Authorization required

**Response**: 204 No Content

---

### Federation (Admin Only)

#### GET /federation/peers
List federation peers.

**Headers**: Authorization required (admin role)

**Response**: 200 OK
```json
{
  "peers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440009",
      "name": "Partner Registry",
      "registry_url": "https://partner.registry.com",
      "is_active": true,
      "last_sync": "2025-06-17T00:00:00Z",
      "agent_count": 75,
      "status": "healthy",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /federation/peers
Add a new federation peer.

**Headers**: Authorization required (admin role)

**Request Body**:
```json
{
  "name": "New Partner",
  "registry_url": "https://newpartner.registry.com",
  "api_key": "their_api_key"  // optional
}
```

**Response**: 201 Created

#### GET /federation/health
Check federation system health.

**Headers**: Authorization required (admin role)

**Response**: 200 OK
```json
{
  "status": "healthy",
  "active_peers": 3,
  "total_peers": 4,
  "peer_health": [
    {
      "peer_id": "550e8400-e29b-41d4-a716-446655440009",
      "name": "Partner Registry",
      "status": "healthy",
      "response_time": 120,
      "last_check": "2025-06-17T00:00:00Z"
    }
  ],
  "last_full_sync": "2025-06-17T00:00:00Z"
}
```

---

### Admin Operations

#### GET /admin/stats
System statistics (admin only).

**Headers**: Authorization required (admin role)

**Response**: 200 OK
```json
{
  "users": {
    "total": 500,
    "active_30d": 350,
    "new_7d": 25
  },
  "agents": {
    "total": 1500,
    "active": 1400,
    "by_type": {
      "service": 600,
      "assistant": 500,
      "tool": 300,
      "model": 100
    }
  },
  "usage": {
    "api_calls_24h": 150000,
    "bootstrap_tokens_24h": 50,
    "federation_queries_24h": 5000
  },
  "system": {
    "version": "1.0.0",
    "uptime_hours": 720,
    "database_size_mb": 512
  }
}
```

#### POST /admin/users/{user_id}/role
Update user role (admin only).

**Headers**: Authorization required (admin role)

**Request Body**:
```json
{
  "role": "admin"  // developer|admin
}
```

**Response**: 200 OK

---

## Error Responses

All endpoints may return these standard error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Validation failed",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions for this operation"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/login | 5 | 1 minute |
| POST /auth/register | 3 | 1 hour |
| POST /onboard/bootstrap/request-token | 5 | 1 minute |
| POST /onboard/register | 60 | 1 minute |
| GET /agents | 100 | 1 minute |
| POST /agents | 10 | 1 minute |
| All other authenticated | 100 | 1 minute |
| All unauthenticated | 30 | 1 minute |

---

## Webhooks (Coming Soon)

The registry will support webhooks for:
- Agent status changes
- New agent registrations
- Federation sync events

---

**End of API Specification**
