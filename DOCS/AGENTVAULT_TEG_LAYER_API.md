# AgentVault TEG Layer API Reference

## Overview

The TEG Layer API provides RESTful endpoints for token management, staking, reputation tracking, and governance operations. All endpoints are versioned under `/api/v1`.

## Authentication

Most endpoints require JWT bearer token authentication:
```
Authorization: Bearer <jwt_token>
```

Tokens are obtained from the Registry's authentication endpoints and contain the agent's DID.

## Base URL

```
Production: https://teg.agentvault.com/api/v1
Development: http://localhost:8002/api/v1
```

## Common Response Formats

### Success Response
```json
{
  "data": { ... },
  "status": "success"
}
```

### Error Response
```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "detail": "Technical details (debug mode only)",
  "validation_errors": [
    {
      "field": "field_name",
      "message": "Field-specific error",
      "value": "invalid_value"
    }
  ]
}
```

## Token Management Endpoints

### Get Token Balance
```http
GET /token/balance
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "agent_id": "did:agentvault:agent123",
  "balance": "1000.500000000000000000"
}
```

### Transfer Tokens
```http
POST /token/transfer
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "receiver_agent_id": "did:agentvault:agent456",
  "amount": "50.0",
  "message": "Payment for services"
}
```

**Headers:**
- `Idempotency-Key` (optional): Unique key to prevent duplicate transfers

**Response:**
```json
{
  "transaction_id": "tx_123456",
  "status": "completed",
  "sender_agent_id": "did:agentvault:agent123",
  "receiver_agent_id": "did:agentvault:agent456",
  "amount": "50.0",
  "fee_amount": "0.001",
  "new_sender_balance": "950.499",
  "timestamp": "2025-06-17T10:30:00Z",
  "attached_message": "Payment for services"
}
```

### Transfer to System Treasury
```http
POST /token/transfer/to-system
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "amount": "100.0",
  "system_account_type": "treasury",
  "purpose": "service_fee"
}
```

### Get Transaction History
```http
GET /token/transactions?limit=50&offset=0
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `limit` (int): Max results per page (default: 100, max: 1000)
- `offset` (int): Pagination offset (default: 0)
- `transaction_type` (string): Filter by type (transfer, issuance, burn)
- `start_date` (datetime): Filter by start date
- `end_date` (datetime): Filter by end date

**Response:**
```json
{
  "transactions": [
    {
      "transaction_id": "tx_123456",
      "sender_agent_id": "did:agentvault:agent123",
      "receiver_agent_id": "did:agentvault:agent456",
      "amount": "50.0",
      "fee_amount": "0.001",
      "status": "completed",
      "transaction_type": "transfer",
      "timestamp": "2025-06-17T10:30:00Z",
      "attached_message": "Payment for services"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Apply Reputation Signal
```http
POST /token/{transaction_id}/reputation-signal
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "signal_value": 1
}
```

**Rules:**
- Only sender can signal
- Signal value must be +1 or -1
- One signal per transaction
- Only for completed transfers

### Get Fee Configuration
```http
GET /token/fees/config
```

**Response:**
```json
{
  "fee_active": true,
  "fee_percentage": 0.0,
  "min_fee_amount": "0.001",
  "max_fee_amount": "0.001",
  "fee_recipient": "did:agentvault:treasury",
  "transfer_fee_amount": "0.001",
  "fee_collection_address": "did:agentvault:treasury"
}
```

## Staking Endpoints

### Stake Tokens
```http
POST /agent/stake
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "amount": "1000.0"
}
```

**Response:**
```json
{
  "stake_id": "stake_789",
  "agent_id": "did:agentvault:agent123",
  "amount": "1000.0",
  "staked_at": "2025-06-17T10:30:00Z",
  "status": "active"
}
```

### Unstake Tokens
```http
POST /agent/unstake
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "stake_id": "stake_789",
  "amount": "500.0"
}
```

### View Stakes
```http
GET /agent/stakes
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "stakes": [
    {
      "stake_id": "stake_789",
      "amount": "1000.0",
      "staked_at": "2025-06-17T10:30:00Z",
      "is_active": true,
      "rewards_earned": "50.0",
      "last_reward_claim": "2025-06-17T10:30:00Z"
    }
  ],
  "total_staked": "1000.0",
  "total_rewards": "50.0"
}
```

### Delegate Stake
```http
POST /agent/delegate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "validator_agent_id": "did:agentvault:validator1",
  "stake_id": "stake_789",
  "amount": "500.0",
  "reward_share_percentage": 10.0
}
```

## Reputation Endpoints

### Get Agent Reputation
```http
GET /reputation/{agent_id}
```

**Response:**
```json
{
  "agent_id": "did:agentvault:agent123",
  "reputation_score": 150,
  "reputation_tier": "trusted",
  "last_update": "2025-06-17T10:30:00Z",
  "total_transactions": 50,
  "positive_signals": 45,
  "negative_signals": 5
}
```

### Get Reputation History
```http
GET /reputation/history/{agent_id}?days=30
```

**Response:**
```json
{
  "agent_id": "did:agentvault:agent123",
  "history": [
    {
      "timestamp": "2025-06-17T10:30:00Z",
      "score_change": 1,
      "new_score": 151,
      "reason": "transaction_signal",
      "related_transaction_id": "tx_123"
    }
  ]
}
```

### Get Reputation Rankings
```http
GET /reputation/rankings?limit=100
```

**Response:**
```json
{
  "rankings": [
    {
      "rank": 1,
      "agent_id": "did:agentvault:topagent",
      "reputation_score": 950,
      "total_transactions": 1000
    }
  ],
  "total_agents": 5000
}
```

## Attestation Endpoints

### Submit Attestation
```http
POST /attestation/submit
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "attestation_type": "fairMarkupPolicy",
  "attestation_data": {
    "markup_percentage": 15,
    "service_category": "compute"
  },
  "storage_pointer": "ipfs://QmXxx...",
  "zkp_proof": {
    "circuit_id": "fairMarkupPolicy/v1.0.0",
    "public_inputs": {...},
    "proof": "0x..."
  }
}
```

**Response:**
```json
{
  "submission_id": "att_123",
  "status": "zkp_verified_true",
  "reward_amount": "10.0",
  "reward_transaction_id": "tx_reward_123"
}
```

### Get Attestation Submissions
```http
GET /attestation/submissions
Authorization: Bearer <jwt_token>
```

### Get Attestation Policies
```http
GET /attestation/policies
```

**Response:**
```json
{
  "policies": [
    {
      "policy_id": "pol_123",
      "policy_code": "FAIR_MARKUP_V1",
      "policy_name": "Fair Markup Policy",
      "reward_amount": "10.0",
      "circuit_identifier": "fairMarkupPolicy/v1.0.0",
      "is_active": true
    }
  ]
}
```

## Governance Endpoints

### List Governance Policies
```http
GET /governance/policies?policy_type=attestation
```

### Get Policy Details
```http
GET /governance/policies/{policy_id}
```

### Create Policy (Admin Only)
```http
POST /governance/policies
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "policy_code": "NEW_POLICY_V1",
  "policy_name": "New Governance Policy",
  "policy_type": "attestation",
  "description": "Policy description",
  "parameters": {...},
  "reward_amount": "5.0",
  "enforcement_level": "mandatory"
}
```

## Dispute Resolution Endpoints

### File Dispute
```http
POST /dispute/file
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "defendant_agent_id": "did:agentvault:agent456",
  "avtp_transaction_id": "avtp_123",
  "reason_code": "UNFAIR_FEE",
  "brief_description": "Charged excessive fees",
  "evidence_pointer": "ipfs://QmEvidence..."
}
```

### Get Dispute Status
```http
GET /dispute/{dispute_id}
Authorization: Bearer <jwt_token>
```

### Get My Disputes
```http
GET /dispute/my-disputes
Authorization: Bearer <jwt_token>
```

## Admin Endpoints

### Issue Tokens
```http
POST /admin/tokens/issue
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "recipient_agent_id": "did:agentvault:agent123",
  "amount": "10000.0",
  "reason": "Initial token grant"
}
```

### Suspend Agent Account
```http
POST /admin/accounts/suspend
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "agent_id": "did:agentvault:badagent",
  "reason": "Terms of service violation",
  "duration_days": 30
}
```

### Review Auditor Flags
```http
GET /admin/auditor/flags?status=NEW&severity=HIGH
Authorization: Bearer <admin_jwt_token>
```

### Resolve Dispute
```http
PUT /admin/disputes/{dispute_id}/resolve
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "resolution_status": "RESOLVED_FAVOR_CLAIMANT",
  "resolution_notes": "Evidence supports the claim",
  "penalties": {
    "reputation_adjustment": -50,
    "token_penalty": "100.0"
  }
}
```

## AVTP Integration Endpoints

### Report AVTP Transaction
```http
POST /avtp/report-transaction
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "avtp_transaction_id": "avtp_123",
  "initiating_agent_did": "did:agentvault:consumer",
  "responding_agent_did": "did:agentvault:provider",
  "service_identifier": "compute.gpu.inference",
  "price_avt": "50.0",
  "outcome_status": "SUCCESS",
  "sla_identifier_referenced": "sla_456"
}
```

## Auditor Endpoints

### Report Flag
```http
POST /auditor/flag
Authorization: Bearer <auditor_jwt_token>
Content-Type: application/json

{
  "flagged_agent_did": "did:agentvault:suspicious",
  "rule_violated_code": "HIGH_VELOCITY_TRANSFERS",
  "flag_reason": "100 transfers in 1 minute",
  "severity": "HIGH",
  "related_transaction_ids": ["tx_1", "tx_2"]
}
```

## Bootstrap Token Endpoints

### Generate Bootstrap Token (Admin)
```http
POST /admin/bootstrap-tokens/generate
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "agent_type_hint": "com.agentvault.compute.v1",
  "requested_by": "admin-user-123",
  "expires_in_hours": 72
}
```

**Response:**
```json
{
  "token": "bst_a1b2c3d4e5f67890_xxxxxxxxxxxx",
  "expires_at": "2025-06-20T10:30:00Z"
}
```

### Validate Bootstrap Token
```http
POST /onboarding/validate-token
Content-Type: application/json

{
  "bootstrap_token": "bst_a1b2c3d4e5f67890_xxxxxxxxxxxx"
}
```

## Health & Status Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "AgentVault TEG Core Service",
  "version": "2.0.0",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "configuration": {
      "status": "healthy",
      "debug_mode": false,
      "log_level": "INFO"
    }
  }
}
```

### Service Info
```http
GET /
```

## Rate Limiting

API rate limits (per agent):
- Standard endpoints: 1000 requests/hour
- Transfer endpoints: 100 requests/hour
- Admin endpoints: 500 requests/hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1623456789
```

## Webhooks

The TEG Layer can send webhooks for important events:

### Transaction Webhook
```json
{
  "event_type": "transaction.completed",
  "timestamp": "2025-06-17T10:30:00Z",
  "data": {
    "transaction_id": "tx_123",
    "sender_agent_id": "did:agentvault:sender",
    "receiver_agent_id": "did:agentvault:receiver",
    "amount": "100.0"
  }
}
```

### Reputation Change Webhook
```json
{
  "event_type": "reputation.changed",
  "timestamp": "2025-06-17T10:30:00Z",
  "data": {
    "agent_id": "did:agentvault:agent123",
    "old_score": 100,
    "new_score": 101,
    "change_reason": "transaction_signal"
  }
}
```

## Error Codes

Common error codes:

| Code | Description |
|------|-------------|
| `AUTH_INVALID_TOKEN` | Invalid or expired JWT token |
| `AUTH_AGENT_SUSPENDED` | Agent account is suspended |
| `BIZ_INSUFFICIENT_BALANCE` | Insufficient token balance |
| `BIZ_ENTITY_NOT_FOUND` | Resource not found |
| `BIZ_SELF_TRANSFER` | Cannot transfer to self |
| `VALIDATION_INVALID_INPUT` | Invalid input parameters |
| `SYS_INTERNAL_ERROR` | Internal server error |

## SDK Examples

### Python
```python
import requests

class TEGClient:
    def __init__(self, base_url, jwt_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
    
    def get_balance(self):
        resp = requests.get(f"{self.base_url}/token/balance", headers=self.headers)
        return resp.json()
    
    def transfer(self, receiver_id, amount, message=None):
        data = {
            "receiver_agent_id": receiver_id,
            "amount": str(amount),
            "message": message
        }
        resp = requests.post(f"{self.base_url}/token/transfer", 
                            json=data, headers=self.headers)
        return resp.json()
```

### JavaScript
```javascript
class TEGClient {
  constructor(baseUrl, jwtToken) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    };
  }

  async getBalance() {
    const resp = await fetch(`${this.baseUrl}/token/balance`, {
      headers: this.headers
    });
    return resp.json();
  }

  async transfer(receiverId, amount, message = null) {
    const resp = await fetch(`${this.baseUrl}/token/transfer`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        receiver_agent_id: receiverId,
        amount: amount.toString(),
        message
      })
    });
    return resp.json();
  }
}
```