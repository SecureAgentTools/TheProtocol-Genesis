# AgentVault Registry Federation System

**Component**: Registry Federation  
**Version**: 1.0.0  
**Last Updated**: Tuesday, June 17, 2025

---

## Overview

The AgentVault Federation System enables multiple registry instances to share agent metadata, creating a decentralized discovery network. This allows agents registered in one registry to be discoverable by users of peer registries.

---

## Architecture

### Federation Model

```
┌─────────────────┐     Federation      ┌─────────────────┐
│   Registry A    │◄───────────────────►│   Registry B    │
│                 │                      │                 │
│  - Agent A1     │     Discovery        │  - Agent B1     │
│  - Agent A2     │◄───────────────────►│  - Agent B2     │
│                 │                      │                 │
└─────────────────┘                      └─────────────────┘
         ▲                                        ▲
         │              Federation                │
         └────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │   Registry C    │
                    │                 │
                    │  - Agent C1     │
                    │  - Agent C2     │
                    │                 │
                    └─────────────────┘
```

### Key Concepts

1. **Peer Registry**: Another AgentVault registry instance that shares data
2. **Federation Token**: API key used for registry-to-registry authentication
3. **Federated Discovery**: Searching across multiple registries
4. **Local Cache**: Temporary storage of federated results
5. **Health Monitoring**: Continuous peer connectivity checks

---

## Database Schema

### federation_peers Table

```sql
CREATE TABLE federation_peers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    registry_url VARCHAR(500) UNIQUE NOT NULL,
    api_key VARCHAR(255),  -- Encrypted
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP,
    last_health_check TIMESTAMP,
    health_status VARCHAR(50) DEFAULT 'unknown',
    agent_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_federation_peers_active ON federation_peers(is_active);
CREATE INDEX idx_federation_peers_url ON federation_peers(registry_url);
```

### federated_agents_cache Table

```sql
CREATE TABLE federated_agents_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peer_id UUID REFERENCES federation_peers(id) ON DELETE CASCADE,
    agent_data JSONB NOT NULL,
    agent_did VARCHAR(255) NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_cache_peer_id ON federated_agents_cache(peer_id);
CREATE INDEX idx_cache_expires ON federated_agents_cache(expires_at);
CREATE UNIQUE INDEX idx_cache_did_peer ON federated_agents_cache(agent_did, peer_id);
```

---

## API Endpoints

### Peer Management (Admin Only)

#### Add Federation Peer
```python
POST /api/v1/federation/peers
{
    "name": "Partner Registry",
    "registry_url": "https://partner.agentvault.io",
    "api_key": "their_federation_token"
}
```

#### List Federation Peers
```python
GET /api/v1/federation/peers

Response:
{
    "peers": [
        {
            "id": "uuid",
            "name": "Partner Registry",
            "registry_url": "https://partner.agentvault.io",
            "is_active": true,
            "health_status": "healthy",
            "agent_count": 150,
            "last_sync": "2025-06-17T00:00:00Z"
        }
    ]
}
```

#### Update Peer Status
```python
PUT /api/v1/federation/peers/{peer_id}
{
    "is_active": false  // Disable peer
}
```

### Federated Discovery

#### Search with Federation
```python
GET /api/v1/discovery/agents?include_federated=true&search=nlp

Response:
{
    "agents": [
        // Local agents
        {
            "id": "local-uuid",
            "name": "Local NLP Agent",
            "is_federated": false,
            "registry_url": "https://registry.agentvault.io"
        },
        // Federated agents
        {
            "id": "fed-uuid",
            "name": "Partner NLP Agent",
            "is_federated": true,
            "registry_url": "https://partner.agentvault.io",
            "registry_name": "Partner Registry"
        }
    ],
    "federation_stats": {
        "queried_registries": 3,
        "successful_queries": 2,
        "failed_queries": 1,
        "total_federated_results": 25
    }
}
```

### Health Monitoring

#### Check Federation Health
```python
GET /api/v1/federation/health

Response:
{
    "overall_status": "degraded",
    "active_peers": 2,
    "total_peers": 3,
    "peers": [
        {
            "peer_id": "uuid",
            "name": "Partner Registry",
            "status": "healthy",
            "response_time_ms": 150,
            "last_check": "2025-06-17T00:00:00Z"
        },
        {
            "peer_id": "uuid2",
            "name": "Registry C",
            "status": "unreachable",
            "error": "Connection timeout",
            "last_check": "2025-06-17T00:00:00Z"
        }
    ]
}
```

---

## Implementation Details

### Federation Service

```python
# src/agentvault_registry/services/federation.py

class FederationService:
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = 300  # 5 minutes
        
    async def discover_agents(
        self,
        query: str = None,
        agent_type: str = None,
        include_local: bool = True,
        timeout: int = 5000
    ) -> FederatedDiscoveryResult:
        """
        Perform federated discovery across all active peers.
        """
        results = []
        
        # Get local results if requested
        if include_local:
            local_agents = await self._get_local_agents(query, agent_type)
            results.extend(local_agents)
        
        # Query all active peers
        active_peers = self._get_active_peers()
        
        # Use asyncio.gather with timeout for parallel queries
        peer_tasks = [
            self._query_peer(peer, query, agent_type)
            for peer in active_peers
        ]
        
        peer_results = await asyncio.gather(
            *peer_tasks,
            return_exceptions=True
        )
        
        # Process results
        federation_stats = self._process_peer_results(
            peer_results,
            active_peers
        )
        
        return FederatedDiscoveryResult(
            agents=results,
            stats=federation_stats
        )
    
    async def _query_peer(
        self,
        peer: FederationPeer,
        query: str,
        agent_type: str
    ) -> List[Agent]:
        """
        Query a single peer registry.
        """
        # Check cache first
        cached = await self._get_cached_results(peer.id, query, agent_type)
        if cached:
            return cached
        
        try:
            # Make HTTP request to peer
            headers = {
                'Authorization': f'Bearer {peer.api_key}',
                'X-Federation-Registry': 'registry.agentvault.io'
            }
            
            params = {
                'search': query,
                'agent_type': agent_type,
                'limit': 50
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{peer.registry_url}/api/v1/agents",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        agents = data.get('agents', [])
                        
                        # Cache results
                        await self._cache_results(
                            peer.id,
                            query,
                            agent_type,
                            agents
                        )
                        
                        # Mark agents as federated
                        for agent in agents:
                            agent['is_federated'] = True
                            agent['registry_url'] = peer.registry_url
                            agent['registry_name'] = peer.name
                        
                        return agents
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to query peer {peer.name}: {e}")
            return []
```

### Health Monitor

```python
# src/agentvault_registry/services/health_monitor.py

class FederationHealthMonitor:
    def __init__(self, db: Session):
        self.db = db
        self.check_interval = 60  # seconds
        
    async def start(self):
        """Start background health monitoring."""
        while True:
            await self.check_all_peers()
            await asyncio.sleep(self.check_interval)
    
    async def check_all_peers(self):
        """Check health of all federation peers."""
        peers = self.db.query(FederationPeer).filter_by(is_active=True).all()
        
        for peer in peers:
            health_status = await self._check_peer_health(peer)
            
            # Update peer status
            peer.health_status = health_status['status']
            peer.last_health_check = datetime.utcnow()
            
            if health_status['status'] == 'healthy':
                peer.agent_count = health_status.get('agent_count', 0)
            
            self.db.commit()
    
    async def _check_peer_health(self, peer: FederationPeer) -> dict:
        """Check health of a single peer."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{peer.registry_url}/api/v1/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'healthy',
                            'response_time_ms': response_time,
                            'agent_count': data.get('agent_count', 0)
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'error': f'HTTP {response.status}'
                        }
                        
        except asyncio.TimeoutError:
            return {'status': 'timeout', 'error': 'Connection timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
```

### Caching Strategy

```python
class FederationCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
        
    async def get(self, peer_id: str, query_hash: str) -> Optional[List[dict]]:
        """Get cached federated results."""
        key = f"federation:{peer_id}:{query_hash}"
        cached = await self.redis.get(key)
        
        if cached:
            return json.loads(cached)
        return None
    
    async def set(
        self,
        peer_id: str,
        query_hash: str,
        agents: List[dict],
        ttl: int = None
    ):
        """Cache federated results."""
        key = f"federation:{peer_id}:{query_hash}"
        ttl = ttl or self.default_ttl
        
        await self.redis.setex(
            key,
            ttl,
            json.dumps(agents)
        )
    
    def compute_query_hash(self, query: str, agent_type: str) -> str:
        """Generate cache key from query parameters."""
        data = f"{query}:{agent_type}".encode()
        return hashlib.md5(data).hexdigest()
```

---

## Security Considerations

### Authentication

1. **Peer API Keys**: Each peer relationship uses unique API keys
2. **Mutual TLS**: Optional mTLS for enhanced security
3. **Request Signing**: HMAC signatures on federated requests
4. **Rate Limiting**: Prevent abuse of federation endpoints

### Data Privacy

1. **Selective Sharing**: Choose which agents to share via federation
2. **Data Minimization**: Only share necessary metadata
3. **No PII**: Never share user personal information
4. **Audit Logging**: Track all federation queries

### Implementation
```python
class FederationSecurity:
    @staticmethod
    def sign_request(
        method: str,
        path: str,
        body: str,
        secret: str
    ) -> str:
        """Generate HMAC signature for request."""
        timestamp = str(int(time.time()))
        message = f"{method}\n{path}\n{body}\n{timestamp}"
        
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}.{signature}"
    
    @staticmethod
    def verify_signature(
        signature: str,
        method: str,
        path: str,
        body: str,
        secret: str,
        max_age: int = 300
    ) -> bool:
        """Verify request signature."""
        try:
            timestamp, sig = signature.split('.')
            
            # Check timestamp
            if int(time.time()) - int(timestamp) > max_age:
                return False
            
            # Verify signature
            expected = FederationSecurity.sign_request(
                method, path, body, secret
            ).split('.')[1]
            
            return hmac.compare_digest(sig, expected)
            
        except Exception:
            return False
```

---

## Configuration

### Environment Variables

```bash
# Federation settings
FEDERATION_ENABLED=true
FEDERATION_CACHE_TTL=300
FEDERATION_QUERY_TIMEOUT=5000
FEDERATION_MAX_RESULTS_PER_PEER=50

# Security
FEDERATION_REQUIRE_SIGNATURE=true
FEDERATION_SIGNATURE_MAX_AGE=300

# Health monitoring
FEDERATION_HEALTH_CHECK_INTERVAL=60
FEDERATION_UNHEALTHY_THRESHOLD=3
```

### Peer Configuration

```python
# config/federation_peers.py
TRUSTED_PEERS = [
    {
        "name": "Official Partner Registry",
        "url": "https://partner.agentvault.io",
        "public_key": "-----BEGIN PUBLIC KEY-----\n...",
        "require_mtls": True
    }
]
```

---

## Monitoring and Metrics

### Key Metrics

1. **Federation Query Performance**
   - Average response time per peer
   - Success/failure rates
   - Cache hit rates

2. **Peer Health**
   - Uptime percentage
   - Average response times
   - Error rates

3. **Data Volume**
   - Agents discovered via federation
   - Query volume per peer
   - Bandwidth usage

### Prometheus Metrics

```python
# Metric definitions
federation_query_duration = Histogram(
    'federation_query_duration_seconds',
    'Time spent querying federation peer',
    ['peer_name', 'status']
)

federation_cache_hits = Counter(
    'federation_cache_hits_total',
    'Number of federation cache hits',
    ['peer_name']
)

federation_peer_health = Gauge(
    'federation_peer_health',
    'Health status of federation peer (1=healthy, 0=unhealthy)',
    ['peer_name']
)
```

---

## Troubleshooting

### Common Issues

#### Peer Connection Failures
```bash
# Check peer connectivity
curl -H "Authorization: Bearer $API_KEY" \
     https://peer.registry.com/api/v1/health

# Verify DNS resolution
nslookup peer.registry.com

# Test with increased timeout
curl --max-time 30 https://peer.registry.com/api/v1/agents
```

#### Cache Issues
```python
# Clear federation cache
from agentvault_registry.services.cache import federation_cache
await federation_cache.clear_peer_cache(peer_id)

# Force cache refresh
GET /api/v1/discovery/agents?include_federated=true&force_refresh=true
```

#### Performance Problems
```sql
-- Check slow queries
SELECT peer_id, COUNT(*) as query_count, AVG(response_time_ms)
FROM federation_query_log
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY peer_id
ORDER BY AVG(response_time_ms) DESC;
```

---

## Best Practices

### For Registry Operators

1. **Selective Peering**: Only peer with trusted registries
2. **Monitor Performance**: Set up alerts for slow peers
3. **Cache Wisely**: Balance freshness vs performance
4. **Document Policies**: Clear data sharing agreements
5. **Regular Audits**: Review federation logs monthly

### For Developers

1. **Handle Failures Gracefully**: Federated results are optional
2. **Show Federation Status**: Indicate data sources in UI
3. **Respect Rate Limits**: Don't overwhelm peer registries
4. **Cache Client-Side**: Reduce redundant queries
5. **Provide Feedback**: Show federation progress to users

---

## Future Enhancements

1. **Blockchain Integration**: Decentralized peer discovery
2. **Advanced Routing**: Intelligent query routing based on peer specialization
3. **Data Synchronization**: Full bidirectional sync option
4. **Federation Marketplace**: Economic incentives for data sharing
5. **Privacy Preserving**: Zero-knowledge proofs for sensitive queries

---

**End of Federation Documentation**
