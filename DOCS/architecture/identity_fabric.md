# Identity Fabric Architecture

## Overview

The Identity Fabric is the Zero-Trust security foundation of the Sovereign Stack, providing cryptographic workload identities through SPIFFE/SPIRE and fine-grained authorization through Open Policy Agent (OPA). It ensures that every service and agent in the ecosystem has a unique, verifiable identity that cannot be forged, creating a trustless environment where security is cryptographic rather than perimeter-based.

## Core Architecture

### Zero-Trust Security Model

The Identity Fabric implements true Zero-Trust architecture where:
- **No implicit trust**: Every request is authenticated and authorized
- **Cryptographic identities**: Unforgeable SPIFFE IDs for all workloads
- **Short-lived credentials**: Automatic rotation prevents compromise
- **Policy-driven access**: Fine-grained authorization decisions

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            IDENTITY FABRIC ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────┐                    ┌─────────────────────┐             │
│  │   SPIRE Server      │                    │  OPA Policy Engine  │             │
│  │                     │                    │                     │             │
│  │ Trust Domain:       │                    │ • Authorization     │             │
│  │ agentvault.com      │                    │ • Policy Evaluation │             │
│  │                     │                    │ • Decision Logging  │             │
│  │ • Root CA          │                    │ • Rego Language     │             │
│  │ • SVID Issuance    │                    └──────────┬──────────┘             │
│  │ • Trust Bundles    │                               │                         │
│  └──────────┬──────────┘                               │                         │
│             │                                           │                         │
│  ┌──────────▼──────────┐                    ┌──────────▼──────────┐             │
│  │   SPIRE Agents      │                    │   Policy Decision   │             │
│  │                     │                    │       Points        │             │
│  │ • Node Attestation  │                    │                     │             │
│  │ • Workload API     │                    │ • Sidecar Proxies   │             │
│  │ • SVID Distribution │                    │ • SDK Integration   │             │
│  │ • Auto Rotation    │                    │ • Cache Layer       │             │
│  └──────────┬──────────┘                    └──────────┬──────────┘             │
│             │                                           │                         │
│  ━━━━━━━━━━━┼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┼━━━━━━━━━━━━━━━━━━━━   │
│             │                                           │                         │
│  ┌──────────▼──────────────────────────────────────────▼──────────┐             │
│  │                         WORKLOAD IDENTITIES                     │             │
│  │                                                                 │             │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐          │             │
│  │  │  Registry  │    │ TEG Layer  │    │   Agents   │          │             │
│  │  │  Backend   │    │    Core    │    │            │          │             │
│  │  │            │    │            │    │            │          │             │
│  │  │ X.509 SVID│    │ X.509 SVID │    │ JWT-SVID   │          │             │
│  │  └────────────┘    └────────────┘    └────────────┘          │             │
│  └─────────────────────────────────────────────────────────────────┘             │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## SPIFFE/SPIRE Implementation

### SPIFFE Identity Framework

SPIFFE (Secure Production Identity Framework For Everyone) provides a standard for identifying and authenticating workloads:

#### SPIFFE ID Format
```
spiffe://trust-domain/path/to/workload

Examples:
spiffe://agentvault.com/service/registry-backend
spiffe://agentvault.com/agent/alice@example.com
spiffe://agentvault.com/admin/platform-operator
```

#### Trust Domain Hierarchy
```
agentvault.com/
├── service/           # Core platform services
│   ├── registry-backend
│   ├── teg-core
│   └── federation-hub
├── agent/             # Individual AI agents
│   ├── user_at_example_dot_com
│   └── trading_bot_v2
├── admin/             # Administrative workloads
│   └── platform-operator
└── spire/             # SPIRE infrastructure
    └── agent/
        └── default
```

### SPIRE Architecture

#### SPIRE Server
The central authority for the trust domain:

```yaml
# SPIRE Server Configuration
server:
  bind_address: "0.0.0.0"
  bind_port: "8081"
  trust_domain: "agentvault.com"
  data_dir: "/opt/spire/data"
  log_level: "INFO"
  
  ca_ttl: "24h"           # CA certificate lifetime
  default_svid_ttl: "1h"  # Default SVID lifetime
  
  # High Availability Configuration
  ha_enabled: true
  ha_cluster_name: "production"
  ha_storage_backend: "postgres"
```

#### SPIRE Agent
Runs on each node to manage workload identities:

```yaml
# SPIRE Agent Configuration
agent:
  data_dir: "/opt/spire/data"
  log_level: "INFO"
  server_address: "spire-server"
  server_port: "8081"
  trust_domain: "agentvault.com"
  
  # Workload attestation
  workload_attestors:
    - docker:
        docker_socket_path: "/var/run/docker.sock"
    - k8s:
        skip_kubelet_verification: true
```

### Identity Types

#### 1. X.509 SVIDs (Service Identities)
Used for service-to-service mutual TLS:

```python
# Service acquiring X.509 SVID
from pyspiffe.workloadapi import default_workload_api_client
from pyspiffe.x509_context import X509Context

class SecureService:
    def __init__(self):
        self.x509_context = None
        self._refresh_svid()
    
    def _refresh_svid(self):
        """Obtain X.509 SVID from SPIRE Agent"""
        with default_workload_api_client() as client:
            self.x509_context = client.fetch_x509_context()
            
    @property
    def svid(self):
        return self.x509_context.default_svid()
    
    @property
    def bundle(self):
        return self.x509_context.x509_bundle_set
```

**X.509 SVID Properties**:
- Lifetime: 1 hour (configurable)
- Auto-rotation: 30 minutes before expiry
- Format: X.509 certificate with SPIFFE ID in SAN
- Usage: mTLS between services

#### 2. JWT SVIDs (Agent Identities)
Used for agent authentication to services:

```python
# Registry acquiring JWT-SVID for agent
async def acquire_agent_jwt_svid(
    agent_email: str,
    audience: List[str]
) -> str:
    """Get JWT-SVID for agent identity"""
    
    # Map email to SPIFFE ID
    agent_spiffe_id = f"spiffe://agentvault.com/agent/{agent_email.replace('@', '_at_').replace('.', '_dot_')}"
    
    with default_workload_api_client() as client:
        jwt_svids = client.fetch_jwt_svid(
            audiences=audience,
            subject=agent_spiffe_id
        )
        
    return jwt_svids[0].token
```

**JWT-SVID Properties**:
- Lifetime: 5 minutes (security-optimized)
- Audience-restricted: Specific target services
- Claims: Standard JWT with SPIFFE subject
- Usage: API authentication

### Workload Registration

#### Service Registration
```bash
# Register Registry Backend
docker exec agentvault-spire-server \
    spire-server entry create \
    -parentID spiffe://agentvault.com/spire/agent/default \
    -spiffeID spiffe://agentvault.com/service/registry-backend \
    -selector docker:label:service:registry-backend \
    -ttl 3600

# Register TEG Core
docker exec agentvault-spire-server \
    spire-server entry create \
    -parentID spiffe://agentvault.com/spire/agent/default \
    -spiffeID spiffe://agentvault.com/service/teg-core \
    -selector docker:label:service:teg-core \
    -ttl 3600
```

#### Dynamic Agent Registration
```python
async def register_agent_identity(agent_did: str, agent_email: str):
    """Dynamically register agent with SPIRE"""
    
    spiffe_id = f"spiffe://agentvault.com/agent/{agent_email.replace('@', '_at_').replace('.', '_dot_')}"
    
    # Call SPIRE Server API
    entry = {
        "parent_id": {"trust_domain": "agentvault.com", "path": "/spire/agent/default"},
        "spiffe_id": {"trust_domain": "agentvault.com", "path": f"/agent/{agent_email}"},
        "selectors": [
            {"type": "docker", "value": f"label:agent-did:{agent_did}"}
        ],
        "ttl": 300  # 5 minutes for JWT-SVIDs
    }
    
    await spire_api.create_entry(entry)
```

## Authorization with OPA

### Policy Architecture

Open Policy Agent provides declarative, fine-grained authorization:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Service A     │────▶│  OPA Decision   │────▶│    Service B    │
│                 │     │     Point       │     │                 │
│ "Can I call B?" │     │ • Evaluate      │     │ "Allow/Deny"    │
└─────────────────┘     │   Policies      │     └─────────────────┘
                        │ • Return        │
                        │   Decision      │
                        └─────────────────┘
```

### Policy Language (Rego)

#### Service Access Control
```rego
package service.access

import future.keywords.if
import future.keywords.in

# Default deny
default allow = false

# Allow service-to-service calls based on SPIFFE ID
allow if {
    # Extract service names from SPIFFE IDs
    caller := parse_spiffe_id(input.caller_id)
    target := parse_spiffe_id(input.target_id)
    
    # Define allowed service interactions
    service_graph[caller.service][target.service]
}

# Service interaction graph
service_graph := {
    "registry-backend": {"teg-core", "federation-hub"},
    "teg-core": {"audit-logger"},
    "federation-hub": {"registry-backend"}
}

# Helper function to parse SPIFFE ID
parse_spiffe_id(spiffe_id) := parts if {
    parts := split(spiffe_id, "/")
}
```

#### Agent Authorization
```rego
package agent.access

# Agent can access their own data
allow if {
    input.method == "GET"
    input.path == ["agents", agent_id]
    input.subject == sprintf("spiffe://agentvault.com/agent/%s", [agent_id])
}

# Agent can update their own profile
allow if {
    input.method == "PUT"
    input.path == ["agents", agent_id]
    input.subject == sprintf("spiffe://agentvault.com/agent/%s", [agent_id])
}

# Rate limiting by reputation tier
rate_limit := limit if {
    reputation := data.agents[input.agent_id].reputation_score
    reputation >= 5000
    limit := 1000  # Master tier
} else := limit if {
    reputation := data.agents[input.agent_id].reputation_score
    reputation >= 1000
    limit := 500   # Expert tier
} else := 100      # Default limit
```

### Policy Evaluation Flow

```python
from typing import Dict, Any
import aiohttp

class OPAClient:
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
    
    async def evaluate_policy(
        self,
        policy_path: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate OPA policy with given input"""
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.opa_url}/v1/data/{policy_path}"
            
            async with session.post(url, json={"input": input_data}) as resp:
                result = await resp.json()
                
        return result["result"]

# Usage in service
async def authorize_request(request: Request) -> bool:
    opa = OPAClient()
    
    decision = await opa.evaluate_policy(
        "service/access/allow",
        {
            "caller_id": request.headers["X-SPIFFE-ID"],
            "target_id": "spiffe://agentvault.com/service/teg-core",
            "method": request.method,
            "path": request.path.split("/")
        }
    )
    
    return decision
```

## JWT-SVID Authentication Flow

### Complete Authentication Sequence

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Agent   │     │ Registry │     │  SPIRE   │     │   TEG    │
│          │     │ Backend  │     │  Agent   │     │   Core   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                 │                 │
     │ 1. Login       │                 │                 │
     │────────────────▶                 │                 │
     │                │                 │                 │
     │                │ 2. Request      │                 │
     │                │    JWT-SVID     │                 │
     │                │─────────────────▶                 │
     │                │                 │                 │
     │                │ 3. Return       │                 │
     │                │    JWT-SVID     │                 │
     │                ◀─────────────────│                 │
     │                │                 │                 │
     │                │ 4. Call TEG     │                 │
     │                │    with JWT     │                 │
     │                │─────────────────────────────────▶ │
     │                │                 │                 │
     │                │                 │     5. Validate │
     │                │                 │        JWT-SVID │
     │                │                 │                 │
     │                │     6. Return   │                 │
     │                │       Data      │                 │
     │                ◀─────────────────────────────────│ │
     │                │                 │                 │
     │ 7. Response    │                 │                 │
     ◀────────────────│                 │                 │
     │                │                 │                 │
```

### Implementation Details

#### Registry Backend - JWT-SVID Acquisition
```python
async def get_jwt_for_agent(agent_email: str, target_service: str) -> str:
    """Acquire JWT-SVID for agent to call target service"""
    
    # Construct agent SPIFFE ID
    agent_spiffe_id = email_to_spiffe_id(agent_email)
    
    # Request JWT-SVID from SPIRE
    with default_workload_api_client() as client:
        jwt_svids = client.fetch_jwt_svid(
            audiences=[f"spiffe://agentvault.com/service/{target_service}"],
            subject=agent_spiffe_id,
            ttl=300  # 5 minutes
        )
    
    return jwt_svids[0].token

@router.post("/api/v1/teg/token")
async def get_teg_token(
    current_user: User = Depends(get_current_user)
):
    """Bridge endpoint to get JWT-SVID for TEG access"""
    
    jwt_token = await get_jwt_for_agent(
        agent_email=current_user.email,
        target_service="teg-core"
    )
    
    return {
        "token": jwt_token,
        "expires_in": 300,
        "token_type": "Bearer"
    }
```

#### TEG Core - JWT-SVID Validation
```python
from pyspiffe.bundle.jwt_bundle.jwt_bundle_set import JwtBundleSet
from pyspiffe.svid.jwt_svid import JwtSvid
import jwt

class SPIFFEAuthenticator:
    def __init__(self):
        self.bundle_set = self._fetch_bundles()
        
    def _fetch_bundles(self) -> JwtBundleSet:
        """Fetch JWT bundles from SPIRE"""
        with default_workload_api_client() as client:
            return client.fetch_jwt_bundles()
    
    def verify_jwt_svid(self, token: str) -> Dict[str, Any]:
        """Verify JWT-SVID and extract claims"""
        
        # Get trust bundle for our domain
        bundle = self.bundle_set.get_bundle_for_trust_domain("agentvault.com")
        
        # Parse and validate JWT
        jwt_svid = bundle.parse_and_validate(
            token,
            expected_audience=["spiffe://agentvault.com/service/teg-core"]
        )
        
        # Extract agent identity from subject
        agent_id = extract_agent_from_spiffe_id(jwt_svid.subject)
        
        return {
            "agent_id": agent_id,
            "spiffe_id": jwt_svid.subject,
            "expiry": jwt_svid.expiry
        }

# FastAPI dependency
async def require_agent_auth(
    authorization: str = Header(...)
) -> str:
    """FastAPI dependency for agent authentication"""
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    
    token = authorization.split(" ", 1)[1]
    
    try:
        claims = authenticator.verify_jwt_svid(token)
        return claims["agent_id"]
    except Exception as e:
        raise HTTPException(401, f"Invalid JWT-SVID: {str(e)}")
```

## Security Patterns

### Defense in Depth

The Identity Fabric implements multiple security layers:

#### 1. Network Security
```yaml
# Docker network isolation
networks:
  identity-net:
    driver: bridge
    internal: true  # No external access
    
  service-net:
    driver: bridge
```

#### 2. Cryptographic Security
- **Private Key Protection**: Keys never leave SPIRE Agent
- **Certificate Pinning**: Services verify exact certificates
- **Perfect Forward Secrecy**: TLS 1.3 with ephemeral keys

#### 3. Operational Security
```python
# Audit logging
@router.middleware("http")
async def audit_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log authentication attempt
    logger.info({
        "event": "auth_attempt",
        "spiffe_id": request.headers.get("X-SPIFFE-ID"),
        "path": request.url.path,
        "method": request.method
    })
    
    response = await call_next(request)
    
    # Log result
    logger.info({
        "event": "auth_result",
        "spiffe_id": request.headers.get("X-SPIFFE-ID"),
        "status": response.status_code,
        "duration_ms": (time.time() - start_time) * 1000
    })
    
    return response
```

### Common Security Patterns

#### Service Mesh Integration
```python
# Envoy sidecar configuration for automatic mTLS
{
    "static_resources": {
        "clusters": [{
            "name": "spire_agent",
            "type": "STATIC",
            "connect_timeout": "1s",
            "http2_protocol_options": {},
            "load_assignment": {
                "cluster_name": "spire_agent",
                "endpoints": [{
                    "lb_endpoints": [{
                        "endpoint": {
                            "address": {
                                "pipe": {
                                    "path": "/opt/spire/sockets/agent.sock"
                                }
                            }
                        }
                    }]
                }]
            }
        }]
    }
}
```

#### Zero-Trust Verification
```python
def verify_service_identity(peer_cert: X509) -> bool:
    """Verify peer certificate against SPIFFE standards"""
    
    # Extract SPIFFE ID from SAN
    san_ext = peer_cert.extensions.get_extension_for_oid(
        ExtensionOID.SUBJECT_ALTERNATIVE_NAME
    )
    
    spiffe_ids = [
        name.value for name in san_ext.value
        if isinstance(name, UniformResourceIdentifier)
        and name.value.startswith("spiffe://")
    ]
    
    if not spiffe_ids:
        return False
    
    # Verify against expected identities
    return any(
        is_allowed_peer(spiffe_id) 
        for spiffe_id in spiffe_ids
    )
```

## Operational Procedures

### Initial Setup

```bash
# 1. Initialize SPIRE Server
docker-compose up -d spire-server

# 2. Get join token for agents
JOIN_TOKEN=$(docker exec agentvault-spire-server \
    spire-server token generate -spiffeID spiffe://agentvault.com/spire/agent/default)

# 3. Start SPIRE Agents with token
SPIRE_AGENT_JOIN_TOKEN=$JOIN_TOKEN docker-compose up -d spire-agent

# 4. Register workloads
./scripts/register-workloads.sh

# 5. Deploy OPA with policies
docker-compose up -d opa
```

### Monitoring & Observability

#### Health Checks
```python
@router.get("/health/identity")
async def identity_health():
    """Check identity fabric health"""
    
    checks = {
        "spire_agent": await check_spire_agent(),
        "svid_valid": await check_svid_validity(),
        "opa_responsive": await check_opa_health(),
        "bundle_fresh": await check_bundle_freshness()
    }
    
    return {
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks,
        "svid_expiry": get_svid_expiry(),
        "last_rotation": get_last_rotation_time()
    }
```

#### Metrics Collection
```python
# Prometheus metrics
auth_attempts = Counter(
    'identity_auth_attempts_total',
    'Total authentication attempts',
    ['service', 'result']
)

svid_rotations = Counter(
    'identity_svid_rotations_total',
    'Total SVID rotations',
    ['workload_type']
)

policy_evaluations = Histogram(
    'identity_policy_evaluation_duration_seconds',
    'OPA policy evaluation duration',
    ['policy', 'decision']
)
```

### Troubleshooting

#### Common Issues

1. **"Failed to fetch SVID"**
   ```bash
   # Check SPIRE Agent status
   docker exec agentvault-spire-agent \
       spire-agent healthcheck
   
   # Verify workload registration
   docker exec agentvault-spire-server \
       spire-server entry show -spiffeID $SPIFFE_ID
   ```

2. **"JWT-SVID validation failed"**
   ```bash
   # Check bundle synchronization
   curl http://localhost:8181/v1/data/bundles
   
   # Verify audience configuration
   echo $JWT_TOKEN | jwt decode -
   ```

3. **"OPA policy denied request"**
   ```bash
   # Test policy evaluation
   curl -X POST http://localhost:8181/v1/data/service/access/allow \
       -H "Content-Type: application/json" \
       -d '{"input": {...}}'
   ```

## Production Deployment

### High Availability Configuration

```yaml
# SPIRE Server HA with PostgreSQL backend
services:
  spire-server-1:
    environment:
      - SPIRE_SERVER_HA_ENABLED=true
      - SPIRE_SERVER_HA_BACKEND=postgres
      - SPIRE_SERVER_HA_BACKEND_CONNECTION_STRING=postgres://...
      
  spire-server-2:
    environment:
      - SPIRE_SERVER_HA_ENABLED=true
      - SPIRE_SERVER_HA_BACKEND=postgres
      - SPIRE_SERVER_HA_BACKEND_CONNECTION_STRING=postgres://...
```

### Security Hardening

1. **Hardware Security Module Integration**
   ```yaml
   plugins:
     KeyManager:
       - aws_kms:
           region: "us-east-1"
           key_id: "arn:aws:kms:..."
   ```

2. **Audit Logging**
   ```yaml
   server:
     audit_log_enabled: true
     audit_log_path: "/var/log/spire/audit.log"
     audit_log_format: "json"
   ```

3. **Rate Limiting**
   ```rego
   # OPA rate limiting policy
   rate_limit_exceeded if {
       count(requests_in_window) > max_requests
   }
   ```

## Future Enhancements

### Planned Features

1. **Multi-Region Federation**
   - Cross-region trust bundles
   - Geographic workload attestation
   - Latency-optimized routing

2. **Advanced Authorization**
   - Graph-based policy evaluation
   - ML-powered anomaly detection
   - Real-time policy updates

3. **Enhanced Observability**
   - Distributed tracing integration
   - Security posture dashboard
   - Automated compliance reporting

---

The Identity Fabric provides the cryptographic foundation for the Sovereign Stack, ensuring that every interaction is authenticated, authorized, and auditable. In a world of autonomous agents, identity isn't just important - it's everything.
