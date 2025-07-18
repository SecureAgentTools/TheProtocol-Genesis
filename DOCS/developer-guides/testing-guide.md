# Testing Guide

Comprehensive guide for testing agents, services, and integrations in The Protocol ecosystem.

## Overview

Testing is crucial for building reliable agents and services. This guide covers:
- Unit testing agents and services
- Integration testing with the registry
- End-to-end testing of economic flows
- Performance and load testing
- Security testing patterns

## Testing Philosophy

The Protocol follows these testing principles:

1. **Test Reality, Not Mocks**: Prefer integration tests with real services over heavily mocked unit tests
2. **Economic Flows Matter**: Always test token movements and economic constraints
3. **Federation Complexity**: Test cross-registry scenarios early and often
4. **Security by Default**: Include security tests in your standard suite
5. **Performance Awareness**: Measure and assert on performance characteristics

## Setting Up Your Test Environment

### Test Configuration

Create a `test.env` file for test-specific settings:

```bash
# Test Database (separate from development)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/test_agentvault

# Test Registry
TEST_REGISTRY_URL=http://localhost:8000
TEST_API_KEY=test_api_key_for_testing_only

# Test TEG Layer
TEST_TEG_URL=http://localhost:8080
TEST_TEG_ADMIN_KEY=test_admin_key

# Test DIDs
TEST_AGENT_DID=did:agentvault:test_agent_001
TEST_TREASURY_DID=did:agentvault:test_treasury

# Faster timeouts for tests
REQUEST_TIMEOUT=5
ATTESTATION_TIMEOUT=30
```

### Docker Compose for Testing

Create `docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  test_db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_agentvault
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
    volumes:
      - test_pg_data:/var/lib/postgresql/data

  test_registry:
    build: ./agentvault_registry
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@test_db:5432/test_agentvault
      API_KEY_SECRET: test_secret
      TESTING_MODE: "true"
    ports:
      - "8002:8000"
    depends_on:
      - test_db

  test_teg:
    build: ./agentvault_teg_layer_mvp
    environment:
      DATABASE_URL: sqlite:///./test_teg.db
      ADMIN_API_KEY: test_admin_key
      TESTING_MODE: "true"
    ports:
      - "8082:8080"

volumes:
  test_pg_data:
```

## Unit Testing Agents

### Basic Agent Test Structure

```python
import pytest
from sovereign_sdk import Agent, TestClient
from your_agent import MyAgent

class TestMyAgent:
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return MyAgent(
            did="did:agentvault:test_agent",
            capabilities=["data_processing", "attestation"]
        )
    
    @pytest.fixture
    def test_client(self, agent):
        """Create test client for the agent."""
        return TestClient(agent)
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.did == "did:aventvault:test_agent"
        assert "data_processing" in agent.capabilities
        assert agent.is_ready()
    
    def test_capability_execution(self, test_client):
        """Test agent executes capabilities correctly."""
        response = test_client.post(
            "/execute",
            json={
                "capability": "data_processing",
                "params": {"data": "test_input"}
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert "processed_data" in result
```

### Testing Economic Features

```python
import pytest
from decimal import Decimal
from sovereign_sdk import EconomicAgent, MockTEGLayer

class TestEconomicAgent:
    @pytest.fixture
    def mock_teg(self):
        """Create mock TEG layer for testing."""
        return MockTEGLayer(initial_balance=Decimal("100.0"))
    
    @pytest.fixture
    def economic_agent(self, mock_teg):
        """Create economic agent with mock TEG."""
        return EconomicAgent(
            did="did:agentvault:test_economic",
            teg_layer=mock_teg,
            stake_amount=Decimal("10.0")
        )
    
    @pytest.mark.asyncio
    async def test_staking_requirement(self, economic_agent):
        """Test agent meets staking requirements."""
        # Verify initial stake
        stake = await economic_agent.get_stake_amount()
        assert stake == Decimal("10.0")
        
        # Test insufficient stake handling
        economic_agent.stake_amount = Decimal("5.0")
        with pytest.raises(InsufficientStakeError):
            await economic_agent.provide_service()
    
    @pytest.mark.asyncio
    async def test_payment_flow(self, economic_agent, mock_teg):
        """Test complete payment flow."""
        client_did = "did:agentvault:test_client"
        service_fee = Decimal("1.0")
        
        # Client pays for service
        await mock_teg.transfer(
            from_did=client_did,
            to_did=economic_agent.did,
            amount=service_fee
        )
        
        # Verify payment received
        balance = await economic_agent.get_balance()
        assert balance == Decimal("111.0")  # 100 + 10 stake + 1 payment
        
        # Execute service
        result = await economic_agent.execute_paid_service(
            client_did=client_did,
            payment_tx_id="test_tx_123"
        )
        
        assert result["status"] == "completed"
        assert mock_teg.get_transaction("test_tx_123") is not None
```

### Testing Agent Cards

```python
def test_agent_card_generation(agent):
    """Test agent generates valid agent card."""
    card = agent.generate_agent_card()
    
    # Validate structure
    assert card["did"] == agent.did
    assert card["capabilities"] == agent.capabilities
    assert "endpoints" in card
    assert "metadata" in card
    assert "signature" in card
    
    # Validate signature
    assert agent.verify_agent_card(card) is True
    
    # Test tampering detection
    card["capabilities"].append("unauthorized_capability")
    assert agent.verify_agent_card(card) is False
```

## Integration Testing with Registry

### Registry Integration Tests

```python
import pytest
import asyncio
from sovereign_sdk import RegistryClient

class TestRegistryIntegration:
    @pytest.fixture
    async def registry_client(self):
        """Create registry client for testing."""
        client = RegistryClient(
            registry_url="http://localhost:8002",
            api_key="test_api_key"
        )
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, registry_client, agent):
        """Test agent registration with registry."""
        # Generate agent card
        agent_card = agent.generate_agent_card()
        
        # Register with registry
        response = await registry_client.register_agent(agent_card)
        
        assert response["status"] == "registered"
        assert "agent_id" in response
        
        # Verify agent is discoverable
        search_result = await registry_client.search_agents(
            capability="data_processing"
        )
        
        assert len(search_result) > 0
        assert any(a["did"] == agent.did for a in search_result)
    
    @pytest.mark.asyncio
    async def test_federation_discovery(self, registry_client):
        """Test cross-registry agent discovery."""
        # Search across federated registries
        results = await registry_client.federated_search(
            capability="rare_capability",
            include_remote=True
        )
        
        # Should find agents from multiple registries
        registries = set(r["registry_id"] for r in results)
        assert len(registries) >= 2
```

### Testing Attestations

```python
class TestAttestationFlow:
    @pytest.mark.asyncio
    async def test_attestation_lifecycle(self, registry_client, agent):
        """Test complete attestation lifecycle."""
        # Submit attestation
        attestation = {
            "claim": "data_quality_verified",
            "subject_did": "did:agentvault:data_provider",
            "evidence": {"accuracy": 0.99, "sample_size": 1000}
        }
        
        result = await agent.submit_attestation(attestation)
        attestation_id = result["attestation_id"]
        
        # Wait for attestation to be processed
        await asyncio.sleep(2)
        
        # Verify attestation status
        status = await registry_client.get_attestation_status(attestation_id)
        assert status["state"] == "active"
        assert status["attestor_did"] == agent.did
        
        # Test attestation query
        attestations = await registry_client.query_attestations(
            subject_did="did:agentvault:data_provider"
        )
        
        assert len(attestations) > 0
        assert attestations[0]["claim"] == "data_quality_verified"
```

## End-to-End Testing

### Complete Workflow Tests

```python
class TestE2EWorkflow:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_marketplace_transaction(self):
        """Test complete marketplace transaction flow."""
        # Setup participants
        buyer = await create_test_agent("buyer", initial_balance=100)
        seller = await create_test_agent("seller", stake=10)
        marketplace = await create_test_agent("marketplace", stake=50)
        
        # Seller lists item
        listing = await seller.create_listing({
            "item": "dataset_001",
            "price": Decimal("5.0"),
            "description": "High-quality dataset"
        })
        
        # Marketplace validates and publishes
        await marketplace.validate_listing(listing)
        published = await marketplace.publish_listing(listing)
        
        # Buyer discovers and purchases
        listings = await buyer.search_listings(query="dataset")
        assert len(listings) > 0
        
        purchase_result = await buyer.purchase_item(
            listing_id=published["id"],
            seller_did=seller.did
        )
        
        # Verify economic flows
        assert purchase_result["status"] == "completed"
        
        # Check balances
        buyer_balance = await buyer.get_balance()
        seller_balance = await seller.get_balance()
        marketplace_balance = await marketplace.get_balance()
        
        assert buyer_balance == Decimal("95.0")  # 100 - 5
        assert seller_balance == Decimal("14.75")  # 10 + 4.75 (5 - 0.25 fee)
        assert marketplace_balance == Decimal("50.25")  # 50 + 0.25 fee
```

### Federation E2E Tests

```python
@pytest.mark.asyncio
@pytest.mark.federation
async def test_cross_registry_collaboration():
    """Test agents collaborating across registries."""
    # Setup agents in different registries
    registry_a_client = RegistryClient("http://localhost:8000")
    registry_b_client = RegistryClient("http://localhost:8001")
    
    agent_a = await create_and_register_agent(
        registry_a_client,
        "processor_a",
        ["data_processing"]
    )
    
    agent_b = await create_and_register_agent(
        registry_b_client,
        "analyzer_b",
        ["data_analysis"]
    )
    
    # Agent A discovers Agent B through federation
    analysts = await agent_a.discover_collaborators(
        capability="data_analysis",
        cross_registry=True
    )
    
    assert len(analysts) > 0
    analyzer = analysts[0]
    assert analyzer["did"] == agent_b.did
    
    # Establish collaboration with economic agreement
    collaboration = await agent_a.propose_collaboration(
        partner_did=agent_b.did,
        terms={
            "revenue_split": {"processor": 0.6, "analyzer": 0.4},
            "min_stake": Decimal("10.0")
        }
    )
    
    # Agent B accepts
    acceptance = await agent_b.accept_collaboration(collaboration["id"])
    
    # Execute joint service
    client_request = {
        "data": "raw_data_to_process_and_analyze",
        "payment": Decimal("10.0")
    }
    
    result = await execute_joint_service(
        agent_a, agent_b, client_request
    )
    
    assert result["status"] == "completed"
    assert result["processor_earning"] == Decimal("6.0")
    assert result["analyzer_earning"] == Decimal("4.0")
```

## Performance Testing

### Load Testing Agents

```python
import asyncio
import time
from locust import HttpUser, task, between

class AgentLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup before load test."""
        # Get API key for testing
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "test_password"
        })
        self.api_key = response.json()["api_key"]
        self.headers = {"X-API-Key": self.api_key}
    
    @task(3)
    def test_capability_execution(self):
        """Test agent capability under load."""
        response = self.client.post(
            "/execute",
            json={
                "capability": "data_processing",
                "params": {"data": "test_" + str(time.time())}
            },
            headers=self.headers
        )
        
        assert response.status_code == 200
    
    @task(1)
    def test_concurrent_attestations(self):
        """Test attestation submission under load."""
        response = self.client.post(
            "/attestations",
            json={
                "claim": "performance_test",
                "subject_did": f"did:agentvault:subject_{time.time()}",
                "evidence": {"test": True}
            },
            headers=self.headers
        )
        
        assert response.status_code in [200, 201]
```

### Benchmarking Economic Operations

```python
@pytest.mark.benchmark
async def test_transaction_throughput():
    """Benchmark transaction processing throughput."""
    teg_client = TEGClient("http://localhost:8080")
    
    # Prepare test accounts
    accounts = []
    for i in range(100):
        did = f"did:agentvault:bench_account_{i}"
        await teg_client.create_account(did)
        await teg_client.fund_account(did, Decimal("100.0"))
        accounts.append(did)
    
    # Benchmark transfers
    start_time = time.time()
    tasks = []
    
    for i in range(1000):
        from_account = accounts[i % 100]
        to_account = accounts[(i + 1) % 100]
        
        task = teg_client.transfer(
            from_did=from_account,
            to_did=to_account,
            amount=Decimal("0.1")
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    # Calculate metrics
    successful = sum(1 for r in results if not isinstance(r, Exception))
    duration = end_time - start_time
    tps = successful / duration
    
    print(f"Transaction throughput: {tps:.2f} TPS")
    print(f"Success rate: {successful/1000*100:.1f}%")
    
    # Assert minimum performance
    assert tps > 50  # Minimum 50 TPS
    assert successful > 950  # >95% success rate
```

## Security Testing

### Authentication and Authorization Tests

```python
class TestSecurity:
    @pytest.mark.security
    async def test_unauthorized_access(self, registry_client):
        """Test unauthorized access is blocked."""
        # Remove auth header
        registry_client.api_key = None
        
        with pytest.raises(UnauthorizedError):
            await registry_client.register_agent({"test": "data"})
    
    @pytest.mark.security
    async def test_api_key_rotation(self, agent):
        """Test API key rotation maintains security."""
        old_key = agent.api_key
        
        # Rotate key
        new_key = await agent.rotate_api_key()
        assert new_key != old_key
        
        # Old key should be invalid
        agent.api_key = old_key
        with pytest.raises(UnauthorizedError):
            await agent.submit_attestation({"test": "data"})
        
        # New key should work
        agent.api_key = new_key
        result = await agent.get_status()
        assert result["status"] == "active"
    
    @pytest.mark.security
    async def test_injection_prevention(self, registry_client):
        """Test SQL/NoSQL injection prevention."""
        malicious_inputs = [
            "'; DROP TABLE agents; --",
            '{"$ne": null}',
            "<script>alert('xss')</script>",
            "../../../etc/passwd"
        ]
        
        for payload in malicious_inputs:
            # Should handle safely without errors
            results = await registry_client.search_agents(
                capability=payload
            )
            # Results should be empty, not error
            assert results == []
```

### Testing SPIRE Integration

```python
@pytest.mark.requires_spire
class TestSPIREIntegration:
    async def test_svid_validation(self, agent):
        """Test SPIRE SVID validation."""
        # Get agent's SVID
        svid = await agent.get_svid()
        
        assert svid is not None
        assert svid.spiffe_id == f"spiffe://agentvault.com/agent/{agent.did}"
        
        # Verify SVID is valid
        validation = await agent.validate_svid(svid)
        assert validation["valid"] is True
        assert validation["expires_at"] > time.time()
    
    async def test_mutual_tls(self, agent_a, agent_b):
        """Test mTLS between agents."""
        # Establish secure channel
        channel = await agent_a.create_secure_channel(agent_b.did)
        
        # Send encrypted message
        message = {"secret": "classified_data"}
        response = await channel.send(message)
        
        assert response["status"] == "delivered"
        assert response["encrypted"] is True
```

## Test Utilities and Helpers

### Test Fixtures

```python
# conftest.py
import pytest
import asyncio
from sovereign_sdk import TestEnvironment

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_env():
    """Setup complete test environment."""
    env = TestEnvironment()
    await env.setup()
    
    yield env
    
    await env.teardown()

@pytest.fixture
async def clean_database(test_env):
    """Ensure clean database for each test."""
    await test_env.reset_database()
    yield
    await test_env.reset_database()

@pytest.fixture
def mock_time():
    """Mock time for deterministic tests."""
    with patch('time.time') as mock:
        mock.return_value = 1234567890.0
        yield mock
```

### Test Data Builders

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AgentBuilder:
    """Builder for test agents."""
    did: str = "did:agentvault:test_agent"
    capabilities: List[str] = None
    stake: Optional[Decimal] = None
    initial_balance: Optional[Decimal] = None
    
    def with_capability(self, capability: str):
        if self.capabilities is None:
            self.capabilities = []
        self.capabilities.append(capability)
        return self
    
    def with_stake(self, amount: Decimal):
        self.stake = amount
        return self
    
    def with_balance(self, amount: Decimal):
        self.initial_balance = amount
        return self
    
    async def build(self):
        """Build and initialize the agent."""
        agent = Agent(
            did=self.did,
            capabilities=self.capabilities or []
        )
        
        if self.stake:
            await agent.set_stake(self.stake)
        
        if self.initial_balance:
            await agent.fund(self.initial_balance)
        
        return agent

# Usage
agent = await (AgentBuilder()
    .with_capability("data_processing")
    .with_capability("attestation")
    .with_stake(Decimal("10.0"))
    .with_balance(Decimal("100.0"))
    .build())
```

## Test Organization Best Practices

### Directory Structure

```
tests/
├── unit/
│   ├── test_agent_core.py
│   ├── test_capabilities.py
│   └── test_economic_features.py
├── integration/
│   ├── test_registry_integration.py
│   ├── test_teg_integration.py
│   └── test_federation.py
├── e2e/
│   ├── test_marketplace_flow.py
│   ├── test_attestation_flow.py
│   └── test_cross_registry.py
├── performance/
│   ├── test_load.py
│   └── test_benchmarks.py
├── security/
│   ├── test_auth.py
│   └── test_vulnerabilities.py
├── fixtures/
│   ├── agents.py
│   ├── registry.py
│   └── test_data.py
└── conftest.py
```

### Test Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (requires services)
    e2e: End-to-end tests (full stack required)
    slow: Slow tests (>5 seconds)
    security: Security-focused tests
    federation: Federation-specific tests
    benchmark: Performance benchmarks
    requires_spire: Requires SPIRE to be running

# Run specific test categories
# pytest -m unit  # Fast unit tests only
# pytest -m "not slow"  # Skip slow tests
# pytest -m "integration and not federation"  # Integration without federation
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run unit tests
        run: poetry run pytest -m unit --cov=./ --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose -f docker-compose.test.yml up -d
      
      - name: Run integration tests
        run: poetry run pytest -m integration
      
      - name: Collect logs on failure
        if: failure()
        run: docker-compose -f docker-compose.test.yml logs
```

## Testing Checklist

Before deploying your agent or service:

- [ ] Unit tests pass with >80% coverage
- [ ] Integration tests pass with real services
- [ ] Economic flows tested (payments, stakes, fees)
- [ ] Federation scenarios tested (if applicable)
- [ ] Performance meets requirements (TPS, latency)
- [ ] Security tests pass (auth, injection, validation)
- [ ] Error handling tested (network, timeout, invalid data)
- [ ] Documentation includes test examples
- [ ] CI/CD pipeline configured
- [ ] Load tests show stability under stress

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Testing distributed systems](https://www.somethingsimilar.com/2013/01/14/notes-on-distributed-systems-for-young-bloods/)
- [Property-based testing with Hypothesis](https://hypothesis.readthedocs.io/)
- [Load testing with Locust](https://docs.locust.io/)

---

*"Test in production? No. Test AS production. The Warrior Owl demands excellence in all environments."*
- The Testing Doctrine