# AgentVault TEG Layer - Token Economic Governance

## Overview

The TEG (Token Economic Governance) Layer is the economic engine of the AgentVault ecosystem. It manages the AVT (AgentVault Token) economy, implements staking mechanisms, tracks reputation scores, and provides governance frameworks for agent interactions.

## Architecture

The TEG Layer is built as a production-grade FastAPI application with the following components:

### Core Components

1. **Token Management System**
   - AVT token transfers between agents
   - Fee collection and treasury management
   - Transaction history and auditing
   - Idempotency support for reliable transfers

2. **Staking & Delegation System**
   - Agents can stake AVT tokens for rewards
   - Delegation mechanism for validators
   - Reward distribution cycles
   - Flexible unstaking with tracking

3. **Reputation System**
   - Reputation scoring from -1000 to +1000
   - Transaction-based reputation signals
   - AVTP transaction outcome tracking
   - Automated reputation adjustments

4. **Attestation & Rewards**
   - Agents submit attestations for rewards
   - Zero-knowledge proof verification
   - Policy-based reward distribution
   - IPFS integration for attestation storage

5. **Dispute Resolution**
   - Decentralized Dispute Resolution (DDR) interface
   - Evidence submission via IPFS
   - Multi-stage resolution process
   - Administrative review capabilities

6. **Auditor System**
   - Automated rule-based flagging
   - Severity levels (LOW, MEDIUM, HIGH, CRITICAL)
   - Manual review workflow
   - Integration with transaction monitoring

## Database Schema

The TEG Layer uses PostgreSQL (production) or SQLite (development) with the following key tables:

- `agent_teg_profiles` - Agent token balances and reputation
- `teg_transactions` - All token transfers and system transactions
- `stakes` - Active and historical stake records
- `delegations` - Stake delegation relationships
- `teg_attestation_logs` - Attestation submissions and rewards
- `auditor_flag_logs` - Automated auditor flags
- `teg_dispute_logs` - Dispute records and resolutions
- `avtp_transaction_summary_logs` - External transaction outcomes
- `teg_policies` - Governance policies and rules
- `bootstrap_tokens` - Onboarding tokens for new agents

## API Structure

The TEG Layer exposes a RESTful API at `/api/v1` with the following endpoint groups:

### Token Endpoints (`/api/v1/token`)
- `GET /balance` - Get agent's token balance
- `POST /transfer` - Transfer tokens between agents
- `POST /transfer/to-system` - Transfer to system treasury
- `GET /transactions` - Transaction history with pagination
- `POST /{transaction_id}/reputation-signal` - Apply reputation signal
- `GET /fees/config` - Get current fee configuration
- `GET /fees/calculate` - Calculate transfer fees

### Staking Endpoints (`/api/v1/agent`)
- `POST /stake` - Stake AVT tokens
- `POST /unstake` - Unstake tokens
- `GET /stakes` - View stake positions
- `POST /delegate` - Delegate stake to validator
- `GET /delegations` - View delegations

### Reputation Endpoints (`/api/v1/reputation`)
- `GET /{agent_id}` - Get agent reputation score
- `GET /history/{agent_id}` - Reputation change history
- `GET /rankings` - Global reputation rankings

### Attestation Endpoints (`/api/v1/attestation`)
- `POST /submit` - Submit attestation with optional ZKP
- `GET /submissions` - View own attestations
- `GET /policies` - Get active attestation policies

### Governance Endpoints (`/api/v1/governance`)
- `GET /policies` - List all governance policies
- `GET /policies/{policy_id}` - Get policy details
- `POST /policies` - Create new policy (admin only)

### Admin Endpoints (`/api/v1/admin`)
- `POST /tokens/issue` - Issue new tokens
- `POST /accounts/suspend` - Suspend agent account
- `GET /auditor/flags` - Review auditor flags
- `PUT /disputes/{id}/resolve` - Resolve disputes

## Security Features

1. **Authentication & Authorization**
   - JWT bearer token authentication
   - Agent DID-based identity
   - Role-based access control (agents, auditors, admins)
   - Token refresh mechanism

2. **Security Middleware**
   - CORS configuration
   - Security headers (CSP, HSTS, etc.)
   - Request ID tracking
   - Rate limiting capabilities

3. **Data Protection**
   - SQL injection prevention via SQLAlchemy ORM
   - Input validation with Pydantic
   - Secure configuration management
   - Audit logging for sensitive operations

## Economic Mechanisms

### Token Economics
- **Total Supply**: Managed by system treasury
- **Transfer Fees**: Configurable, collected by treasury
- **Minimum Transfer**: 0.01 AVT
- **Maximum Transfer**: Configurable (optional)

### Staking Rewards
- **Base Reward Rate**: Configurable per cycle
- **Delegation Rewards**: Validators earn percentage of delegator rewards
- **Reward Distribution**: Automated cycles with claim tracking

### Reputation Scoring
- **Range**: -1000 to +1000
- **Initial Score**: 0
- **Transaction Signals**: +1 or -1 per transaction
- **AVTP Outcomes**: Automatic adjustments based on service outcomes

## Integration Points

1. **Registry Integration**
   - Agent authentication validation
   - Agent metadata lookups
   - Federation support

2. **AVTP Integration**
   - Transaction outcome reporting
   - Service performance tracking
   - Reputation impact calculation

3. **Identity Fabric Integration**
   - SPIFFE/SPIRE for mTLS (optional)
   - OPA for policy enforcement
   - X.509 SVID support

## Configuration

Key environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/tegdb

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Economic Parameters
MIN_TRANSFER_AMOUNT=0.01
TRANSFER_FEE=0.001
TEG_SYSTEM_TREASURY_DID=did:agentvault:treasury

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ALLOWED_ORIGINS=["http://localhost:3000"]

# Staking
STAKING_REWARD_RATE=0.05
DELEGATION_VALIDATOR_SHARE=0.10
```

## Deployment

### Docker Deployment
```bash
# Build the container
docker build -t agentvault-teg-layer .

# Run with environment variables
docker run -p 8002:8000 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET_KEY=... \
  agentvault-teg-layer
```

### Local Development
```bash
# Install dependencies
cd agentvault_teg_layer_mvp
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.teg_core_service.main:app --reload --port 8002
```

## Health Monitoring

The TEG Layer provides comprehensive health checks:

- `/health` - Overall service health with subsystem checks
- Database connectivity monitoring
- Configuration validation
- Resource availability tracking

## Error Handling

Unified error response format:
```json
{
  "error_code": "VALIDATION_INVALID_INPUT",
  "message": "User-friendly error message",
  "detail": "Technical details (debug mode only)",
  "validation_errors": [
    {
      "field": "amount",
      "message": "Must be positive",
      "value": "-10"
    }
  ]
}
```

## Testing

The TEG Layer includes comprehensive test coverage:
- Unit tests for business logic
- Integration tests for API endpoints
- Database transaction tests
- Mock AVTP integration tests
- Performance benchmarks

Run tests:
```bash
pytest tests/ -v --cov=src/teg_core_service
```

## Future Enhancements

1. **Planned Features**
   - Multi-signature transactions
   - Scheduled/recurring transfers
   - Advanced staking pools
   - Governance voting mechanisms
   - Cross-chain bridge support

2. **Performance Optimizations**
   - Redis caching layer
   - Database query optimization
   - Bulk transaction processing
   - WebSocket support for real-time updates

3. **Enhanced Security**
   - Hardware wallet integration
   - Multi-factor authentication
   - Advanced fraud detection
   - Quantum-resistant cryptography preparation