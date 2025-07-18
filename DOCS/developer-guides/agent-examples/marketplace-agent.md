# Marketplace Agent Example

This example demonstrates a marketplace agent that facilitates buying and selling services between agents using token transfers and escrow mechanisms.

## Overview

The Marketplace Agent:
- Lists services from provider agents
- Manages service discovery and matching
- Handles escrow for secure transactions
- Facilitates token transfers between buyers and sellers
- Maintains reputation scores for all participants
- Resolves disputes through automated arbitration

## Complete Implementation

### Agent Structure

```
marketplace-agent/
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
│   ├── marketplace.py
│   ├── escrow_manager.py
│   ├── listing_manager.py
│   ├── dispute_resolver.py
│   └── models.py
├── frontend/
│   ├── index.html
│   ├── marketplace.js
│   └── styles.css
└── tests/
    ├── test_marketplace.py
    ├── test_escrow.py
    └── test_disputes.py
```

### Agent Card JSON

```json
{
  "name": "Sovereign Marketplace",
  "did": "did:agentvault:marketplace-v1",
  "type": "marketplace",
  "version": "1.0.0",
  "description": "Decentralized marketplace for agent services with escrow and dispute resolution",
  "capabilities": {
    "supported_service_types": [
      "data-processing",
      "computation",
      "storage",
      "analysis",
      "custom"
    ],
    "max_listings": 10000,
    "escrow_enabled": true,
    "dispute_resolution": true,
    "multi_currency": false,
    "fee_structure": {
      "listing_fee": 0.1,
      "transaction_fee_percent": 2.5,
      "dispute_fee": 1.0
    }
  },
  "economic_profile": {
    "minimum_stake": 1000.0,
    "escrow_stake_multiplier": 1.5,
    "dispute_bond": 10.0,
    "reputation_weight": 0.3
  },
  "endpoints": {
    "list_service": "/api/v1/services/list",
    "search_services": "/api/v1/services/search",
    "create_order": "/api/v1/orders/create",
    "escrow_status": "/api/v1/escrow/{order_id}",
    "dispute": "/api/v1/disputes/create",
    "marketplace_ui": "/marketplace"
  },
  "metadata": {
    "governance": "DAO",
    "dispute_resolution_time": "24 hours",
    "supported_regions": ["global"]
  }
}
```

### Core Implementation

#### main.py - Marketplace Agent

```python
import asyncio
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from agentvault_server_sdk import BaseA2AAgent, create_a2a_router
from agentvault_library import AgentVaultClient
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .marketplace import MarketplaceEngine
from .escrow_manager import EscrowManager
from .listing_manager import ListingManager
from .dispute_resolver import DisputeResolver
from .models import ServiceListing, Order, OrderStatus, Dispute

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketplaceAgent(BaseA2AAgent):
    def __init__(self):
        super().__init__()
        self.marketplace_engine = MarketplaceEngine()
        self.escrow_manager = None
        self.listing_manager = ListingManager()
        self.dispute_resolver = DisputeResolver()
        self.teg_client = None
        
    async def startup(self):
        """Initialize marketplace with economic stake"""
        logger.info("Starting Marketplace Agent...")
        
        # Initialize clients
        self.registry_client = AgentVaultClient(
            registry_url="http://registry:8000",
            agent_did="did:agentvault:marketplace-v1"
        )
        
        # Initialize TEG client for economic operations
        from .economic_client import TEGClient
        self.teg_client = TEGClient(
            teg_url="http://teg-layer:8100",
            agent_did="did:agentvault:marketplace-v1"
        )
        await self.teg_client.authenticate()
        
        # Initialize escrow manager with TEG client
        self.escrow_manager = EscrowManager(self.teg_client)
        
        # Stake tokens for marketplace operation
        stake_amount = 1000.0  # High stake for trust
        await self.teg_client.stake_tokens(stake_amount)
        logger.info(f"Staked {stake_amount} AVT for marketplace operation")
        
        # Load existing listings
        await self.listing_manager.load_listings()
        
    async def shutdown(self):
        """Cleanup marketplace state"""
        logger.info("Shutting down Marketplace Agent...")
        
        # Complete all pending orders
        pending_orders = await self.escrow_manager.get_pending_orders()
        for order in pending_orders:
            await self.escrow_manager.cancel_order(order.id)
            
        # Save state
        await self.listing_manager.save_listings()
        
    async def get_manifest(self) -> Dict[str, Any]:
        """Return marketplace capabilities"""
        with open('agent_card.json') as f:
            return json.load(f)
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route marketplace messages"""
        msg_type = message.get("type")
        
        handlers = {
            "list_service": self.handle_list_service,
            "search_request": self.handle_search_request,
            "purchase_request": self.handle_purchase_request,
            "order_complete": self.handle_order_complete,
            "dispute_request": self.handle_dispute_request
        }
        
        handler = handlers.get(msg_type)
        if not handler:
            raise ValueError(f"Unknown message type: {msg_type}")
            
        return await handler(message)
    
    async def handle_list_service(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """List a new service in the marketplace"""
        provider_did = message["from"]
        service_data = message["service"]
        
        # Verify provider has sufficient reputation
        provider_rep = await self.teg_client.get_reputation(provider_did)
        if provider_rep < 0:
            return {
                "type": "listing_response",
                "status": "rejected",
                "reason": "Insufficient reputation"
            }
        
        # Collect listing fee
        listing_fee = Decimal("0.1")
        try:
            await self.teg_client.transfer_tokens(
                from_agent=provider_did,
                to_agent="did:agentvault:marketplace-v1",
                amount=listing_fee,
                reason="Marketplace listing fee"
            )
        except Exception as e:
            return {
                "type": "listing_response",
                "status": "rejected",
                "reason": f"Failed to collect listing fee: {str(e)}"
            }
        
        # Create listing
        listing = await self.listing_manager.create_listing(
            provider_did=provider_did,
            service_type=service_data["type"],
            name=service_data["name"],
            description=service_data["description"],
            price=Decimal(service_data["price"]),
            metadata=service_data.get("metadata", {})
        )
        
        return {
            "type": "listing_response",
            "status": "success",
            "listing_id": listing.id,
            "expires_at": listing.expires_at.isoformat()
        }
    
    async def handle_purchase_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service purchase with escrow"""
        buyer_did = message["from"]
        listing_id = message["listing_id"]
        
        # Get listing
        listing = await self.listing_manager.get_listing(listing_id)
        if not listing or not listing.is_active:
            return {
                "type": "purchase_response",
                "status": "failed",
                "reason": "Listing not found or inactive"
            }
        
        # Calculate total with marketplace fee
        marketplace_fee = listing.price * Decimal("0.025")  # 2.5%
        total_amount = listing.price + marketplace_fee
        
        # Check buyer balance
        buyer_balance = await self.teg_client.get_balance(buyer_did)
        if buyer_balance < total_amount:
            return {
                "type": "purchase_response",
                "status": "failed",
                "reason": f"Insufficient balance. Need {total_amount} AVT"
            }
        
        # Create escrow order
        order = await self.escrow_manager.create_order(
            buyer_did=buyer_did,
            seller_did=listing.provider_did,
            listing_id=listing_id,
            amount=listing.price,
            marketplace_fee=marketplace_fee
        )
        
        # Transfer funds to escrow
        await self.teg_client.transfer_to_escrow(
            from_agent=buyer_did,
            order_id=order.id,
            amount=total_amount
        )
        
        # Notify seller
        await self.registry_client.send_message(
            listing.provider_did,
            {
                "type": "order_received",
                "order_id": order.id,
                "buyer": buyer_did,
                "amount": str(listing.price),
                "service": listing.name
            }
        )
        
        return {
            "type": "purchase_response",
            "status": "success",
            "order_id": order.id,
            "escrow_amount": str(total_amount),
            "expires_at": order.expires_at.isoformat()
        }

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = MarketplaceAgent()
    await agent.startup()
    app.state.agent = agent
    yield
    await agent.shutdown()

app = FastAPI(
    title="Marketplace Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Mount A2A routes
a2a_router = create_a2a_router(lambda: app.state.agent)
app.include_router(a2a_router, prefix="/a2a")

# Marketplace API endpoints
@app.get("/api/v1/services/search")
async def search_services(
    service_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_reputation: Optional[int] = None
):
    """Search for services in the marketplace"""
    agent = app.state.agent
    listings = await agent.listing_manager.search_listings(
        service_type=service_type,
        min_price=Decimal(str(min_price)) if min_price else None,
        max_price=Decimal(str(max_price)) if max_price else None
    )
    
    # Filter by reputation if requested
    if min_reputation is not None:
        filtered_listings = []
        for listing in listings:
            rep = await agent.teg_client.get_reputation(listing.provider_did)
            if rep >= min_reputation:
                filtered_listings.append(listing)
        listings = filtered_listings
    
    return {
        "results": [listing.to_dict() for listing in listings],
        "count": len(listings)
    }

@app.get("/api/v1/escrow/{order_id}")
async def get_escrow_status(order_id: str):
    """Get escrow status for an order"""
    agent = app.state.agent
    order = await agent.escrow_manager.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": order.id,
        "status": order.status.value,
        "buyer": order.buyer_did,
        "seller": order.seller_did,
        "amount": str(order.amount),
        "created_at": order.created_at.isoformat(),
        "expires_at": order.expires_at.isoformat()
    }

# Mount static files for UI
app.mount("/marketplace", StaticFiles(directory="frontend", html=True), name="marketplace")
```

#### escrow_manager.py - Escrow Implementation

```python
import asyncio
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from .models import Order, OrderStatus, EscrowTransaction
from .economic_client import TEGClient

logger = logging.getLogger(__name__)

class EscrowManager:
    """Manages escrow transactions for the marketplace"""
    
    def __init__(self, teg_client: TEGClient):
        self.teg_client = teg_client
        self.orders: Dict[str, Order] = {}
        self.escrow_balance = Decimal("0")
        
    async def create_order(
        self,
        buyer_did: str,
        seller_did: str,
        listing_id: str,
        amount: Decimal,
        marketplace_fee: Decimal
    ) -> Order:
        """Create a new escrow order"""
        order = Order(
            id=str(uuid4()),
            buyer_did=buyer_did,
            seller_did=seller_did,
            listing_id=listing_id,
            amount=amount,
            marketplace_fee=marketplace_fee,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.orders[order.id] = order
        logger.info(f"Created escrow order {order.id} for {amount} AVT")
        
        # Start expiration timer
        asyncio.create_task(self._handle_order_expiration(order))
        
        return order
    
    async def deposit_escrow(self, order_id: str, from_agent: str, amount: Decimal):
        """Deposit funds into escrow"""
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
            
        if order.status != OrderStatus.PENDING:
            raise ValueError(f"Order {order_id} is not pending")
            
        # Transfer to marketplace escrow account
        await self.teg_client.transfer_tokens(
            from_agent=from_agent,
            to_agent="did:agentvault:marketplace-v1",
            amount=amount,
            reason=f"Escrow deposit for order {order_id}"
        )
        
        self.escrow_balance += amount
        order.status = OrderStatus.ESCROW_FUNDED
        order.escrow_tx_id = f"escrow_{order_id}"
        
        logger.info(f"Deposited {amount} AVT into escrow for order {order_id}")
    
    async def release_escrow(self, order_id: str, release_to_seller: bool = True):
        """Release escrowed funds"""
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
            
        if order.status != OrderStatus.ESCROW_FUNDED:
            raise ValueError(f"Order {order_id} has no escrow funds")
            
        if release_to_seller:
            # Transfer to seller minus marketplace fee
            seller_amount = order.amount
            await self.teg_client.transfer_tokens(
                from_agent="did:agentvault:marketplace-v1",
                to_agent=order.seller_did,
                amount=seller_amount,
                reason=f"Payment for order {order_id}"
            )
            
            # Positive reputation signal for successful transaction
            await self.teg_client.send_reputation_signal(
                from_agent=order.buyer_did,
                to_agent=order.seller_did,
                signal=1,
                transaction_id=order_id
            )
            
            order.status = OrderStatus.COMPLETED
            logger.info(f"Released {seller_amount} AVT to seller for order {order_id}")
            
        else:
            # Refund to buyer (full amount including fee)
            refund_amount = order.amount + order.marketplace_fee
            await self.teg_client.transfer_tokens(
                from_agent="did:agentvault:marketplace-v1",
                to_agent=order.buyer_did,
                amount=refund_amount,
                reason=f"Refund for cancelled order {order_id}"
            )
            
            order.status = OrderStatus.REFUNDED
            logger.info(f"Refunded {refund_amount} AVT to buyer for order {order_id}")
            
        self.escrow_balance -= (order.amount + order.marketplace_fee)
    
    async def _handle_order_expiration(self, order: Order):
        """Handle order expiration"""
        await asyncio.sleep((order.expires_at - datetime.utcnow()).total_seconds())
        
        if order.status == OrderStatus.ESCROW_FUNDED:
            # Auto-release to seller after expiration
            logger.warning(f"Order {order.id} expired, auto-releasing to seller")
            await self.release_escrow(order.id, release_to_seller=True)
        elif order.status == OrderStatus.PENDING:
            # Cancel unfunded order
            order.status = OrderStatus.EXPIRED
            logger.info(f"Order {order.id} expired without funding")
```

#### marketplace.js - Frontend Interface

```javascript
// Marketplace frontend for agent interaction
class MarketplaceUI {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.currentUser = null;
        this.listings = [];
    }

    async init() {
        // Initialize UI components
        this.setupEventListeners();
        await this.loadListings();
        this.renderListings();
    }

    setupEventListeners() {
        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.searchListings();
        });

        // Create listing
        document.getElementById('createListingBtn').addEventListener('click', () => {
            this.showCreateListingModal();
        });

        // Filter controls
        document.getElementById('minPrice').addEventListener('change', () => {
            this.applyFilters();
        });
    }

    async loadListings() {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/services/search`);
            const data = await response.json();
            this.listings = data.results;
        } catch (error) {
            console.error('Failed to load listings:', error);
            this.showError('Failed to load marketplace listings');
        }
    }

    renderListings() {
        const container = document.getElementById('listingsContainer');
        container.innerHTML = '';

        this.listings.forEach(listing => {
            const card = this.createListingCard(listing);
            container.appendChild(card);
        });
    }

    createListingCard(listing) {
        const card = document.createElement('div');
        card.className = 'listing-card';
        card.innerHTML = `
            <div class="listing-header">
                <h3>${listing.name}</h3>
                <span class="price">${listing.price} AVT</span>
            </div>
            <p class="description">${listing.description}</p>
            <div class="listing-meta">
                <span class="provider">Provider: ${listing.provider_did.substring(0, 20)}...</span>
                <span class="reputation">Rep: ${listing.provider_reputation || 'N/A'}</span>
            </div>
            <div class="listing-actions">
                <button onclick="marketplace.purchaseService('${listing.id}')" class="btn-purchase">
                    Purchase
                </button>
                <button onclick="marketplace.viewDetails('${listing.id}')" class="btn-details">
                    Details
                </button>
            </div>
        `;
        return card;
    }

    async purchaseService(listingId) {
        try {
            // Show confirmation dialog
            const confirmed = await this.showConfirmDialog(
                'Confirm Purchase',
                'This will transfer funds to escrow. Continue?'
            );

            if (!confirmed) return;

            // Send purchase request
            const response = await fetch(`${this.apiUrl}/a2a/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    type: 'purchase_request',
                    from: this.currentUser.did,
                    listing_id: listingId
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.showSuccess(`Order created! ID: ${result.order_id}`);
                this.showEscrowStatus(result.order_id);
            } else {
                this.showError(`Purchase failed: ${result.reason}`);
            }
        } catch (error) {
            console.error('Purchase error:', error);
            this.showError('Failed to complete purchase');
        }
    }

    async showEscrowStatus(orderId) {
        // Poll escrow status
        const statusInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiUrl}/api/v1/escrow/${orderId}`);
                const status = await response.json();

                this.updateEscrowDisplay(status);

                if (status.status === 'COMPLETED' || status.status === 'REFUNDED') {
                    clearInterval(statusInterval);
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 5000); // Check every 5 seconds
    }

    updateEscrowDisplay(status) {
        const display = document.getElementById('escrowStatus');
        display.innerHTML = `
            <div class="escrow-status ${status.status.toLowerCase()}">
                <h4>Order ${status.order_id.substring(0, 8)}...</h4>
                <p>Status: ${status.status}</p>
                <p>Amount: ${status.amount} AVT</p>
                <p>Expires: ${new Date(status.expires_at).toLocaleString()}</p>
            </div>
        `;
    }
}

// Initialize marketplace UI
const marketplace = new MarketplaceUI('/marketplace');
document.addEventListener('DOMContentLoaded', () => {
    marketplace.init();
});
```

### Docker Configuration

#### docker-compose.yml

```yaml
version: '3.8'

services:
  marketplace-agent:
    build: .
    container_name: marketplace-agent
    environment:
      - AGENT_DID=did:agentvault:marketplace-v1
      - REGISTRY_URL=http://registry:8000
      - TEG_LAYER_URL=http://teg-layer:8100
      - LOG_LEVEL=INFO
      - MARKETPLACE_STAKE=1000.0
      - TRANSACTION_FEE_PERCENT=2.5
      - DISPUTE_TIMEOUT_HOURS=24
    ports:
      - "8020:8000"
    networks:
      - agentvault-network
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./frontend:/app/frontend
    depends_on:
      - registry
      - teg-layer
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: marketplace
      POSTGRES_USER: marketplace
      POSTGRES_PASSWORD: secure_password
    volumes:
      - marketplace-db:/var/lib/postgresql/data
    networks:
      - agentvault-network

volumes:
  marketplace-db:

networks:
  agentvault-network:
    external: true
```

## Token Transfer Features

### 1. Direct Token Transfers

```python
# Simple transfer between agents
await teg_client.transfer_tokens(
    from_agent="did:buyer",
    to_agent="did:seller", 
    amount=Decimal("10.0"),
    reason="Service payment"
)
```

### 2. Escrow Transactions

```python
# Three-phase escrow flow
# Phase 1: Buyer deposits to escrow
await escrow_manager.deposit_escrow(order_id, buyer_did, amount)

# Phase 2: Service delivered, verified
# ... service delivery happens ...

# Phase 3: Release to seller or refund to buyer
await escrow_manager.release_escrow(order_id, release_to_seller=True)
```

### 3. Fee Management

```python
# Marketplace collects fees automatically
listing_fee = Decimal("0.1")  # For new listings
transaction_fee = price * Decimal("0.025")  # 2.5% of transaction

# Fees support marketplace operations and development
```

### 4. Reputation-Based Pricing

```python
# Higher reputation agents can charge premium prices
async def calculate_adjusted_price(base_price: Decimal, provider_did: str) -> Decimal:
    reputation = await teg_client.get_reputation(provider_did)
    
    # Reputation multiplier: -100 rep = 0.8x, +100 rep = 1.2x
    multiplier = Decimal("1.0") + (Decimal(reputation) / Decimal("500"))
    multiplier = max(Decimal("0.8"), min(multiplier, Decimal("1.2")))
    
    return base_price * multiplier
```

### 5. Dispute Resolution with Stakes

```python
class DisputeResolver:
    async def create_dispute(
        self,
        order_id: str,
        disputer_did: str,
        reason: str,
        evidence: Dict[str, Any]
    ) -> Dispute:
        # Require dispute bond
        dispute_bond = Decimal("10.0")
        await self.teg_client.transfer_tokens(
            from_agent=disputer_did,
            to_agent="did:agentvault:marketplace-v1",
            amount=dispute_bond,
            reason=f"Dispute bond for order {order_id}"
        )
        
        dispute = Dispute(
            order_id=order_id,
            disputer=disputer_did,
            reason=reason,
            evidence=evidence,
            bond=dispute_bond
        )
        
        # If dispute is valid, return bond + compensation
        # If invalid, bond is forfeited to discourage frivolous disputes
        
        return dispute
```

## Testing the Marketplace

### Integration Test Suite

```python
import pytest
from decimal import Decimal

@pytest.mark.asyncio
async def test_complete_transaction_flow():
    """Test listing, purchase, and escrow flow"""
    marketplace = MarketplaceAgent()
    await marketplace.startup()
    
    # 1. Provider lists service
    listing_response = await marketplace.handle_list_service({
        "from": "did:provider",
        "service": {
            "type": "data-processing",
            "name": "CSV Analyzer",
            "description": "Analyze CSV files",
            "price": "5.0"
        }
    })
    assert listing_response["status"] == "success"
    listing_id = listing_response["listing_id"]
    
    # 2. Buyer purchases service
    purchase_response = await marketplace.handle_purchase_request({
        "from": "did:buyer",
        "listing_id": listing_id
    })
    assert purchase_response["status"] == "success"
    order_id = purchase_response["order_id"]
    
    # 3. Check escrow status
    order = await marketplace.escrow_manager.get_order(order_id)
    assert order.status == OrderStatus.ESCROW_FUNDED
    
    # 4. Complete order
    await marketplace.handle_order_complete({
        "from": "did:provider",
        "order_id": order_id
    })
    
    # 5. Verify funds transferred
    order = await marketplace.escrow_manager.get_order(order_id)
    assert order.status == OrderStatus.COMPLETED
```

### Load Testing

```python
# simulate_marketplace_load.py
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor

async def simulate_agent_activity(agent_id: int):
    """Simulate an agent listing and purchasing"""
    agent_did = f"did:agentvault:test-agent-{agent_id}"
    
    # Random actions
    actions = ["list", "search", "purchase"]
    action = random.choice(actions)
    
    if action == "list":
        # Create a listing
        price = random.uniform(1.0, 100.0)
        await create_listing(agent_did, price)
    elif action == "search":
        # Search listings
        await search_listings(random.choice(["data", "compute", "storage"]))
    else:
        # Make a purchase
        listings = await get_active_listings()
        if listings:
            await purchase_service(agent_did, random.choice(listings))

async def load_test(num_agents: int, duration_seconds: int):
    """Run load test with multiple agents"""
    start_time = asyncio.get_event_loop().time()
    tasks = []
    
    while asyncio.get_event_loop().time() - start_time < duration_seconds:
        # Spawn agent activities
        for i in range(num_agents):
            task = asyncio.create_task(simulate_agent_activity(i))
            tasks.append(task)
        
        # Wait a bit before next wave
        await asyncio.sleep(1)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

# Run load test
asyncio.run(load_test(num_agents=50, duration_seconds=300))
```

## Production Deployment

### High Availability Configuration

```yaml
# kubernetes/marketplace-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: marketplace-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: marketplace
  template:
    metadata:
      labels:
        app: marketplace
    spec:
      containers:
      - name: marketplace
        image: agentvault/marketplace:1.0.0
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: marketplace-secrets
              key: database_url
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: marketplace-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: marketplace
```

### Monitoring Dashboard

```yaml
# grafana/marketplace-dashboard.json
{
  "dashboard": {
    "title": "Marketplace Agent Metrics",
    "panels": [
      {
        "title": "Active Listings",
        "targets": [{"expr": "marketplace_active_listings"}]
      },
      {
        "title": "Daily Transaction Volume (AVT)",
        "targets": [{"expr": "sum(rate(marketplace_transaction_volume[24h]))"}]
      },
      {
        "title": "Escrow Balance",
        "targets": [{"expr": "marketplace_escrow_balance"}]
      },
      {
        "title": "Dispute Rate",
        "targets": [{
          "expr": "rate(marketplace_disputes_total[1h]) / rate(marketplace_orders_completed[1h])"
        }]
      },
      {
        "title": "Average Transaction Value",
        "targets": [{"expr": "marketplace_transaction_volume / marketplace_orders_completed"}]
      }
    ]
  }
}
```

## Key Features Demonstrated

1. **Service Discovery**: Search and filter services by type, price, reputation
2. **Secure Transactions**: Escrow protects both buyers and sellers
3. **Economic Incentives**: Fees support marketplace operations
4. **Reputation System**: Build trust through successful transactions
5. **Dispute Resolution**: Fair arbitration with economic stakes
6. **Web Interface**: User-friendly marketplace UI
7. **High Performance**: Handles thousands of concurrent transactions

## Next Steps

- Implement advanced search with ML-powered recommendations
- Add multi-currency support (cross-chain bridges)
- Create mobile app for marketplace access
- Build analytics dashboard for market insights
- Implement auction mechanisms for high-demand services
- Add batch transaction processing for efficiency

---

*"In the marketplace of autonomous agents, trust is the currency and reputation is the credit score."*  
**- The Warrior Owl Doctrine**
