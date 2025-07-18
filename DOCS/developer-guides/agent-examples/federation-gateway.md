# Federation Gateway Agent Example

This example demonstrates a federation gateway agent that enables seamless communication and service discovery across multiple registries in The Protocol network.

## Overview

The Federation Gateway Agent:
- Bridges communication between agents in different registries
- Maintains synchronized agent directories across federations
- Routes messages between registries securely
- Handles identity verification across trust boundaries
- Manages cross-registry token transfers
- Provides unified service discovery

## Complete Implementation

### Agent Structure

```
federation-gateway/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── agent_card.json
├── config/
│   ├── .env
│   ├── federation_config.yaml
│   └── registry_endpoints.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── federation_bridge.py
│   ├── registry_sync.py
│   ├── message_router.py
│   ├── identity_verifier.py
│   └── models.py
├── monitoring/
│   ├── prometheus_config.yml
│   └── alerts.yml
└── tests/
    ├── test_federation.py
    ├── test_routing.py
    └── test_identity.py
```

### Agent Card JSON

```json
{
  "name": "Federation Gateway Alpha",
  "did": "did:agentvault:federation-gateway-alpha",
  "type": "federation-gateway",
  "version": "1.0.0",
  "description": "Cross-registry federation gateway enabling seamless agent communication across trust boundaries",
  "capabilities": {
    "supported_registries": [
      "http://registry-a:8000",
      "http://registry-b:8001"
    ],
    "federation_protocol_version": "1.0",
    "message_routing": true,
    "agent_discovery": true,
    "identity_bridging": true,
    "token_bridge": true,
    "max_message_size_kb": 1024,
    "rate_limits": {
      "messages_per_minute": 1000,
      "sync_interval_seconds": 30
    }
  },
  "economic_profile": {
    "minimum_stake": 500.0,
    "routing_fee": 0.01,
    "bridge_fee": 0.1,
    "requires_attestation": true
  },
  "security": {
    "tls_required": true,
    "mutual_auth": true,
    "identity_verification": "SPIFFE",
    "encryption": "AES-256-GCM"
  },
  "endpoints": {
    "route_message": "/api/v1/route",
    "discover_agents": "/api/v1/discover",
    "verify_identity": "/api/v1/verify",
    "bridge_tokens": "/api/v1/bridge",
    "federation_status": "/api/v1/status"
  },
  "metadata": {
    "operator": "Federation Consortium",
    "sla": "99.9% uptime",
    "compliance": ["GDPR", "SOC2"]
  }
}
```

### Core Implementation

#### main.py - Federation Gateway Entry Point

```python
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import yaml
from agentvault_server_sdk import BaseA2AAgent, create_a2a_router
from agentvault_library import AgentVaultClient, KeyManager
from fastapi import FastAPI, HTTPException, WebSocket
from contextlib import asynccontextmanager

from .federation_bridge import FederationBridge
from .registry_sync import RegistrySync
from .message_router import MessageRouter
from .identity_verifier import IdentityVerifier
from .models import FederatedMessage, RegistryInfo, AgentRoute

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FederationGatewayAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__()
        self.federation_bridge = None
        self.registry_sync = None
        self.message_router = None
        self.identity_verifier = None
        self.registry_clients: Dict[str, AgentVaultClient] = {}
        self.agent_routes: Dict[str, AgentRoute] = {}
        
    async def startup(self):
        """Initialize federation gateway with multi-registry connections"""
        logger.info("Starting Federation Gateway Agent...")
        
        # Load federation configuration
        with open('config/federation_config.yaml') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize identity verifier (SPIFFE/SPIRE)
        self.identity_verifier = IdentityVerifier(
            trust_domain=self.config['trust_domain'],
            spire_agent_socket=self.config['spire_agent_socket']
        )
        
        # Initialize registry connections
        await self._initialize_registries()
        
        # Initialize components
        self.federation_bridge = FederationBridge(
            gateway_did="did:agentvault:federation-gateway-alpha",
            registries=self.registry_clients
        )
        
        self.registry_sync = RegistrySync(
            registries=self.registry_clients,
            sync_interval=self.config['sync_interval']
        )
        
        self.message_router = MessageRouter(
            agent_routes=self.agent_routes,
            identity_verifier=self.identity_verifier
        )
        
        # Stake tokens in each registry
        for registry_url, client in self.registry_clients.items():
            await self._stake_in_registry(client, registry_url)
        
        # Start background tasks
        asyncio.create_task(self.registry_sync.start_sync())
        asyncio.create_task(self._update_routing_table())
        
    async def _initialize_registries(self):
        """Initialize connections to all federated registries"""
        with open('config/registry_endpoints.json') as f:
            registry_configs = json.load(f)
        
        for registry in registry_configs['registries']:
            try:
                # Use provided API keys for each registry
                key_manager = KeyManager()
                key_manager.add_key(
                    registry['url'],
                    registry['api_key'],
                    source='config'
                )
                
                client = AgentVaultClient(
                    registry_url=registry['url'],
                    agent_did="did:agentvault:federation-gateway-alpha",
                    key_manager=key_manager
                )
                
                # Authenticate with registry
                await client.authenticate(
                    email=registry['email'],
                    password=registry['password']
                )
                
                self.registry_clients[registry['url']] = client
                logger.info(f"Connected to registry: {registry['url']}")
                
            except Exception as e:
                logger.error(f"Failed to connect to {registry['url']}: {e}")
    
    async def _stake_in_registry(self, client: AgentVaultClient, registry_url: str):
        """Stake tokens in a registry for gateway operation"""
        try:
            # Get TEG client for this registry
            teg_url = registry_url.replace(':8000', ':8100').replace(':8001', ':8100')
            
            # Stake tokens
            stake_response = await client.call_method(
                "POST",
                f"{teg_url}/api/v1/stakes",
                json={
                    "agent_id": "did:agentvault:federation-gateway-alpha",
                    "amount": "500.0",
                    "duration_days": 90
                }
            )
            
            logger.info(f"Staked 500 AVT in registry {registry_url}")
            
        except Exception as e:
            logger.error(f"Failed to stake in {registry_url}: {e}")
    
    async def get_manifest(self) -> Dict[str, Any]:
        """Return gateway capabilities"""
        with open('agent_card.json') as f:
            return json.load(f)
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route federated messages"""
        msg_type = message.get("type")
        
        if msg_type == "federated_message":
            return await self.handle_federated_message(message)
        elif msg_type == "discover_request":
            return await self.handle_discover_request(message)
        elif msg_type == "bridge_tokens":
            return await self.handle_token_bridge(message)
        else:
            raise ValueError(f"Unknown message type: {msg_type}")
    
    async def handle_federated_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route message across registries"""
        # Extract routing information
        source_did = message["from"]
        target_did = message["to"]
        payload = message["payload"]
        
        # Verify source identity
        if not await self.identity_verifier.verify_agent(source_did):
            return {
                "type": "routing_response",
                "status": "failed",
                "reason": "Identity verification failed"
            }
        
        # Find target registry
        target_route = self.agent_routes.get(target_did)
        if not target_route:
            # Try to discover agent
            target_route = await self._discover_agent_route(target_did)
            if not target_route:
                return {
                    "type": "routing_response",
                    "status": "failed",
                    "reason": "Target agent not found in federation"
                }
        
        # Route message
        try:
            result = await self.message_router.route_message(
                source_registry=message.get("source_registry"),
                target_registry=target_route.registry_url,
                message=FederatedMessage(
                    id=str(uuid4()),
                    source_did=source_did,
                    target_did=target_did,
                    payload=payload,
                    timestamp=datetime.utcnow()
                )
            )
            
            # Collect routing fee
            await self._collect_routing_fee(source_did)
            
            return {
                "type": "routing_response",
                "status": "success",
                "message_id": result.id,
                "target_registry": target_route.registry_url
            }
            
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return {
                "type": "routing_response",
                "status": "failed",
                "reason": str(e)
            }
    
    async def _update_routing_table(self):
        """Periodically update agent routing table"""
        while True:
            try:
                all_agents = {}
                
                # Collect agents from all registries
                for registry_url, client in self.registry_clients.items():
                    agents = await client.call_method("GET", "/api/v1/agents")
                    
                    for agent in agents:
                        all_agents[agent['did']] = AgentRoute(
                            agent_did=agent['did'],
                            registry_url=registry_url,
                            last_seen=datetime.utcnow(),
                            capabilities=agent.get('capabilities', {})
                        )
                
                # Update routing table
                self.agent_routes = all_agents
                logger.info(f"Updated routing table: {len(all_agents)} agents")
                
            except Exception as e:
                logger.error(f"Failed to update routing table: {e}")
            
            await asyncio.sleep(30)  # Update every 30 seconds

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = FederationGatewayAgent()
    await agent.startup()
    app.state.agent = agent
    yield
    await agent.shutdown()

app = FastAPI(
    title="Federation Gateway Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Mount A2A routes
a2a_router = create_a2a_router(lambda: app.state.agent)
app.include_router(a2a_router, prefix="/a2a")

# Federation-specific endpoints
@app.get("/api/v1/status")
async def federation_status():
    """Get federation gateway status"""
    agent = app.state.agent
    return {
        "status": "operational",
        "connected_registries": list(agent.registry_clients.keys()),
        "total_agents": len(agent.agent_routes),
        "uptime": (datetime.utcnow() - agent.startup_time).total_seconds()
    }

@app.get("/api/v1/discover")
async def discover_agents(
    service_type: Optional[str] = None,
    capabilities: Optional[List[str]] = None
):
    """Discover agents across all federated registries"""
    agent = app.state.agent
    results = []
    
    for agent_did, route in agent.agent_routes.items():
        # Filter by criteria
        if service_type and route.capabilities.get("type") != service_type:
            continue
            
        if capabilities:
            agent_caps = set(route.capabilities.get("features", []))
            if not all(cap in agent_caps for cap in capabilities):
                continue
        
        results.append({
            "did": agent_did,
            "registry": route.registry_url,
            "capabilities": route.capabilities,
            "last_seen": route.last_seen.isoformat()
        })
    
    return {
        "results": results,
        "count": len(results),
        "registries_searched": len(agent.registry_clients)
    }

@app.websocket("/ws/federation-stream")
async def federation_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time federation events"""
    await websocket.accept()
    agent = app.state.agent
    
    try:
        # Subscribe to federation events
        async for event in agent.federation_bridge.event_stream():
            await websocket.send_json({
                "type": "federation_event",
                "event": event.type,
                "data": event.data,
                "timestamp": event.timestamp.isoformat()
            })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

#### message_router.py - Cross-Registry Message Routing

```python
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from cryptography.fernet import Fernet

from .models import FederatedMessage, AgentRoute
from .identity_verifier import IdentityVerifier

logger = logging.getLogger(__name__)

class MessageRouter:
    """Routes messages between agents across registry boundaries"""
    
    def __init__(self, agent_routes: Dict[str, AgentRoute], identity_verifier: IdentityVerifier):
        self.agent_routes = agent_routes
        self.identity_verifier = identity_verifier
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
    async def route_message(
        self,
        source_registry: str,
        target_registry: str,
        message: FederatedMessage
    ) -> FederatedMessage:
        """Route message from source to target registry"""
        
        # Verify cross-registry permissions
        if not await self._verify_federation_permissions(source_registry, target_registry):
            raise PermissionError("Cross-registry communication not allowed")
        
        # Encrypt message payload for transit
        encrypted_payload = self._encrypt_payload(message.payload)
        
        # Add routing metadata
        routed_message = FederatedMessage(
            id=message.id,
            source_did=message.source_did,
            target_did=message.target_did,
            payload=encrypted_payload,
            timestamp=message.timestamp,
            routing_metadata={
                "source_registry": source_registry,
                "target_registry": target_registry,
                "gateway": "did:agentvault:federation-gateway-alpha",
                "encrypted": True
            }
        )
        
        # Forward to target registry
        target_client = self.registry_clients.get(target_registry)
        if not target_client:
            raise ValueError(f"No client for registry: {target_registry}")
        
        # Send through A2A protocol
        response = await target_client.send_message(
            message.target_did,
            {
                "type": "federated_delivery",
                "gateway_message": routed_message.dict(),
                "source_registry": source_registry
            }
        )
        
        logger.info(f"Routed message {message.id} from {source_registry} to {target_registry}")
        
        return routed_message
    
    def _encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """Encrypt message payload for secure transit"""
        import json
        payload_bytes = json.dumps(payload).encode()
        encrypted = self.cipher.encrypt(payload_bytes)
        return encrypted.decode('latin-1')  # Convert bytes to string
    
    def _decrypt_payload(self, encrypted_payload: str) -> Dict[str, Any]:
        """Decrypt message payload"""
        import json
        encrypted_bytes = encrypted_payload.encode('latin-1')
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())
    
    async def _verify_federation_permissions(
        self,
        source_registry: str,
        target_registry: str
    ) -> bool:
        """Verify federation agreement between registries"""
        # In production, check federation agreements database
        # For now, allow all configured registry pairs
        return (source_registry in self.registry_clients and 
                target_registry in self.registry_clients)
```

#### federation_bridge.py - Token Bridge Implementation

```python
import logging
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
import asyncio

from .models import TokenBridge, BridgeTransaction

logger = logging.getLogger(__name__)

class FederationBridge:
    """Handles cross-registry token transfers and economic bridging"""
    
    def __init__(self, gateway_did: str, registries: Dict[str, Any]):
        self.gateway_did = gateway_did
        self.registries = registries
        self.bridge_pools: Dict[str, Decimal] = {}
        self.pending_bridges: Dict[str, BridgeTransaction] = {}
        
    async def initialize_bridge_pools(self):
        """Initialize liquidity pools for each registry pair"""
        # Create liquidity pools for token bridging
        for registry_a in self.registries:
            for registry_b in self.registries:
                if registry_a != registry_b:
                    pool_key = f"{registry_a}->{registry_b}"
                    # Initial liquidity provided by gateway
                    self.bridge_pools[pool_key] = Decimal("10000.0")
                    
                    logger.info(f"Initialized bridge pool {pool_key} with 10000 AVT")
    
    async def bridge_tokens(
        self,
        from_agent: str,
        to_agent: str,
        amount: Decimal,
        from_registry: str,
        to_registry: str
    ) -> BridgeTransaction:
        """Bridge tokens between registries"""
        
        # Verify agents exist in their respective registries
        if not await self._verify_agent_in_registry(from_agent, from_registry):
            raise ValueError(f"Agent {from_agent} not found in {from_registry}")
            
        if not await self._verify_agent_in_registry(to_agent, to_registry):
            raise ValueError(f"Agent {to_agent} not found in {to_registry}")
        
        # Check bridge liquidity
        pool_key = f"{from_registry}->{to_registry}"
        if self.bridge_pools.get(pool_key, Decimal("0")) < amount:
            raise ValueError("Insufficient bridge liquidity")
        
        # Calculate bridge fee (0.1%)
        bridge_fee = amount * Decimal("0.001")
        net_amount = amount - bridge_fee
        
        # Create bridge transaction
        bridge_tx = BridgeTransaction(
            id=str(uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            amount=amount,
            fee=bridge_fee,
            from_registry=from_registry,
            to_registry=to_registry,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.pending_bridges[bridge_tx.id] = bridge_tx
        
        try:
            # Step 1: Lock tokens in source registry
            await self._lock_tokens_in_registry(
                from_agent,
                amount,
                from_registry,
                bridge_tx.id
            )
            
            # Step 2: Mint equivalent tokens in target registry
            await self._mint_tokens_in_registry(
                to_agent,
                net_amount,
                to_registry,
                bridge_tx.id
            )
            
            # Step 3: Update bridge pools
            self.bridge_pools[pool_key] -= net_amount
            reverse_pool_key = f"{to_registry}->{from_registry}"
            self.bridge_pools[reverse_pool_key] = self.bridge_pools.get(
                reverse_pool_key, Decimal("0")
            ) + net_amount
            
            bridge_tx.status = "completed"
            bridge_tx.completed_at = datetime.utcnow()
            
            logger.info(f"Completed token bridge {bridge_tx.id}: {amount} AVT from {from_registry} to {to_registry}")
            
            return bridge_tx
            
        except Exception as e:
            # Rollback on failure
            bridge_tx.status = "failed"
            bridge_tx.error = str(e)
            
            # Attempt to unlock tokens if locked
            if bridge_tx.status != "pending":
                await self._unlock_tokens_in_registry(
                    from_agent,
                    amount,
                    from_registry,
                    bridge_tx.id
                )
            
            raise e
    
    async def _lock_tokens_in_registry(
        self,
        agent_did: str,
        amount: Decimal,
        registry_url: str,
        bridge_tx_id: str
    ):
        """Lock tokens in source registry"""
        client = self.registries[registry_url]
        teg_url = registry_url.replace(':8000', ':8100').replace(':8001', ':8100')
        
        # Transfer tokens to bridge escrow account
        response = await client.call_method(
            "POST",
            f"{teg_url}/api/v1/transfers",
            json={
                "sender_agent_id": agent_did,
                "receiver_agent_id": self.gateway_did,
                "amount": str(amount),
                "reason": f"Bridge lock for tx {bridge_tx_id}",
                "transfer_type": "BRIDGE_LOCK"
            }
        )
        
        if response.get("status") != "success":
            raise Exception(f"Failed to lock tokens: {response}")
    
    async def _mint_tokens_in_registry(
        self,
        agent_did: str,
        amount: Decimal,
        registry_url: str,
        bridge_tx_id: str
    ):
        """Mint bridged tokens in target registry"""
        client = self.registries[registry_url]
        teg_url = registry_url.replace(':8000', ':8100').replace(':8001', ':8100')
        
        # Gateway mints tokens to recipient
        # In production, this would involve more complex verification
        response = await client.call_method(
            "POST",
            f"{teg_url}/api/v1/transfers",
            json={
                "sender_agent_id": self.gateway_did,
                "receiver_agent_id": agent_did,
                "amount": str(amount),
                "reason": f"Bridge mint for tx {bridge_tx_id}",
                "transfer_type": "BRIDGE_MINT"
            }
        )
        
        if response.get("status") != "success":
            raise Exception(f"Failed to mint tokens: {response}")
```

### Docker Configuration

#### docker-compose.yml

```yaml
version: '3.8'

services:
  federation-gateway:
    build: .
    container_name: federation-gateway-alpha
    environment:
      - AGENT_DID=did:agentvault:federation-gateway-alpha
      - LOG_LEVEL=INFO
      - SPIFFE_ENDPOINT_SOCKET=/tmp/spire-agent/public/api.sock
      # Registry A credentials
      - REGISTRY_A_URL=http://registry-a:8000
      - REGISTRY_A_EMAIL=commander@agentvault.com
      - REGISTRY_A_PASSWORD=SovereignKey!2025
      - REGISTRY_A_API_KEY=avreg_eJx7JyZWspw29zO8A_EcsMPsA6_lrL7O6eFwzGaIG6I
      # Registry B credentials  
      - REGISTRY_B_URL=http://registry-b:8001
      - REGISTRY_B_EMAIL=commander@agentvault.com
      - REGISTRY_B_PASSWORD=SovereignKey!2025
      - REGISTRY_B_API_KEY=avreg_d2yxb_VO1L9IieWEr4SF6oogMrOdNu2P7T3K5dKOcHk
    ports:
      - "8030:8000"
      - "9090:9090"  # Prometheus metrics
    networks:
      - agentvault-network
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - /tmp/spire-agent:/tmp/spire-agent:ro
    depends_on:
      - registry-a
      - registry-b
      - spire-agent
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus_config.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9091:9090"
    networks:
      - agentvault-network

volumes:
  prometheus-data:

networks:
  agentvault-network:
    external: true
```

#### config/federation_config.yaml

```yaml
# Federation Gateway Configuration
federation:
  name: "Alpha Federation"
  version: "1.0"
  
trust_domain: "agentvault.com"
spire_agent_socket: "/tmp/spire-agent/public/api.sock"

sync_interval: 30  # seconds

routing:
  max_message_size_kb: 1024
  rate_limits:
    messages_per_minute: 1000
    per_agent_limit: 100
  
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_hours: 24

bridge:
  enabled: true
  fee_percent: 0.1
  min_amount: 1.0
  max_amount: 10000.0
  
  liquidity_pools:
    initial_liquidity: 10000.0
    rebalance_threshold: 0.2

monitoring:
  metrics_port: 9090
  health_check_interval: 10
  
  alerts:
    - name: "high_error_rate"
      threshold: 0.05
      window: "5m"
    - name: "low_liquidity"
      threshold: 1000.0
      action: "rebalance"

security:
  require_mutual_tls: true
  allowed_origins:
    - "https://registry-a.agentvault.com"
    - "https://registry-b.agentvault.com"
  
  rate_limiting:
    enabled: true
    window_seconds: 60
    max_requests: 1000
```

### Testing Federation Features

#### Integration Tests

```python
# tests/test_federation.py
import pytest
import asyncio
from decimal import Decimal

@pytest.mark.asyncio
async def test_cross_registry_message_routing():
    """Test routing messages between agents in different registries"""
    gateway = FederationGatewayAgent()
    await gateway.startup()
    
    # Create test message from Registry A agent to Registry B agent
    message = {
        "type": "federated_message",
        "from": "did:agentvault:agent-a",
        "to": "did:agentvault:agent-b",
        "source_registry": "http://registry-a:8000",
        "payload": {
            "type": "hello",
            "content": "Cross-registry greeting!"
        }
    }
    
    # Route the message
    response = await gateway.handle_federated_message(message)
    
    assert response["status"] == "success"
    assert response["target_registry"] == "http://registry-b:8001"
    assert "message_id" in response

@pytest.mark.asyncio
async def test_token_bridge():
    """Test cross-registry token transfer"""
    gateway = FederationGatewayAgent()
    await gateway.startup()
    
    # Bridge tokens from Registry A to Registry B
    bridge_request = {
        "type": "bridge_tokens",
        "from": "did:agentvault:alice",
        "to": "did:agentvault:bob",
        "amount": "100.0",
        "from_registry": "http://registry-a:8000",
        "to_registry": "http://registry-b:8001"
    }
    
    response = await gateway.handle_token_bridge(bridge_request)
    
    assert response["status"] == "success"
    assert Decimal(response["net_amount"]) == Decimal("99.9")  # After 0.1% fee
    assert response["bridge_tx_id"] is not None

@pytest.mark.asyncio
async def test_agent_discovery():
    """Test discovering agents across all registries"""
    gateway = FederationGatewayAgent()
    await gateway.startup()
    
    # Wait for initial sync
    await asyncio.sleep(5)
    
    # Search for data processing agents
    from httpx import AsyncClient
    async with AsyncClient() as client:
        response = await client.get(
            "http://localhost:8030/api/v1/discover",
            params={"service_type": "data-processor"}
        )
    
    data = response.json()
    assert data["count"] > 0
    assert len(data["registries_searched"]) == 2
    
    # Verify agents from both registries are found
    registries = set(agent["registry"] for agent in data["results"])
    assert "http://registry-a:8000" in registries
    assert "http://registry-b:8001" in registries
```

#### Load Testing Federation

```python
# tests/load_test_federation.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import random

async def simulate_federated_traffic(duration_seconds: int):
    """Simulate cross-registry traffic patterns"""
    start_time = time.time()
    message_count = 0
    error_count = 0
    
    # Define test agents in different registries
    registry_a_agents = [f"did:agentvault:a-agent-{i}" for i in range(10)]
    registry_b_agents = [f"did:agentvault:b-agent-{i}" for i in range(10)]
    
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration_seconds:
            # Random cross-registry message
            source = random.choice(registry_a_agents)
            target = random.choice(registry_b_agents)
            
            message = {
                "type": "federated_message",
                "from": source,
                "to": target,
                "source_registry": "http://registry-a:8000",
                "payload": {
                    "type": "test_message",
                    "timestamp": time.time(),
                    "data": "Load test payload"
                }
            }
            
            try:
                async with session.post(
                    "http://localhost:8030/a2a/message",
                    json=message
                ) as response:
                    if response.status == 200:
                        message_count += 1
                    else:
                        error_count += 1
            except Exception as e:
                error_count += 1
            
            # Throttle to avoid overwhelming
            await asyncio.sleep(0.1)
    
    return {
        "duration": duration_seconds,
        "messages_sent": message_count,
        "errors": error_count,
        "messages_per_second": message_count / duration_seconds
    }

# Run load test
results = asyncio.run(simulate_federated_traffic(300))  # 5 minutes
print(f"Load test results: {results}")
```

### Monitoring and Observability

#### Prometheus Metrics

```python
# Add to main.py
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Define federation metrics
messages_routed = Counter(
    'federation_messages_routed_total',
    'Total messages routed between registries',
    ['source_registry', 'target_registry']
)

routing_latency = Histogram(
    'federation_routing_latency_seconds',
    'Message routing latency',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

bridge_transactions = Counter(
    'federation_bridge_transactions_total',
    'Total token bridge transactions',
    ['status']
)

bridge_liquidity = Gauge(
    'federation_bridge_liquidity_avt',
    'Available bridge liquidity',
    ['pool']
)

active_connections = Gauge(
    'federation_active_registry_connections',
    'Number of active registry connections'
)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")
```

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Federation Gateway Metrics",
    "panels": [
      {
        "title": "Message Routing Rate",
        "targets": [{
          "expr": "rate(federation_messages_routed_total[5m])"
        }]
      },
      {
        "title": "Routing Latency (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, federation_routing_latency_seconds)"
        }]
      },
      {
        "title": "Bridge Liquidity by Pool",
        "targets": [{
          "expr": "federation_bridge_liquidity_avt"
        }]
      },
      {
        "title": "Bridge Transaction Success Rate",
        "targets": [{
          "expr": "rate(federation_bridge_transactions_total{status='completed'}[5m]) / rate(federation_bridge_transactions_total[5m])"
        }]
      },
      {
        "title": "Active Registry Connections",
        "targets": [{
          "expr": "federation_active_registry_connections"
        }]
      }
    ]
  }
}
```

## Production Deployment

### High Availability Setup

```yaml
# kubernetes/federation-ha.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: federation-gateway
spec:
  serviceName: federation-gateway
  replicas: 3
  selector:
    matchLabels:
      app: federation-gateway
  template:
    metadata:
      labels:
        app: federation-gateway
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: federation-gateway
            topologyKey: kubernetes.io/hostname
      containers:
      - name: gateway
        image: agentvault/federation-gateway:1.0.0
        env:
        - name: CLUSTER_MODE
          value: "true"
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        ports:
        - containerPort: 8000
        - containerPort: 9090
        volumeMounts:
        - name: spire-agent-socket
          mountPath: /tmp/spire-agent
          readOnly: true
      volumes:
      - name: spire-agent-socket
        hostPath:
          path: /run/spire/sockets
          type: Directory
---
apiVersion: v1
kind: Service
metadata:
  name: federation-gateway-lb
spec:
  type: LoadBalancer
  selector:
    app: federation-gateway
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
```

## Key Features Demonstrated

1. **Cross-Registry Routing**: Seamless message delivery across trust boundaries
2. **Identity Verification**: SPIFFE/SPIRE-based cryptographic identity
3. **Token Bridging**: Economic value transfer between registries
4. **Service Discovery**: Unified view of agents across federations
5. **High Availability**: Stateful set with anti-affinity for resilience
6. **Security**: Mutual TLS, encryption, and rate limiting
7. **Observability**: Comprehensive metrics and monitoring

## Advanced Federation Features

### Multi-Registry Broadcast

```python
async def broadcast_to_federation(self, message: Dict[str, Any], criteria: Dict[str, Any]):
    """Broadcast message to all matching agents across registries"""
    matching_agents = []
    
    # Find all matching agents
    for agent_did, route in self.agent_routes.items():
        if self._matches_criteria(route, criteria):
            matching_agents.append((agent_did, route.registry_url))
    
    # Broadcast in parallel
    tasks = []
    for agent_did, registry in matching_agents:
        task = self.message_router.route_message(
            source_registry=message.get("source_registry"),
            target_registry=registry,
            message=FederatedMessage(
                source_did=message["from"],
                target_did=agent_did,
                payload=message["payload"],
                timestamp=datetime.utcnow()
            )
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "broadcast_id": str(uuid4()),
        "recipients": len(matching_agents),
        "successes": sum(1 for r in results if not isinstance(r, Exception))
    }
```

### Federation Governance

```python
class FederationGovernance:
    """Manage federation agreements and policies"""
    
    async def propose_new_member(self, registry_url: str, proposer_did: str):
        """Propose adding a new registry to the federation"""
        # Requires stake and existing member endorsement
        proposal = {
            "type": "add_registry",
            "registry_url": registry_url,
            "proposer": proposer_did,
            "stake": 10000.0,  # High stake for federation membership
            "voting_period": timedelta(days=7)
        }
        
        # Submit to governance contract
        return await self.submit_governance_proposal(proposal)
```

## Next Steps

- Implement federation consensus mechanism
- Add cross-chain bridges for multi-blockchain support
- Create federation explorer UI
- Build automated liquidity rebalancing
- Implement privacy-preserving routing
- Add support for hierarchical federations

---

*"In the federation of sovereign agents, the gateway is both bridge and guardian."*  
**- The Warrior Owl Doctrine**
