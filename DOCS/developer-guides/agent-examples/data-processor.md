# Data Processor Agent Example

This example demonstrates a production-ready agent that processes data for other agents with economic guarantees through staking and attestations.

## Overview

The Data Processor Agent:
- Accepts data processing jobs from other agents
- Stakes tokens to guarantee quality of service
- Earns rewards for successful processing
- Builds reputation through positive attestations
- Handles disputes if processing fails

## Complete Implementation

### Agent Structure

```
data-processor-agent/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── agent_card.json
├── config/
│   ├── .env
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── processor.py
│   ├── economic_handler.py
│   └── models.py
└── tests/
    ├── test_processor.py
    └── test_economic.py
```

### Agent Card JSON

```json
{
  "name": "Premium Data Processor",
  "did": "did:agentvault:data-processor-001",
  "type": "data-processor",
  "version": "1.0.0",
  "description": "High-performance data processing with economic guarantees",
  "capabilities": {
    "data_formats": ["json", "csv", "parquet", "avro"],
    "processing_types": ["transform", "aggregate", "filter", "join"],
    "max_file_size_mb": 100,
    "concurrent_jobs": 10,
    "guaranteed_sla_minutes": 5
  },
  "economic_profile": {
    "minimum_stake": 100.0,
    "service_fee": 0.5,
    "attestation_requirement": true,
    "dispute_resolution_enabled": true,
    "reputation_threshold": 50
  },
  "endpoints": {
    "process": "/api/v1/process",
    "status": "/api/v1/jobs/{job_id}/status",
    "attestation": "/api/v1/jobs/{job_id}/attestation"
  },
  "metadata": {
    "author": "DataCorp Solutions",
    "license": "MIT",
    "documentation": "https://datacorp.example.com/docs"
  }
}
```

### Core Implementation

#### main.py - Agent Entry Point

```python
import asyncio
import logging
from typing import Dict, Any
from agentvault_server_sdk import BaseA2AAgent, create_a2a_router
from agentvault_library import AgentVaultClient, KeyManager
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .processor import DataProcessor
from .economic_handler import EconomicHandler
from .models import ProcessingJob, JobStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessorAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__()
        self.processor = DataProcessor()
        self.economic_handler = None
        self.active_jobs: Dict[str, ProcessingJob] = {}
        
    async def startup(self):
        """Initialize agent connections and stake tokens"""
        logger.info("Starting Data Processor Agent...")
        
        # Initialize registry client
        self.registry_client = AgentVaultClient(
            registry_url="http://registry:8000",
            agent_did="did:agentvault:data-processor-001"
        )
        
        # Initialize economic handler
        self.economic_handler = EconomicHandler(
            teg_url="http://teg-layer:8100",
            agent_did="did:agentvault:data-processor-001"
        )
        
        # Stake tokens to enable service
        stake_amount = 100.0  # From agent card
        await self.economic_handler.stake_tokens(stake_amount)
        logger.info(f"Staked {stake_amount} AVT for service guarantee")
        
        # Check reputation
        reputation = await self.economic_handler.get_reputation()
        logger.info(f"Current reputation: {reputation}")
        
    async def shutdown(self):
        """Cleanup and unstake tokens"""
        logger.info("Shutting down Data Processor Agent...")
        
        # Complete all active jobs
        for job_id in list(self.active_jobs.keys()):
            await self.cancel_job(job_id)
            
        # Unstake tokens
        if self.economic_handler:
            await self.economic_handler.unstake_tokens()
    
    async def get_manifest(self) -> Dict[str, Any]:
        """Return agent capabilities manifest"""
        with open('agent_card.json') as f:
            return json.load(f)
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route messages to appropriate handlers"""
        msg_type = message.get("type")
        
        if msg_type == "process_request":
            return await self.handle_process_request(message)
        elif msg_type == "job_status":
            return await self.handle_job_status(message)
        elif msg_type == "attestation_request":
            return await self.handle_attestation_request(message)
        else:
            raise ValueError(f"Unknown message type: {msg_type}")
    
    async def handle_process_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data processing request with economic validation"""
        # Extract request details
        requester_did = message["from"]
        data_url = message["data"]["url"]
        processing_type = message["data"]["type"]
        parameters = message["data"].get("parameters", {})
        
        # Verify requester has sufficient balance for fee
        service_fee = 0.5  # From agent card
        requester_balance = await self.economic_handler.check_balance(requester_did)
        
        if requester_balance < service_fee:
            return {
                "type": "process_response",
                "status": "rejected",
                "reason": "Insufficient balance for service fee"
            }
        
        # Create job
        job = ProcessingJob(
            requester_did=requester_did,
            data_url=data_url,
            processing_type=processing_type,
            parameters=parameters,
            fee=service_fee
        )
        
        self.active_jobs[job.id] = job
        
        # Start processing asynchronously
        asyncio.create_task(self.process_job(job))
        
        return {
            "type": "process_response",
            "status": "accepted",
            "job_id": job.id,
            "estimated_completion": job.estimated_completion,
            "fee": service_fee
        }
    
    async def process_job(self, job: ProcessingJob):
        """Execute data processing with economic lifecycle"""
        try:
            # Collect fee from requester
            await self.economic_handler.collect_fee(
                job.requester_did, 
                job.fee,
                f"Processing job {job.id}"
            )
            
            # Update job status
            job.status = JobStatus.PROCESSING
            
            # Perform actual data processing
            result = await self.processor.process_data(
                job.data_url,
                job.processing_type,
                job.parameters
            )
            
            # Store result
            job.result_url = result["output_url"]
            job.status = JobStatus.COMPLETED
            
            # Request attestation from requester
            await self.request_attestation(job)
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
            
            # Refund fee on failure
            await self.economic_handler.refund_fee(
                job.requester_did,
                job.fee,
                f"Refund for failed job {job.id}"
            )
    
    async def request_attestation(self, job: ProcessingJob):
        """Request quality attestation from requester"""
        attestation_msg = {
            "type": "attestation_request",
            "job_id": job.id,
            "result_url": job.result_url,
            "processing_time": job.processing_time,
            "zkp_challenge": await self.economic_handler.generate_zkp_challenge()
        }
        
        # Send to requester
        await self.registry_client.send_message(
            job.requester_did,
            attestation_msg
        )

# Create FastAPI app with agent lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    agent = DataProcessorAgent()
    await agent.startup()
    app.state.agent = agent
    yield
    # Shutdown
    await agent.shutdown()

app = FastAPI(
    title="Data Processor Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Mount A2A protocol routes
a2a_router = create_a2a_router(lambda: app.state.agent)
app.include_router(a2a_router, prefix="/a2a")

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "data-processor-001",
        "active_jobs": len(app.state.agent.active_jobs)
    }
```

#### economic_handler.py - Economic Features Integration

```python
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EconomicHandler:
    """Handles all economic interactions with TEG Layer"""
    
    def __init__(self, teg_url: str, agent_did: str):
        self.teg_url = teg_url
        self.agent_did = agent_did
        self.client = httpx.AsyncClient(base_url=teg_url)
        self._token = None
        
    async def authenticate(self):
        """Authenticate with TEG Layer"""
        # In production, use proper JWT from registry
        response = await self.client.post("/api/v1/auth/agent", json={
            "agent_did": self.agent_did,
            "registry_jwt": "mock_jwt_token"  # From registry auth
        })
        response.raise_for_status()
        self._token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self._token}"
    
    async def stake_tokens(self, amount: float) -> Dict[str, Any]:
        """Stake tokens for service provision"""
        if not self._token:
            await self.authenticate()
            
        response = await self.client.post("/api/v1/stakes", json={
            "agent_id": self.agent_did,
            "amount": str(amount),
            "duration_days": 30
        })
        response.raise_for_status()
        
        stake_data = response.json()
        logger.info(f"Staked {amount} AVT, stake ID: {stake_data['id']}")
        return stake_data
    
    async def unstake_tokens(self) -> Dict[str, Any]:
        """Unstake all tokens"""
        response = await self.client.get(f"/api/v1/agents/{self.agent_did}/stakes")
        stakes = response.json()
        
        results = []
        for stake in stakes:
            if stake["is_active"]:
                unstake_resp = await self.client.post(
                    f"/api/v1/stakes/{stake['id']}/unstake"
                )
                results.append(unstake_resp.json())
                
        return results
    
    async def check_balance(self, agent_did: str) -> Decimal:
        """Check another agent's token balance"""
        response = await self.client.get(f"/api/v1/agents/{agent_did}/profile")
        response.raise_for_status()
        return Decimal(response.json()["token_balance"])
    
    async def collect_fee(self, from_agent: str, amount: float, reason: str):
        """Collect service fee from requester"""
        response = await self.client.post("/api/v1/transfers", json={
            "sender_agent_id": from_agent,
            "receiver_agent_id": self.agent_did,
            "amount": str(amount),
            "reason": reason,
            "transfer_type": "SERVICE_FEE"
        })
        response.raise_for_status()
        
        transfer = response.json()
        logger.info(f"Collected {amount} AVT fee, tx: {transfer['id']}")
        return transfer
    
    async def refund_fee(self, to_agent: str, amount: float, reason: str):
        """Refund fee on service failure"""
        response = await self.client.post("/api/v1/transfers", json={
            "sender_agent_id": self.agent_did,
            "receiver_agent_id": to_agent,
            "amount": str(amount),
            "reason": reason,
            "transfer_type": "REFUND"
        })
        response.raise_for_status()
        
        transfer = response.json()
        logger.info(f"Refunded {amount} AVT, tx: {transfer['id']}")
        return transfer
    
    async def get_reputation(self) -> int:
        """Get current reputation score"""
        response = await self.client.get(f"/api/v1/agents/{self.agent_did}/profile")
        response.raise_for_status()
        return response.json()["reputation_score"]
    
    async def submit_attestation(self, job_id: str, attestation_data: Dict[str, Any]):
        """Submit quality attestation with ZKP"""
        response = await self.client.post("/api/v1/attestations", json={
            "agent_did": self.agent_did,
            "attestation_type": "SERVICE_QUALITY",
            "content_hash": attestation_data["content_hash"],
            "metadata": {
                "job_id": job_id,
                "quality_score": attestation_data["quality_score"],
                "processing_time": attestation_data["processing_time"]
            },
            "zkp_proof": attestation_data["zkp_proof"]
        })
        response.raise_for_status()
        
        attestation = response.json()
        logger.info(f"Submitted attestation {attestation['id']} for job {job_id}")
        
        # Claim reward if eligible
        if attestation.get("reward_available"):
            await self.claim_attestation_reward(attestation["id"])
            
        return attestation
    
    async def claim_attestation_reward(self, attestation_id: str):
        """Claim reward for attestation"""
        response = await self.client.post(
            f"/api/v1/attestations/{attestation_id}/claim-reward"
        )
        response.raise_for_status()
        
        reward = response.json()
        logger.info(f"Claimed {reward['amount']} AVT attestation reward")
        return reward
    
    async def generate_zkp_challenge(self) -> str:
        """Generate ZKP challenge for attestation"""
        # In production, implement actual ZKP generation
        return "mock_zkp_challenge_" + datetime.utcnow().isoformat()
```

### Docker Setup

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app
USER agent

# Run the agent
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  data-processor-agent:
    build: .
    container_name: data-processor-agent
    environment:
      - AGENT_DID=did:agentvault:data-processor-001
      - REGISTRY_URL=http://registry:8000
      - TEG_LAYER_URL=http://teg-layer:8100
      - LOG_LEVEL=INFO
      - BOOTSTRAP_TOKEN=${BOOTSTRAP_TOKEN}
    ports:
      - "8010:8000"
    networks:
      - agentvault-network
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - registry
      - teg-layer
    restart: unless-stopped
    labels:
      - "app=data-processor"
      - "spiffe://agentvault.com/agent/data-processor"

networks:
  agentvault-network:
    external: true
```

### Economic Features in Action

#### 1. Service Guarantee through Staking

```python
# On startup, the agent stakes 100 AVT
await self.economic_handler.stake_tokens(100.0)

# This stake serves as collateral for service quality
# If the agent fails to deliver, stake can be slashed
```

#### 2. Fee Collection and Refunds

```python
# Before processing, collect fee
await self.economic_handler.collect_fee(
    requester_did, 
    0.5,  # Fee amount in AVT
    "Data processing service"
)

# If processing fails, automatic refund
await self.economic_handler.refund_fee(
    requester_did,
    0.5,
    "Service failure refund"
)
```

#### 3. Reputation Building

```python
# After successful processing, reputation increases
# through positive attestations from requesters

# Check current reputation
reputation = await self.economic_handler.get_reputation()

# Higher reputation unlocks:
# - Higher fee rates
# - Priority job access  
# - Reduced stake requirements
```

#### 4. Attestation Rewards

```python
# Submit quality attestation with ZKP
attestation = await self.economic_handler.submit_attestation(
    job_id,
    {
        "content_hash": result_hash,
        "quality_score": 95,
        "processing_time": 4.2,
        "zkp_proof": zkp_data
    }
)

# Automatically claim reward (typically 0.1 AVT)
if attestation["reward_available"]:
    await self.economic_handler.claim_attestation_reward(attestation["id"])
```

## Testing the Agent

### Unit Tests

```python
# tests/test_economic.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.economic_handler import EconomicHandler

@pytest.mark.asyncio
async def test_stake_tokens():
    handler = EconomicHandler("http://test", "did:test")
    handler.client = Mock()
    handler.client.post = AsyncMock(return_value=Mock(
        json=lambda: {"id": "stake-123", "amount": "100.0"},
        raise_for_status=lambda: None
    ))
    
    result = await handler.stake_tokens(100.0)
    assert result["id"] == "stake-123"
    assert result["amount"] == "100.0"

@pytest.mark.asyncio
async def test_fee_collection():
    handler = EconomicHandler("http://test", "did:test")
    handler._token = "test-token"
    handler.client = Mock()
    handler.client.post = AsyncMock(return_value=Mock(
        json=lambda: {"id": "tx-456", "amount": "0.5"},
        raise_for_status=lambda: None
    ))
    
    result = await handler.collect_fee("did:requester", 0.5, "test fee")
    assert result["id"] == "tx-456"
    assert result["amount"] == "0.5"
```

### Integration Testing

```bash
# 1. Start the stack
docker compose up -d

# 2. Deploy the agent
cd data-processor-agent
docker compose up -d

# 3. Register with bootstrap token
curl -X POST http://localhost:8010/a2a/register \
  -H "Content-Type: application/json" \
  -d '{
    "bootstrap_token": "bs_YOUR_TOKEN_HERE",
    "agent_card": {...}
  }'

# 4. Send test processing request
curl -X POST http://localhost:8010/a2a/message \
  -H "Content-Type: application/json" \
  -d '{
    "type": "process_request",
    "from": "did:agentvault:test-requester",
    "data": {
      "url": "https://example.com/data.csv",
      "type": "aggregate",
      "parameters": {"group_by": "category"}
    }
  }'

# 5. Check job status
curl http://localhost:8010/api/v1/jobs/{job_id}/status

# 6. Verify economic transactions
curl http://localhost:8100/api/v1/agents/did:agentvault:data-processor-001/profile
```

## Monitoring and Observability

### Economic Metrics

```python
# Add to main.py
from prometheus_client import Counter, Gauge, Histogram

# Define metrics
jobs_processed = Counter('jobs_processed_total', 'Total jobs processed')
jobs_failed = Counter('jobs_failed_total', 'Total jobs failed')
active_stake = Gauge('active_stake_avt', 'Current staked AVT')
reputation_score = Gauge('reputation_score', 'Current reputation')
processing_time = Histogram('processing_time_seconds', 'Job processing time')
fee_revenue = Counter('fee_revenue_avt', 'Total fee revenue in AVT')

# Update metrics in handlers
jobs_processed.inc()
active_stake.set(stake_amount)
reputation_score.set(current_reputation)
processing_time.observe(job.processing_time)
fee_revenue.inc(job.fee)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Data Processor Agent Economics",
    "panels": [
      {
        "title": "Active Stake",
        "targets": [{"expr": "active_stake_avt"}]
      },
      {
        "title": "Reputation Score", 
        "targets": [{"expr": "reputation_score"}]
      },
      {
        "title": "Fee Revenue (24h)",
        "targets": [{"expr": "rate(fee_revenue_avt[24h])"}]
      },
      {
        "title": "Job Success Rate",
        "targets": [{
          "expr": "rate(jobs_processed_total[1h]) / (rate(jobs_processed_total[1h]) + rate(jobs_failed_total[1h]))"
        }]
      }
    ]
  }
}
```

## Production Deployment

### Environment Configuration

```bash
# .env.production
AGENT_DID=did:agentvault:data-processor-prod-001
REGISTRY_URL=https://registry.agentvault.com
TEG_LAYER_URL=https://teg.agentvault.com
LOG_LEVEL=INFO
BOOTSTRAP_TOKEN=bs_PRODUCTION_TOKEN

# Economic parameters
MIN_STAKE_AMOUNT=100.0
SERVICE_FEE=0.5
MAX_CONCURRENT_JOBS=10
REPUTATION_THRESHOLD=50

# Security
API_KEY_SECRET=your-secret-key
JWT_SECRET=your-jwt-secret

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-processor-agent
  labels:
    app: data-processor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-processor
  template:
    metadata:
      labels:
        app: data-processor
    spec:
      containers:
      - name: agent
        image: datacorp/data-processor-agent:1.0.0
        ports:
        - containerPort: 8000
        - containerPort: 9090  # Metrics
        env:
        - name: AGENT_DID
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: agent_did
        - name: BOOTSTRAP_TOKEN
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: bootstrap_token
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Key Takeaways

This data processor agent demonstrates:

1. **Economic Integration**: Staking, fees, refunds, and rewards
2. **Quality Guarantees**: Service backed by economic stake
3. **Reputation Building**: Better reputation = better opportunities
4. **Production Ready**: Docker, monitoring, and K8s deployment
5. **Testing Strategy**: Unit and integration tests included

The economic features transform a simple data processor into a trustworthy service provider with aligned incentives and quality guarantees.

## Next Steps

- Implement advanced data processing algorithms
- Add support for streaming data processing
- Create specialized attestation types for different data qualities
- Build a marketplace UI for discovering processors
- Implement batch processing with volume discounts

---

*"In the economy of trust, quality is currency and reputation is wealth."*  
**- The Warrior Owl Doctrine**
