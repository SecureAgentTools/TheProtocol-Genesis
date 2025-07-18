# Agent Card Schema Reference

## Overview

The Agent Card is a JSON document that serves as the passport for autonomous agents in the AgentVault ecosystem. It provides essential metadata about an agent, including its capabilities, authentication requirements, available skills, and endpoint information. Think of it as a machine-readable business card that enables automatic discovery, authentication, and interaction between agents.

The Agent Card follows the A2A (Agent-to-Agent) protocol specifications and enables:
- **Automatic Discovery**: Agents can be discovered and understood by other agents
- **Authentication Negotiation**: Clients can determine which authentication scheme to use
- **Capability Verification**: Clients can understand what an agent can do before connecting
- **Protocol Compatibility**: Ensures agents can communicate using compatible protocols

## Complete Example

Below is a comprehensive example showing all possible fields in an Agent Card:

```json
{
  // REQUIRED FIELDS
  "schemaVersion": "1.0",                           // Version of the Agent Card schema
  "humanReadableId": "myorg/weather-reporter",      // Unique, user-friendly identifier
  "agentVersion": "2.1.0",                          // Version of the agent software
  "name": "Advanced Weather Reporter",              // Human-readable display name
  "description": "An agent that provides detailed weather analysis and forecasts using multiple data sources",
  "url": "https://api.weather-agent.example.com/a2a", // Primary A2A endpoint URL
  
  "provider": {                                     // Information about the provider
    "name": "Weather Corp International",           // REQUIRED: Provider name
    "url": "https://weathercorp.example.com",      // OPTIONAL: Provider homepage
    "support_contact": "support@weathercorp.com"    // OPTIONAL: Support contact
  },
  
  "capabilities": {                                 // Protocol capabilities
    "a2aVersion": "1.0",                           // REQUIRED: A2A protocol version
    "mcpVersion": "0.6",                           // OPTIONAL: MCP protocol version
    "supportedMessageParts": ["text", "file", "data"], // OPTIONAL: Message part types
    "supportsPushNotifications": true,              // OPTIONAL: Push notification support
    "teeDetails": {                                // OPTIONAL: TEE information
      "type": "Intel SGX",                         // REQUIRED if teeDetails present
      "attestationEndpoint": "https://api.weather-agent.example.com/attestation",
      "publicKey": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqh...",
      "description": "Runs in Intel SGX enclave for secure data processing"
    }
  },
  
  "authSchemes": [                                 // REQUIRED: At least one auth scheme
    {
      "scheme": "apiKey",                          // For API key authentication
      "description": "Use your Weather Corp API key",
      "service_identifier": "weather-corp"         // Key identifier for key managers
    },
    {
      "scheme": "oauth2",                          // For OAuth2 authentication
      "description": "OAuth2 Client Credentials Grant",
      "tokenUrl": "https://auth.weathercorp.com/oauth/token", // REQUIRED for oauth2
      "scopes": ["weather:read", "forecast:read"], // OPTIONAL: Required scopes
      "service_identifier": "weather-corp-oauth"
    },
    {
      "scheme": "bearer",                          // For bearer token authentication
      "description": "Use a pre-shared bearer token"
    },
    {
      "scheme": "none",                            // No authentication required
      "description": "Public endpoints require no authentication"
    }
  ],
  
  // OPTIONAL FIELDS
  "skills": [                                      // List of agent skills
    {
      "id": "current_weather",                     // Unique skill identifier
      "name": "Current Weather",                   // Human-readable skill name
      "description": "Get current weather conditions for any location",
      "input_schema": {                            // JSON Schema for input
        "type": "object",
        "properties": {
          "location": { "type": "string" },
          "units": { "type": "string", "enum": ["metric", "imperial"] }
        },
        "required": ["location"]
      },
      "output_schema": {                           // JSON Schema for output
        "type": "object",
        "properties": {
          "temperature": { "type": "number" },
          "conditions": { "type": "string" },
          "humidity": { "type": "number" }
        }
      }
    },
    {
      "id": "forecast",
      "name": "Weather Forecast",
      "description": "Get weather forecast for up to 7 days",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": { "type": "string" },
          "days": { "type": "integer", "minimum": 1, "maximum": 7 }
        },
        "required": ["location"]
      }
    }
  ],
  
  "tags": ["weather", "forecast", "climate", "api"], // Keywords for discovery
  "privacyPolicyUrl": "https://weathercorp.example.com/privacy",
  "termsOfServiceUrl": "https://weathercorp.example.com/terms",
  "iconUrl": "https://weathercorp.example.com/assets/agent-icon.png",
  "lastUpdated": "2025-01-15T10:30:00Z"           // ISO 8601 timestamp
}
```

## Field-by-Field Reference

### Core Fields

| Field Name | Type | Required? | Description |
|------------|------|-----------|-------------|
| `schemaVersion` | string | **Yes** | Version of the Agent Card schema itself (e.g., "1.0") |
| `humanReadableId` | string | **Yes** | User-friendly, unique identifier (e.g., "myorg/agent-name"). Used for discovery and key management |
| `agentVersion` | string | **Yes** | Version string of the agent software (e.g., "2.1.0") |
| `name` | string | **Yes** | Human-readable display name of the agent |
| `description` | string | **Yes** | Detailed description of the agent's purpose and functionality |
| `url` | string (URL) | **Yes** | Primary A2A endpoint URL for interacting with the agent. Must use HTTPS unless localhost |
| `provider` | object | **Yes** | Information about the agent's provider (see Provider Object) |
| `capabilities` | object | **Yes** | Protocol capabilities and features (see Capabilities Object) |
| `authSchemes` | array | **Yes** | List of supported authentication schemes. Must contain at least one item |
| `skills` | array | No | List of specific skills/capabilities the agent possesses |
| `tags` | array | No | Keywords for categorization and discovery |
| `privacyPolicyUrl` | string (URL) | No | URL to the agent's privacy policy |
| `termsOfServiceUrl` | string (URL) | No | URL to the agent's terms of service |
| `iconUrl` | string (URL) | No | URL to an icon representing the agent |
| `lastUpdated` | string | No | ISO 8601 timestamp of last card update |

### Provider Object

| Field Name | Type | Required? | Description |
|------------|------|-----------|-------------|
| `name` | string | **Yes** | Name of the agent provider or developer |
| `url` | string (URL) | No | Homepage URL of the provider |
| `support_contact` | string | No | Contact information for support (email or URL) |

### Capabilities Object

| Field Name | Type | Required? | Description |
|------------|------|-----------|-------------|
| `a2aVersion` | string | **Yes** | Version of the A2A protocol supported (e.g., "1.0") |
| `mcpVersion` | string | No | Version of Model Context Protocol supported if any |
| `supportedMessageParts` | array | No | List of message part types (e.g., ["text", "file", "data"]) |
| `supportsPushNotifications` | boolean | No | Whether agent supports push notifications to webhooks |
| `teeDetails` | object | No | Trusted Execution Environment details (see TEE Details) |

### TEE Details Object

| Field Name | Type | Required? | Description |
|------------|------|-----------|-------------|
| `type` | string | **Yes** | TEE technology identifier (e.g., "Intel SGX", "AWS Nitro Enclaves") |
| `attestationEndpoint` | string (URL) | No | URL for attestation document verification |
| `publicKey` | string | No | Public key for secure communication/attestation |
| `description` | string | No | Human-readable description of TEE setup |

### Authentication Scheme Object

| Field Name | Type | Required? | Description |
|------------|------|-----------|-------------|
| `scheme` | string | **Yes** | One of: "apiKey", "oauth2", "bearer", "none" |
| `description` | string | No | Human-readable description of authentication requirements |
| `tokenUrl` | string (URL) | **Yes** (oauth2 only) | OAuth2 token endpoint URL |
| `scopes` | array | No | OAuth2 scopes required (oauth2 only) |
| `service_identifier` | string | No | Identifier for key managers to retrieve credentials |

### Skill Object

| Field Name | Type | Required? | Description |
|------------|------|-----------|-------------|
| `id` | string | **Yes** | Unique identifier for the skill |
| `name` | string | **Yes** | Human-readable skill name |
| `description` | string | **Yes** | Detailed description of the skill |
| `input_schema` | object | No | JSON Schema for expected input format |
| `output_schema` | object | No | JSON Schema for output format |

## Authentication Schemes

### API Key Authentication

```json
{
  "scheme": "apiKey",
  "description": "Requires an API key in the Authorization header",
  "service_identifier": "myservice"
}
```

The client should send: `Authorization: ApiKey <key-value>`

### OAuth2 Client Credentials

```json
{
  "scheme": "oauth2",
  "description": "OAuth2 Client Credentials Grant flow",
  "tokenUrl": "https://auth.example.com/oauth/token",
  "scopes": ["read", "write"],
  "service_identifier": "myservice-oauth"
}
```

The client must:
1. POST to `tokenUrl` with client credentials
2. Receive an access token
3. Send: `Authorization: Bearer <access-token>`

### Bearer Token

```json
{
  "scheme": "bearer",
  "description": "Use a pre-shared bearer token"
}
```

The client should send: `Authorization: Bearer <token-value>`

### No Authentication

```json
{
  "scheme": "none",
  "description": "This endpoint requires no authentication"
}
```

No authentication headers required.

## Validation Rules

1. **URL Validation**: The `url` field must use HTTPS unless it's a localhost URL
2. **Schema Version**: Must be a valid schema version (currently "1.0")
3. **Auth Schemes**: The `authSchemes` array must contain at least one authentication method
4. **OAuth2 Requirements**: When `scheme` is "oauth2", the `tokenUrl` field is required
5. **Required Fields**: All fields marked as required in the tables above must be present
6. **ISO 8601 Dates**: The `lastUpdated` field must be in ISO 8601 format

## Best Practices

1. **Human Readable ID**: Use a namespace format like "organization/agent-name" for easy identification
2. **Versioning**: Follow semantic versioning for `agentVersion` (MAJOR.MINOR.PATCH)
3. **Descriptions**: Write clear, comprehensive descriptions that help users understand the agent's purpose
4. **Skills Documentation**: Include detailed `input_schema` and `output_schema` for each skill
5. **Authentication**: Provide clear descriptions for each auth scheme explaining how to obtain credentials
6. **Tags**: Use relevant, searchable tags to improve discoverability
7. **Updates**: Keep the `lastUpdated` field current when making changes to the agent

## Common Patterns

### Public Agent (No Auth)
```json
{
  "authSchemes": [
    {
      "scheme": "none",
      "description": "This is a public agent - no authentication required"
    }
  ]
}
```

### Enterprise Agent (Multiple Auth Options)
```json
{
  "authSchemes": [
    {
      "scheme": "oauth2",
      "description": "Preferred: OAuth2 for enterprise SSO",
      "tokenUrl": "https://auth.corp.com/oauth/token",
      "scopes": ["agent:access"]
    },
    {
      "scheme": "apiKey",
      "description": "Alternative: API key for service accounts",
      "service_identifier": "corp-agent"
    }
  ]
}
```

### Secure Agent (TEE-enabled)
```json
{
  "capabilities": {
    "a2aVersion": "1.0",
    "teeDetails": {
      "type": "Intel SGX",
      "attestationEndpoint": "https://agent.example.com/attestation",
      "publicKey": "-----BEGIN PUBLIC KEY-----...",
      "description": "Processes sensitive data in secure enclave"
    }
  }
}
```

This reference provides everything needed to create valid Agent Cards for any scenario. For implementation details and validators, refer to the [Building an Agent guide](../developer-guides/building-an-agent.md).
