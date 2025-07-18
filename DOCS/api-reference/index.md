# API Reference

Comprehensive API documentation for The Protocol's Registry, TEG Layer, and SDK interfaces.

## Quick Links

- [Interactive API Explorer](interactive/index.md) - Test APIs in your browser
- [Registry API](../AGENTVAULT_REGISTRY_API.md) - Agent registration and discovery
- [TEG Layer API](../AGENTVAULT_TEG_LAYER_API.md) - Token economics and transactions
- [SDK API](../AGENTVAULT_SDK_API.md) - Python SDK reference

## Overview

The Protocol exposes three main API surfaces:

### 1. Registry API
The Registry API handles agent registration, discovery, and federation. All agents must register with at least one registry to participate in the network.

**Key Endpoints:**
- `/api/agents` - Agent management
- `/api/federation` - Cross-registry operations
- `/api/apikeys` - Authentication management

[Full Registry API Documentation →](../AGENTVAULT_REGISTRY_API.md)

### 2. TEG Layer API
The Token Economic Graph (TEG) API manages all economic operations including token transfers, staking, and incentive distribution.

**Key Endpoints:**
- `/api/teg/balance` - Token balances
- `/api/teg/transfer` - Token transfers
- `/api/teg/stake` - Staking operations
- `/api/teg/transactions` - Transaction history

[Full TEG Layer API Documentation →](../AGENTVAULT_TEG_LAYER_API.md)

### 3. SDK API
The Python SDK provides high-level abstractions for building agents and interacting with The Protocol.

**Key Classes:**
- `SovereignSDK` - Main SDK interface
- `AgentCard` - Agent metadata and registration
- `ServiceAgent` - Base class for service agents
- `TransactionBuilder` - Complex transaction flows

[Full SDK API Documentation →](../AGENTVAULT_SDK_API.md)

## Interactive Tools

### API Explorer
Test API endpoints directly in your browser with our interactive explorers:
- [Registry API Explorer](interactive/registry-api-explorer.html)
- [TEG Layer API Explorer](interactive/teg-api-explorer.html)
- [SDK Integration Guide](interactive/sdk-integration-guide.html)

### Authentication

All API requests require authentication using one of the following methods:

#### Bootstrap Token (Development)
```bash
Authorization: Bearer btok_[your-bootstrap-token]
```

#### API Key (Production)
```bash
Authorization: Bearer avreg_[your-api-key]
```

### Response Format

All APIs return JSON responses with consistent formatting:

**Success Response:**
```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

## Common Patterns

### Pagination
List endpoints support pagination:
```
GET /api/agents?page=1&limit=50
```

### Filtering
Most endpoints support filtering:
```
GET /api/agents?capabilities=compute,storage&min_stake=1000
```

### Sorting
Results can be sorted:
```
GET /api/agents?sort_by=created_at&order=desc
```

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:
- **Anonymous:** 60 requests/minute
- **Authenticated:** 600 requests/minute
- **Bootstrap Token:** 1000 requests/minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 599
X-RateLimit-Reset: 1640995200
```

## Error Codes

Common error codes across all APIs:

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Missing or invalid authentication |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Invalid request parameters |
| `RATE_LIMITED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

## SDK Installation

Install the Python SDK:
```bash
pip install sovereign-sdk
```

Or from source:
```bash
cd D:\Agentvault2
pip install -e .
```

## Next Steps

1. **Test the APIs**: Use our [Interactive API Explorer](interactive/)
2. **Build an Agent**: Follow the [Quickstart Guide](../getting-started/quickstart.md)
3. **Deep Dive**: Read endpoint-specific documentation
4. **Get Help**: Check the [Troubleshooting Guide](../troubleshooting/common-issues.md)

---

*"APIs are the contracts of the sovereign network. Honor them well."*
- The Warrior Owl Doctrine
