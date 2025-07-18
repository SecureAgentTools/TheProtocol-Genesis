# Token Economy Graph (TEG) Layer Architecture

## Overview

The Token Economy Graph (TEG) Layer is the economic engine of the Sovereign Stack, implementing a comprehensive token-based incentive system that ensures good behavior, rewards contributions, and enables sustainable agent interactions. It transforms abstract concepts of trust and reputation into concrete economic mechanisms.

## System Architecture

### Core Components

The TEG Layer consists of seven interconnected subsystems:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TEG LAYER ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ Token Management│    │Staking & Rewards│    │Reputation System│             │
│  │                 │    │                 │    │                 │             │
│  │ • AVT Tokens    │    │ • Stake AVT     │    │ • Score Calc    │             │
│  │ • Transfers     │    │ • Delegations   │    │ • Rankings      │             │
│  │ • Balances      │    │ • Distributions │    │ • Trust Levels  │             │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘             │
│           │                       │                       │                       │
│  ┌────────▼───────────────────────▼───────────────────────▼────────┐             │
│  │                        CORE TRANSACTION ENGINE                   │             │
│  │                                                                  │             │
│  │  • Atomic Operations    • Audit Trail    • Fee Management       │             │
│  │  • Balance Verification • Idempotency    • Event Emission       │             │
│  └────────┬─────────────────────────────────────────────┬──────────┘             │
│           │                                             │                         │
│  ┌────────▼────────┐    ┌─────────────────┐    ┌──────▼───────┐                │
│  │Attestation System│    │Dispute Resolution│    │Auditor System│                │
│  │                 │    │                 │    │              │                │
│  │ • ZKP Support   │    │ • Kleros DDR    │    │ • Anomaly    │                │
│  │ • IPFS Storage  │    │ • Evidence      │    │   Detection  │                │
│  │ • Rewards       │    │ • Arbitration   │    │ • Auto Flags │                │
│  └─────────────────┘    └─────────────────┘    └──────────────┘                │
│                                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐      │
│  │                          POLICY GOVERNANCE ENGINE                      │      │
│  │                                                                        │      │
│  │  • Community Policies  • Reward Parameters  • Economic Constants      │      │
│  └───────────────────────────────────────────────────────────────────────┘      │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Framework**: FastAPI with async/await patterns
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Token Precision**: 36 decimal places total, 18 decimal precision
- **External Storage**: IPFS for attestation data
- **Integration**: AVTP protocol for external transactions

## Data Models

### Core Entities

#### AgentTEGProfile
The economic identity of each agent:

```python
class AgentTEGProfile(Base):
    __tablename__ = "agent_teg_profiles"
    
    agent_id: str = Column(String(255), primary_key=True)  # Agent DID
    token_balance: Decimal = Column(Numeric(36, 18), default=0)
    reputation_score: int = Column(Integer, default=0)
    account_status: str = Column(String(50), default="active")
    
    # Statistics
    total_attestations: int = Column(Integer, default=0)
    successful_transactions: int = Column(Integer, default=0)
    failed_transactions: int = Column(Integer, default=0)
    disputes_won: int = Column(Integer, default=0)
    disputes_lost: int = Column(Integer, default=0)
    
    # Timestamps
    created_at: datetime = Column(DateTime, server_default=func.now())
    updated_at: datetime = Column(DateTime, onupdate=func.now())
    last_activity: datetime = Column(DateTime)
```

#### TEGTransaction
Complete audit trail for all token movements:

```python
class TEGTransaction(Base):
    __tablename__ = "teg_transactions"
    
    transaction_id: str = Column(String(36), primary_key=True)
    sender_agent_id: str = Column(String(255), nullable=True)  # null for issuance
    receiver_agent_id: str = Column(String(255), nullable=False)
    amount: Decimal = Column(Numeric(36, 18), nullable=False)
    fee_amount: Decimal = Column(Numeric(36, 18), default=0)
    
    # Transaction metadata
    transaction_type: str = Column(String(50))  # transfer/issuance/burn/reward
    status: str = Column(String(50), default="pending")
    attached_message: str = Column(String(256))
    reference_id: str = Column(String(255))  # For idempotency
    
    # Relationships
    created_at: datetime = Column(DateTime, server_default=func.now())
    completed_at: datetime = Column(DateTime)
```

#### Stake
Locked tokens for network participation:

```python
class Stake(Base):
    __tablename__ = "stakes"
    
    stake_id: str = Column(String(36), primary_key=True)
    agent_id: str = Column(String(255), ForeignKey("agent_teg_profiles.agent_id"))
    amount: Decimal = Column(Numeric(36, 18), nullable=False)
    staked_at: datetime = Column(DateTime, server_default=func.now())
    unstaked_at: datetime = Column(DateTime, nullable=True)
    is_active: bool = Column(Boolean, default=True)
    last_reward_claim: datetime = Column(DateTime, nullable=True)
    
    # Computed fields
    @property
    def duration_days(self) -> int:
        end_time = self.unstaked_at or datetime.utcnow()
        return (end_time - self.staked_at).days
```

## Economic Mechanisms

### Token Management

#### AVT (AgentVault Token)
The native utility token with specific properties:

- **Precision**: 18 decimal places for micropayments
- **Supply Management**: Controlled issuance and burn mechanisms
- **Transfer Fees**: Configurable per transaction type
- **Minimum Balance**: Prevents dust attacks

#### Transaction Flow
```python
async def transfer_tokens(
    sender_id: str,
    receiver_id: str,
    amount: Decimal,
    message: Optional[str] = None
) -> TEGTransaction:
    async with db.begin():
        # 1. Verify sender balance
        sender = await get_agent_profile(sender_id)
        if sender.token_balance < amount + fee:
            raise InsufficientBalanceError()
        
        # 2. Create transaction record
        tx = TEGTransaction(
            transaction_id=generate_uuid(),
            sender_agent_id=sender_id,
            receiver_agent_id=receiver_id,
            amount=amount,
            fee_amount=fee,
            transaction_type="transfer",
            attached_message=message
        )
        
        # 3. Update balances atomically
        sender.token_balance -= (amount + fee)
        receiver.token_balance += amount
        treasury.token_balance += fee
        
        # 4. Emit events
        await emit_transfer_event(tx)
        
        return tx
```

### Staking & Rewards System

#### Staking Mechanics

Agents stake AVT tokens to demonstrate commitment and earn rewards:

1. **Minimum Stake**: 10 AVT (configurable)
2. **Lock Period**: No enforced minimum
3. **Reward Rate**: 5% APY distributed proportionally
4. **Compound Option**: Auto-reinvest rewards

#### Delegation System

Agents can delegate stake to validators:

```python
class Delegation(Base):
    __tablename__ = "delegations"
    
    delegation_id: str = Column(String(36), primary_key=True)
    delegator_agent_id: str = Column(String(255))
    validator_agent_id: str = Column(String(255))
    stake_id: str = Column(String(36), ForeignKey("stakes.stake_id"))
    delegated_amount: Decimal = Column(Numeric(36, 18))
    reward_share_percentage: Decimal = Column(Numeric(5, 2), default=10.0)
    is_active: bool = Column(Boolean, default=True)
```

#### Reward Distribution Algorithm

```python
async def distribute_staking_rewards(reward_percentage: Decimal):
    """Distribute rewards to all active stakes and delegations"""
    
    # Calculate total rewards pool
    total_staked = await get_total_staked_amount()
    total_rewards = total_staked * (reward_percentage / 100)
    
    # Distribute to direct stakers
    for stake in await get_active_stakes():
        stake_reward = (stake.amount / total_staked) * total_rewards
        await issue_reward(stake.agent_id, stake_reward, "staking")
    
    # Distribute to delegations
    for delegation in await get_active_delegations():
        delegation_reward = (delegation.amount / total_staked) * total_rewards
        
        # Split between delegator and validator
        validator_share = delegation_reward * (delegation.reward_share_percentage / 100)
        delegator_share = delegation_reward - validator_share
        
        await issue_reward(delegation.validator_agent_id, validator_share, "delegation_validator")
        await issue_reward(delegation.delegator_agent_id, delegator_share, "delegation_delegator")
```

### Reputation System

#### Score Calculation

Reputation is calculated using weighted factors:

```python
def calculate_reputation_score(agent_id: str) -> int:
    """Calculate agent reputation based on multiple factors"""
    
    profile = get_agent_profile(agent_id)
    
    # Base factors
    attestation_score = profile.total_attestations * W2_ATTESTATION_WEIGHT
    transaction_score = (
        profile.successful_transactions * W3_SUCCESSFUL_TXN_WEIGHT -
        profile.failed_transactions * W4_FAILED_TXN_WEIGHT
    )
    
    # Stake influence (capped)
    effective_stake = min(profile.total_staked, MAX_STAKE_EFFECTIVE_FOR_REP)
    stake_score = effective_stake * W1_STAKE_WEIGHT
    
    # Penalties
    flag_penalty = count_critical_flags(agent_id) * W5_CRITICAL_FLAG_PENALTY
    dispute_penalty = profile.disputes_lost * W6_NEGATIVE_DDR_PENALTY
    
    # Calculate final score
    raw_score = (
        attestation_score + 
        transaction_score + 
        stake_score - 
        flag_penalty - 
        dispute_penalty
    )
    
    return max(MIN_REPUTATION_SCORE, int(raw_score))
```

#### Reputation Tiers

| Score Range | Tier | Benefits |
|-------------|------|----------|
| 0-99 | Novice | Basic network access |
| 100-499 | Trusted | Reduced transaction fees |
| 500-999 | Veteran | Priority processing |
| 1000-4999 | Expert | Governance participation |
| 5000+ | Master | Validator eligibility |

### Attestation System

#### Submission Flow

Agents earn rewards for contributing verified information:

```python
@router.post("/api/v1/attestations/submit")
async def submit_attestation(
    attestation: AttestationSubmission,
    agent_id: str = Depends(verify_agent_identity)
):
    # 1. Validate attestation format
    validate_attestation_schema(attestation)
    
    # 2. Store attestation data
    attestation_log = TEGAttestationLog(
        submission_id=generate_uuid(),
        agent_did=agent_id,
        attestation_type=attestation.type,
        attestation_hash=attestation.hash,
        storage_pointer=attestation.ipfs_cid,
        circuit_id=attestation.zkp_circuit,
        zkp_proof_value=attestation.zkp_proof
    )
    
    # 3. Issue reward
    reward_amount = get_policy_reward(attestation.type)
    await transfer_tokens(
        sender_id=TREASURY_DID,
        receiver_id=agent_id,
        amount=reward_amount,
        message=f"Attestation reward: {attestation.type}"
    )
    
    # 4. Update reputation
    await update_reputation(agent_id, "attestation_submitted")
    
    return {"submission_id": attestation_log.submission_id, "reward": reward_amount}
```

#### Zero-Knowledge Proof Support

For privacy-preserving attestations:

```json
{
  "attestation_type": "fair_pricing",
  "attestation_hash": "0x3f4a...",
  "storage_pointer": "ipfs://QmXyz...",
  "circuit_identifier": "fairPricing/v1.0.0",
  "zkp_proof": {
    "public_inputs": {
      "max_markup": "30",
      "timestamp": "1719270000"
    },
    "proof": "0xabcd..."
  }
}
```

### Dispute Resolution

#### Dispute Lifecycle

```
OPEN → UNDER_REVIEW → AWAITING_ARBITRATION → RESOLVED
                    ↓                      ↓
                 REJECTED              ABANDONED
```

#### Dispute Categories

- **UnfairFee**: Excessive service charges
- **FailedService**: Service not delivered
- **ReputationAbuse**: Gaming the system
- **ContractViolation**: Breaking agreements
- **DataIntegrity**: False attestations

### Auditor System

#### Automated Monitoring

The algorithmic auditor continuously monitors for anomalies:

```python
class AuditorRule:
    def __init__(self, rule_code: str, severity: str):
        self.rule_code = rule_code
        self.severity = severity
    
    async def evaluate(self, context: dict) -> Optional[AuditorFlag]:
        """Override in subclasses"""
        pass

class HighVelocityRule(AuditorRule):
    """Detect unusually high transaction velocity"""
    
    async def evaluate(self, context: dict) -> Optional[AuditorFlag]:
        agent_id = context["agent_id"]
        tx_count = await count_recent_transactions(agent_id, minutes=5)
        
        if tx_count > 100:  # Threshold
            return AuditorFlag(
                flagged_agent_did=agent_id,
                rule_violated_code="HIGH_VELOCITY_V1",
                flag_reason=f"Agent executed {tx_count} transactions in 5 minutes",
                severity="HIGH"
            )
        return None
```

## API Reference

### Token Operations

#### Transfer Tokens
```http
POST /api/v1/token/transfer
Authorization: Bearer <token>
Content-Type: application/json

{
  "receiver_agent_id": "did:agentvault:bob",
  "amount": "100.5",
  "message": "Payment for AI consultation"
}

Response: 200 OK
{
  "transaction_id": "tx_abc123",
  "status": "completed",
  "sender_balance": "899.5",
  "timestamp": "2025-06-17T10:00:00Z"
}
```

#### Check Balance
```http
GET /api/v1/token/balance
Authorization: Bearer <token>

Response: 200 OK
{
  "agent_id": "did:agentvault:alice",
  "balance": "1000.0",
  "staked": "500.0",
  "available": "500.0",
  "pending": "0.0"
}
```

### Staking Operations

#### Create Stake
```http
POST /api/v1/staking/stake
Authorization: Bearer <token>

{
  "amount": "1000.0"
}

Response: 200 OK
{
  "stake_id": "stk_xyz789",
  "amount": "1000.0",
  "staked_at": "2025-06-17T10:00:00Z",
  "estimated_apy": "5.0"
}
```

#### Delegate Stake
```http
POST /api/v1/staking/delegate
Authorization: Bearer <token>

{
  "stake_id": "stk_xyz789",
  "validator_agent_id": "did:agentvault:validator1",
  "amount": "500.0",
  "reward_share_percentage": "15.0"
}
```

### Reputation Operations

#### Get Reputation Score
```http
GET /api/v1/agents/{agent_id}/reputation

Response: 200 OK
{
  "agent_id": "did:agentvault:alice",
  "reputation_score": 1250,
  "tier": "Expert",
  "factors": {
    "attestations": 500,
    "transactions": 400,
    "stake_influence": 200,
    "penalties": -50
  },
  "percentile": 85
}
```

### Admin Operations

#### Issue Tokens
```http
POST /api/v1/admin/token/issue
X-Admin-Key: <admin_key>

{
  "recipient_agent_id": "did:agentvault:treasury",
  "amount": "10000.0",
  "reason": "Initial treasury funding"
}
```

#### Trigger Reward Distribution
```http
POST /api/v1/admin/staking/trigger-reward-cycle
X-Admin-Key: <admin_key>

{
  "reward_percentage": "5.0"
}
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/teg

# Security
ADMIN_API_KEY=your-secure-admin-key
JWT_PUBLIC_KEY_PATH=/keys/jwt_public.pem

# Token Economy
DEFAULT_TRANSFER_FEE=0.0
MIN_TRANSFER_AMOUNT=0.01
MIN_STAKE_AMOUNT=10.0
ATTESTATION_SUBMISSION_REWARD=0.1

# Reputation Weights
W1_STAKE_WEIGHT=0.1
W2_ATTESTATION_WEIGHT=2.0
W3_SUCCESSFUL_TXN_WEIGHT=1.0
W4_FAILED_TXN_WEIGHT=2.0
W5_CRITICAL_FLAG_PENALTY=50.0
W6_NEGATIVE_DDR_PENALTY=100.0

# System Accounts
TEG_SYSTEM_TREASURY_DID=did:agentvault:teg_treasury
```

### Policy Configuration

```python
# Default policies
DEFAULT_POLICIES = [
    {
        "policy_code": "FAIR_PRICING_V1",
        "policy_name": "Fair Pricing Attestation",
        "reward_amount": Decimal("0.5"),
        "parameters": {
            "max_markup_percentage": 30,
            "verification_required": True
        }
    },
    {
        "policy_code": "QUALITY_SERVICE_V1", 
        "policy_name": "Service Quality Attestation",
        "reward_amount": Decimal("0.3"),
        "parameters": {
            "min_success_rate": 95
        }
    }
]
```

## Security Considerations

### Economic Security

1. **Sybil Resistance**
   - Staking requirements create cost for fake accounts
   - Reputation building requires time and genuine activity
   - Bootstrap tokens limit registration rate

2. **Market Manipulation**
   - Auditor monitors for wash trading
   - Transaction velocity limits
   - Large transfer notifications

3. **Smart Contract Bridge** (Future)
   - Multi-signature treasury
   - Time-locked withdrawals
   - Oracle price feeds

### Operational Security

1. **Access Control**
   - Admin endpoints require separate API key
   - Agent operations use JWT-SVID tokens
   - All actions logged with actor identity

2. **Data Integrity**
   - All transactions are immutable once completed
   - Attestations use content-addressed storage (IPFS)
   - Audit trail for all state changes

## Performance Optimization

### Database Optimization

1. **Indexes**
   ```sql
   CREATE INDEX idx_transactions_agent ON teg_transactions(sender_agent_id, receiver_agent_id);
   CREATE INDEX idx_stakes_active ON stakes(agent_id) WHERE is_active = true;
   CREATE INDEX idx_attestations_agent ON attestation_logs(agent_did, created_at DESC);
   ```

2. **Partitioning** (PostgreSQL)
   ```sql
   CREATE TABLE teg_transactions_2025_q2 PARTITION OF teg_transactions
   FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
   ```

### Caching Strategy

```python
# Redis caching for hot data
@cache(ttl=300)  # 5 minutes
async def get_agent_balance(agent_id: str) -> Decimal:
    profile = await db.get(AgentTEGProfile, agent_id)
    return profile.token_balance

@cache(ttl=3600)  # 1 hour
async def get_reputation_percentile(score: int) -> int:
    return await calculate_percentile_rank(score)
```

## Deployment Architecture

### Service Configuration

```yaml
services:
  teg-core:
    build: ./agentvault_teg_layer_mvp
    environment:
      - DATABASE_URL=${TEG_DATABASE_URL}
      - ADMIN_API_KEY=${TEG_ADMIN_KEY}
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
```

### Health Monitoring

```python
@router.get("/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "ipfs": await check_ipfs_gateway(),
        "balance_integrity": await verify_balance_consistency()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

## Future Roadmap

### Phase 1: Current Implementation ✓
- Basic token transfers
- Staking and delegation
- Reputation calculation
- Attestation rewards

### Phase 2: Enhanced Features (Q3 2025)
- Automated market makers
- Liquidity pools
- Advanced governance voting
- Cross-chain bridges

### Phase 3: Full Decentralization (Q4 2025)
- On-chain settlement
- Decentralized sequencer
- Zero-knowledge rollups
- DAO governance

---

The TEG Layer transforms trust into tangible value, creating an economy where good behavior is profitable and bad behavior is expensive. It's the economic foundation that enables truly autonomous agent interactions at scale.
