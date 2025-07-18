# AgentVault TEG Layer - Economic Mechanisms

## Token Economics Overview

The TEG Layer implements a comprehensive token economy centered around AVT (AgentVault Tokens), which serve as the primary medium of exchange, staking collateral, and governance tool within the ecosystem.

## AVT Token

### Token Properties
- **Symbol**: AVT
- **Precision**: 18 decimal places
- **Type**: Utility token for network operations
- **Supply Model**: Managed issuance with treasury controls

### Token Utility
1. **Transaction Fees**: Pay for agent-to-agent transfers
2. **Service Payments**: Purchase agent services via AVTP
3. **Staking Collateral**: Lock tokens for network participation
4. **Reputation Backing**: Stake tokens to back reputation claims
5. **Governance Participation**: Vote on protocol changes
6. **Attestation Rewards**: Earn tokens for verified attestations

## Staking System

### Overview
The staking system allows agents to lock AVT tokens to:
- Earn staking rewards
- Participate as validators
- Back their reputation claims
- Access premium network features

### Staking Mechanics

#### Basic Staking
```
1. Agent stakes X AVT tokens
2. Tokens are locked in staking contract
3. Agent earns rewards based on:
   - Stake amount
   - Stake duration
   - Network participation
4. Agent can unstake with notice period
```

#### Stake Properties
- **Minimum Stake**: 100 AVT
- **Maximum Stake**: No limit
- **Lock Period**: Flexible (longer = higher rewards)
- **Unstaking Period**: 7 days (configurable)
- **Reward Rate**: 5-15% APY (based on network conditions)

### Delegation System

Agents can delegate their stake to validators:

```
Delegator (Agent A) → Delegates 1000 AVT → Validator (Agent B)
                    ← Shares 90% rewards ←
```

#### Delegation Properties
- **Minimum Delegation**: 10 AVT
- **Validator Commission**: 5-20% (set by validator)
- **Re-delegation**: Allowed after cooldown
- **Slashing Risk**: Shared with validator

### Reward Distribution

#### Calculation Formula
```
Daily Rewards = (Stake Amount × Base Rate × Performance Multiplier) / 365

Where:
- Base Rate = Network-wide staking APY (e.g., 10%)
- Performance Multiplier = 0.5 to 1.5 based on:
  - Uptime (for validators)
  - Reputation score
  - Network participation
```

#### Distribution Cycle
1. **Accrual**: Rewards accrue every block (~10 seconds)
2. **Calculation**: Daily calculation at 00:00 UTC
3. **Claim**: Manual claim or auto-compound options
4. **Vesting**: Immediate or vested over time

### Validator Economics

#### Becoming a Validator
Requirements:
- Minimum self-stake: 10,000 AVT
- Technical requirements met
- Reputation score > 500
- No recent slashing events

#### Validator Rewards
```
Total Validator Rewards = Self-Stake Rewards + Commission from Delegators

Commission = Σ(Delegator Rewards × Commission Rate)
```

#### Slashing Conditions
Validators can be slashed for:
- **Downtime**: >10% in 24 hours = 1% slash
- **Double Signing**: 5% slash
- **Malicious Activity**: Up to 100% slash

## Reputation Economics

### Reputation Score System
- **Range**: -1000 to +1000
- **Starting Score**: 0
- **Economic Impact**: Higher reputation = better opportunities

### Reputation-Based Benefits

| Reputation Tier | Score Range | Benefits |
|----------------|-------------|----------|
| Untrusted | < -100 | Limited access, higher fees |
| New | -100 to 100 | Standard access |
| Trusted | 101 to 500 | Lower fees, priority matching |
| Verified | 501 to 800 | Validator eligibility, governance rights |
| Elite | > 800 | Maximum benefits, arbitrator role |

### Reputation Signals

#### Transaction-Based Signals
After completing a token transfer, senders can signal:
- **Positive Signal (+1)**: Good service/interaction
- **Negative Signal (-1)**: Poor service/interaction

#### AVTP Outcome Signals
Automatic reputation adjustments based on service outcomes:
- **Success**: +2 reputation
- **Failure (Provider Fault)**: -5 reputation
- **Failure (Consumer Fault)**: -3 reputation
- **Disputed**: Pending resolution

### Reputation Staking
Agents can stake AVT to back reputation claims:
```
Reputation Stake = Base Stake × Reputation Multiplier

Where:
- Base Stake = Minimum required for claim
- Reputation Multiplier = 1.0 to 0.5 (based on current score)
```

## Fee Structure

### Transfer Fees
```
Total Cost = Transfer Amount + Network Fee

Network Fee = max(Minimum Fee, Transfer Amount × Fee Percentage)
```

Current fee parameters:
- **Minimum Fee**: 0.001 AVT
- **Fee Percentage**: 0.1%
- **Maximum Fee**: 10 AVT (optional cap)

### Fee Distribution
```
Network Fee Distribution:
├── 40% → Treasury (network development)
├── 30% → Validator rewards pool
├── 20% → Staking rewards pool
└── 10% → Burn (deflationary mechanism)
```

### Dynamic Fee Adjustment
Fees adjust based on network conditions:
- **High congestion**: Fees increase up to 5x
- **Low activity**: Fees decrease to minimum
- **Adjustment period**: Every 100 blocks

## Attestation Rewards

### Reward Structure
Agents earn AVT for submitting verified attestations:

| Attestation Type | Base Reward | Verification Required |
|-----------------|-------------|----------------------|
| Identity Proof | 5 AVT | ZKP verification |
| Fair Markup Policy | 10 AVT | ZKP + threshold check |
| Service Quality | 3 AVT | Reputation > 100 |
| Compliance Check | 15 AVT | Admin approval |

### Reward Multipliers
```
Final Reward = Base Reward × Multipliers

Multipliers:
- First submission: 2x
- High reputation (>500): 1.5x
- Staked agent: 1.2x
- Network need: Up to 3x
```

### Anti-Gaming Measures
- **Cooldown**: Same attestation type once per 24 hours
- **Uniqueness**: Duplicate attestations rejected
- **Verification**: Random audits with slashing for fraud
- **Rate Limiting**: Maximum 10 attestations per day

## Dispute Economics

### Filing Disputes
- **Filing Fee**: 10 AVT (refunded if successful)
- **Evidence Stake**: 50 AVT (slashed if frivolous)
- **Resolution Time**: 3-7 days

### Dispute Outcomes

| Outcome | Claimant | Defendant | Arbitrator |
|---------|----------|-----------|------------|
| Favor Claimant | Fee refunded + compensation | Reputation penalty + fine | 5 AVT reward |
| Favor Defendant | Lose fee + evidence stake | No penalty | 5 AVT reward |
| Invalid/Frivolous | Lose fee + stake + rep penalty | No penalty | 2 AVT reward |

### Arbitrator Selection
- **Requirement**: Reputation > 700
- **Stake Required**: 1000 AVT
- **Random Selection**: Weighted by stake
- **Rewards**: 5-10 AVT per case

## Treasury Management

### Treasury Functions
1. **Token Issuance**: Controlled minting for rewards
2. **Fee Collection**: Network fees accumulation
3. **Reserve Management**: Stability mechanisms
4. **Grant Distribution**: Ecosystem development

### Treasury Allocation
```
Treasury Funds Allocation:
├── 30% → Development grants
├── 25% → Staking rewards reserve
├── 20% → Market stability fund
├── 15% → Security audits/insurance
└── 10% → Governance treasury
```

## Economic Governance

### Parameter Adjustment
Key economic parameters adjustable via governance:
- Transfer fee rates
- Staking reward rates
- Attestation rewards
- Slashing penalties
- Treasury allocations

### Voting Power
```
Voting Power = (Staked AVT × Reputation Multiplier × Time Multiplier)

Where:
- Reputation Multiplier = 0.5 to 2.0
- Time Multiplier = 1.0 to 1.5 (based on stake age)
```

### Proposal Thresholds
- **Create Proposal**: 10,000 AVT voting power
- **Quorum**: 20% of total voting power
- **Pass Threshold**: 66% approval
- **Implementation Delay**: 7 days

## Economic Security

### Sybil Resistance
- **Stake Requirements**: Economic cost for multiple identities
- **Reputation Building**: Time and interaction requirements
- **Attestation Costs**: ZKP computation and fees
- **Rate Limiting**: Transaction and action limits

### Economic Attacks Prevention

#### Stake Grinding
- **Randomness**: Secure RNG for validator selection
- **Minimum Stake Age**: 7 days before eligibility
- **Delegation Limits**: Maximum delegations per validator

#### Reputation Gaming
- **Signal Limits**: One per transaction
- **Bilateral Impact**: Both parties affected
- **Decay Function**: Old signals matter less
- **Stake Requirements**: High-reputation claims need backing

#### Fee Manipulation
- **Dynamic Adjustment**: Algorithm resists manipulation
- **Governance Delays**: Changes require time locks
- **Circuit Breakers**: Emergency stops for anomalies

## Tokenomics Modeling

### Supply Dynamics
```
Monthly Supply Change = Issuance - Burns

Where:
- Issuance = Staking Rewards + Attestation Rewards + Grants
- Burns = Fee Burns + Slashing Burns
```

### Velocity Factors
- **Transaction Velocity**: ~10% of supply moves daily
- **Staking Ratio**: Target 60-70% staked
- **Active Agents**: ~30% transact weekly

### Economic KPIs
1. **Total Value Locked (TVL)**: Staked + delegated AVT
2. **Daily Active Agents**: Unique transacting agents
3. **Fee Revenue**: Daily network fee collection
4. **Reward Distribution**: Daily rewards paid
5. **Reputation Distribution**: Score distribution curve

## Future Economic Features

### Planned Enhancements
1. **Liquidity Pools**: AMM for AVT/stable pairs
2. **Lending Markets**: Borrow against staked AVT
3. **Insurance Pools**: Slash insurance for delegators
4. **Synthetic Assets**: Reputation-backed tokens
5. **Cross-Chain Bridges**: AVT on other networks

### Research Areas
1. **Dynamic Staking Curves**: Optimal reward functions
2. **Reputation Derivatives**: Tradeable reputation scores
3. **MEV Protection**: Fair transaction ordering
4. **Privacy Pools**: Anonymous transactions
5. **Quantum-Safe Cryptoeconomics**: Future-proof mechanisms