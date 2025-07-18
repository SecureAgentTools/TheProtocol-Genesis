# The Sovereign Stack: Forging the Future of Agent-to-Agent Communication

Welcome to the **Sovereign Stack** - a battle-tested, production-ready ecosystem that enables secure, autonomous, and economically-incentivized communication between AI agents.

## Vision: The Age of Autonomous Agents

In a world where AI agents are becoming increasingly sophisticated and numerous, the ability for them to discover each other, communicate reliably, and collaborate securely is no longer optional - it's essential. The Sovereign Stack provides the foundational infrastructure to make this possible, creating a new paradigm where agents can:

- **Discover** each other through federated registries
- **Authenticate** with cryptographic identities
- **Transact** using token economies
- **Collaborate** with trust and accountability
- **Evolve** through reputation and governance

## The Sovereign Stack Architecture

The Sovereign Stack is composed of four battle-hardened pillars, each serving a critical role in the ecosystem:

### 1. **AgentVault Core Framework**
The foundational libraries and tools that power agent development:
- **agentvault_library**: Core Python client for A2A protocol and secure key management
- **agentvault_cli**: Command-line interface for agent operations
- **agentvault_server_sdk**: SDK for building compliant agents

### 2. **Token Economy Graph (TEG) Layer**
The economic engine that incentivizes good behavior:
- Token management with AVT (AgentVault Token)
- Staking and rewards system
- Dispute resolution framework
- Reputation scoring and auditor oversight
- Attestation rewards for network contributions

### 3. **Identity Fabric**
Zero-Trust security through cryptographic workload identities:
- SPIFFE/SPIRE integration for automatic identity rotation
- OPA (Open Policy Agent) for fine-grained authorization
- mTLS for all inter-service communication
- JWT-SVID tokens for API authentication

### 4. **Federated Registry**
The discovery backbone of the network:
- Decentralized agent discovery
- OAuth 2.0 bridge for secure agent onboarding
- Agent templates and metadata management
- Rate-limited bootstrap token system

## Documentation Structure

This documentation is organized to serve different audiences and purposes:

### For New Developers
- **[Getting Started](getting-started/installation.md)**: Installation, setup, and your first agent
  - [Installation Guide](getting-started/installation.md)
  - [Running the Stack](getting-started/running-the-stack.md)

### For Architects
- **[Architecture](architecture/overview.md)**: Deep technical dives into each component
  - [System Overview](architecture/overview.md)
  - [Registry Architecture](architecture/registry.md)
  - [TEG Layer](architecture/teg_layer.md)
  - [Identity Fabric](architecture/identity_fabric.md)

### For Builders
- **[Developer Guides](developer-guides/building-an-agent.md)**: Practical tutorials and references
  - [Building an Agent](developer-guides/building-an-agent.md)
  - [CLI Reference](developer-guides/cli-reference.md)
  - [Onboarding Protocol](developer-guides/onboarding-protocol.md)

### For Operators
- **[Operations](IDENTITY_FABRIC_OPERATIONS.md)**: Running and maintaining the stack
  - [SPIRE Workload Registration](SPIRE_WORKLOAD_REGISTRATION.md)
  - [SPIRE Quick Reference](SPIRE_QUICK_REFERENCE.md)
  - [SPIRE Agent Fix Success Log](SPIRE_AGENT_FIX_SUCCESS_LOG.md)
  - [SPIRE Agent Quick Fix Guide](SPIRE_AGENT_QUICK_FIX_GUIDE.md)
  - [Federation Status Guide](FEDERATION_STATUS.md)
  - [Identity Fabric Operations](IDENTITY_FABRIC_OPERATIONS.md)

### Reference
- **[API & Schema Documentation](reference/agent-card-schema.md)**
  - [Agent Card Schema](reference/agent-card-schema.md)

### For Visionaries
- **[Philosophy](philosophy.md)**: The principles that guide our development

## Quick Start

Ready to dive in? Here's the fastest path to running your first agent:

```bash
# Clone the repository
git clone https://github.com/SecureAgentTools/SovereignStack

# Install dependencies
cd SovereignStack
poetry install

# Start the core services
docker-compose up -d

# Create your first agent
agentvault_cli agent create my-first-agent
```

## Core Principles

The Sovereign Stack is built on uncompromising principles:

1. **Cryptographic Identity First**: Every agent has a verifiable identity
2. **Economic Incentives**: Good behavior is rewarded, bad behavior is punished
3. **Decentralized by Design**: No single point of failure or control
4. **Developer Experience**: APIs that are a joy to use
5. **Production Ready**: Battle-tested and ready for scale

## The Warrior Owl Doctrine

This project embodies the **Warrior Owl** philosophy - combining the strategic wisdom of the owl with the fierce execution of the warrior. Every component is built with:

- **Proof, Not Promises**: Every feature is verified through code
- **Excellence Mode**: No shortcuts, no compromises
- **Human-AI Trinity**: Seamless collaboration between human architects and AI executors

## Join the Revolution

The age of autonomous agents is here. The infrastructure is built. The protocols are defined. The economy is operational.

Now it's time to build the agents that will change the world.

Welcome to the Sovereign Stack. Welcome to the future.

---

*"In the union of human wisdom and artificial intelligence, we forge systems that transcend the limitations of either alone."*

**- The Warrior Owl Doctrine**
