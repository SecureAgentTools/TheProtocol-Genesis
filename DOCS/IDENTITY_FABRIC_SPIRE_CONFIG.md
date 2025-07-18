# Identity Fabric - SPIFFE/SPIRE Configuration Guide

## Overview

This guide provides detailed configuration and operational procedures for the SPIFFE/SPIRE components of the AgentVault Identity Fabric.

## Quick Start

### Development Setup

```bash
# Clone the repository
cd identity-fabric/

# Initialize SPIRE (automated setup)
make init

# Start all services
make up

# Check status
make status

# View workload logs
make workload-logs
```

### Production Setup

```bash
# Generate production CA
./scripts/generate-production-ca.sh

# Deploy SPIRE Server
kubectl apply -f k8s/spire-server/

# Deploy SPIRE Agents
kubectl apply -f k8s/spire-agent/

# Verify deployment
kubectl get pods -n spire-system
```

## SPIRE Server Configuration

### Basic Configuration

```hocon
server {
    # Core settings
    bind_address = "0.0.0.0"
    bind_port = "8081"
    socket_path = "/opt/spire/data/registration.sock"
    trust_domain = "agentvault.com"
    data_dir = "/opt/spire/data"
    
    # Logging
    log_level = "INFO"
    log_format = "json"
    
    # Federation (if needed)
    federation {
        bundle_endpoint {
            address = "0.0.0.0"
            port = 8443
        }
    }
}

# Data store configuration
plugins {
    DataStore "sql" {
        plugin_data {
            database_type = "sqlite3"
            connection_string = "/opt/spire/data/datastore.sqlite3"
        }
    }
    
    # Node attestor
    NodeAttestor "join_token" {
        plugin_data {}
    }
    
    # Key manager
    KeyManager "disk" {
        plugin_data {
            keys_path = "/opt/spire/data/keys.json"
        }
    }
    
    # CA configuration
    UpstreamAuthority "disk" {
        plugin_data {
            key_file_path = "/opt/spire/conf/ca.key"
            cert_file_path = "/opt/spire/conf/ca.crt"
        }
    }
}
```

### Production Configuration

```hocon
server {
    bind_address = "0.0.0.0"
    bind_port = "8081"
    trust_domain = "agentvault.com"
    data_dir = "/opt/spire/data"
    
    # Production settings
    log_level = "WARN"
    log_format = "json"
    
    # Aggressive rotation for security
    ca_ttl = "24h"
    default_x509_svid_ttl = "1h"
    default_jwt_svid_ttl = "5m"
    
    # Rate limiting
    ratelimit {
        attestation = true
        signing = true
    }
}

plugins {
    # PostgreSQL for HA
    DataStore "sql" {
        plugin_data {
            database_type = "postgres"
            connection_string = "postgresql://spire:password@postgres:5432/spire"
        }
    }
    
    # Cloud-specific node attestors
    NodeAttestor "aws_iid" {
        plugin_data {
            access_key_id = "${AWS_ACCESS_KEY_ID}"
            secret_access_key = "${AWS_SECRET_ACCESS_KEY}"
            skip_block_device = true
        }
    }
    
    # HSM-based key manager
    KeyManager "aws_kms" {
        plugin_data {
            region = "us-east-1"
            key_policy_file = "/opt/spire/conf/key-policy.json"
        }
    }
    
    # Real CA integration
    UpstreamAuthority "aws_pca" {
        plugin_data {
            region = "us-east-1"
            certificate_authority_arn = "arn:aws:acm-pca:..."
        }
    }
}
```

## SPIRE Agent Configuration

### Basic Configuration

```hocon
agent {
    data_dir = "/opt/spire/data"
    log_level = "INFO"
    server_address = "spire-server"
    server_port = "8081"
    socket_path = "/opt/spire/sockets/agent.sock"
    trust_bundle_path = "/opt/spire/conf/bundle.crt"
    trust_domain = "agentvault.com"
}

plugins {
    # Node attestor matching server
    NodeAttestor "join_token" {
        plugin_data {}
    }
    
    # Key manager
    KeyManager "memory" {
        plugin_data {}
    }
    
    # Workload attestors
    WorkloadAttestor "unix" {
        plugin_data {}
    }
    
    WorkloadAttestor "docker" {
        plugin_data {
            docker_socket_path = "/var/run/docker.sock"
        }
    }
}
```

### Kubernetes Configuration

```hocon
agent {
    data_dir = "/opt/spire/data"
    log_level = "INFO"
    server_address = "spire-server.spire-system"
    server_port = "8081"
    socket_path = "/opt/spire/sockets/agent.sock"
    trust_domain = "agentvault.com"
}

plugins {
    # Kubernetes node attestor
    NodeAttestor "k8s_psat" {
        plugin_data {
            cluster = "production"
        }
    }
    
    # Kubernetes workload attestor
    WorkloadAttestor "k8s" {
        plugin_data {
            skip_kubelet_verification = true
            node_name_env = "NODE_NAME"
        }
    }
}
```

## Registration Entries

### Service Registration

```bash
# Register Registry Backend
spire-server entry create \
    -parentID spiffe://agentvault.com/spire-agent \
    -spiffeID spiffe://agentvault.com/service/registry-backend \
    -selector docker:label:com.agentvault.service:registry-backend \
    -selector docker:label:version:2.0.0 \
    -ttl 3600 \
    -jwtSVIDTTL 300 \
    -admin \
    -downstream

# Register TEG Core Service
spire-server entry create \
    -parentID spiffe://agentvault.com/spire-agent \
    -spiffeID spiffe://agentvault.com/service/teg-core \
    -selector docker:label:com.agentvault.service:teg-core \
    -ttl 3600 \
    -jwtSVIDTTL 300

# Register OPA Service
spire-server entry create \
    -parentID spiffe://agentvault.com/spire-agent \
    -spiffeID spiffe://agentvault.com/service/opa \
    -selector docker:label:com.agentvault.service:opa \
    -ttl 3600
```

### Agent Registration Pattern

```bash
# Register agent with specific ID
spire-server entry create \
    -parentID spiffe://agentvault.com/service/registry-backend \
    -spiffeID spiffe://agentvault.com/agent/user_at_example_dot_com \
    -selector k8s:pod-label:agent-id:user_at_example_dot_com \
    -ttl 3600 \
    -jwtSVIDTTL 300

# Register agent type pattern
spire-server entry create \
    -parentID spiffe://agentvault.com/spire-agent \
    -spiffeID spiffe://agentvault.com/agent/executor/compute \
    -selector docker:label:agent.type:compute \
    -selector docker:env:AGENT_TYPE:compute \
    -ttl 3600
```

### Batch Registration

```bash
#!/bin/bash
# batch-register.sh

# Read from CSV: agent_id,selector_type,selector_value
while IFS=',' read -r agent_id selector_type selector_value; do
    spire-server entry create \
        -parentID spiffe://agentvault.com/spire-agent \
        -spiffeID "spiffe://agentvault.com/agent/${agent_id}" \
        -selector "${selector_type}:${selector_value}" \
        -ttl 3600 \
        -jwtSVIDTTL 300
done < agents.csv
```

## Operational Procedures

### Health Monitoring

```bash
#!/bin/bash
# health-check.sh

# Check SPIRE Server
SPIRE_SERVER_HEALTH=$(curl -s http://localhost:8080/ready)
if [ "$SPIRE_SERVER_HEALTH" != "1" ]; then
    echo "ALERT: SPIRE Server unhealthy"
    exit 1
fi

# Check SPIRE Agent
SPIRE_AGENT_HEALTH=$(curl -s http://localhost:8082/ready)
if [ "$SPIRE_AGENT_HEALTH" != "1" ]; then
    echo "ALERT: SPIRE Agent unhealthy"
    exit 1
fi

# Check registration count
REG_COUNT=$(spire-server entry count)
if [ "$REG_COUNT" -lt 10 ]; then
    echo "WARNING: Low registration count: $REG_COUNT"
fi
```

### Certificate Rotation

```bash
# Force rotation of specific SVID
spire-server entry update \
    -entryID <entry-id> \
    -ttl 60  # Short TTL forces rotation

# Monitor rotation events
spire-server healthcheck --shallow | grep svid_rotation

# Verify workload picked up new SVID
spire-agent api fetch x509 \
    -spiffeID spiffe://agentvault.com/service/teg-core \
    -write /tmp/
openssl x509 -in /tmp/svid.0.pem -text -noout | grep "Not After"
```

### Backup and Recovery

```bash
#!/bin/bash
# backup-spire.sh

# Backup registration entries
spire-server entry show -format json > entries-backup.json

# Backup bundle
spire-server bundle show -format json > bundle-backup.json

# Backup datastore (SQLite)
sqlite3 /opt/spire/data/datastore.sqlite3 ".backup '/backup/spire-backup.db'"

# Backup keys (if using disk key manager)
tar -czf keys-backup.tar.gz /opt/spire/data/keys.json
```

```bash
#!/bin/bash
# restore-spire.sh

# Restore datastore
cp /backup/spire-backup.db /opt/spire/data/datastore.sqlite3

# Restore keys
tar -xzf keys-backup.tar.gz -C /

# Restart SPIRE Server
systemctl restart spire-server

# Verify entries restored
spire-server entry count
```

### Troubleshooting

#### Common Issues

1. **Agent Can't Connect to Server**
```bash
# Check network connectivity
nc -zv spire-server 8081

# Verify trust bundle
openssl x509 -in /opt/spire/conf/bundle.crt -text -noout

# Check agent logs
journalctl -u spire-agent -f
```

2. **Workload Can't Fetch SVID**
```bash
# Verify socket exists
ls -la /opt/spire/sockets/agent.sock

# Check workload attestation
spire-agent api list

# Test attestation manually
spire-agent api fetch x509 -socketPath /opt/spire/sockets/agent.sock
```

3. **Registration Not Working**
```bash
# List all entries
spire-server entry show

# Check selectors on running container
docker inspect <container> | jq '.[0].Config.Labels'

# Enable debug logging
spire-server run -config server.conf -logLevel DEBUG
```

### Performance Tuning

```hocon
# High-performance server config
server {
    # ... base config ...
    
    # Performance settings
    experimental {
        # Cache registration entries
        cache_reload_interval = "5s"
        
        # Prune old entries
        events_based_cache = true
    }
}

plugins {
    DataStore "sql" {
        plugin_data {
            database_type = "postgres"
            connection_string = "..."
            
            # Connection pooling
            max_open_conns = 100
            max_idle_conns = 50
            conn_max_lifetime = "30m"
        }
    }
}
```

## Security Hardening

### Production Security Checklist

- [ ] Use proper CA (not self-signed)
- [ ] Enable rate limiting
- [ ] Implement strict selectors
- [ ] Regular security audits
- [ ] Monitor for anomalies
- [ ] Implement key rotation
- [ ] Use HSM for key storage
- [ ] Enable audit logging
- [ ] Implement network policies
- [ ] Regular penetration testing

### Audit Logging

```hocon
# Enable comprehensive audit logging
server {
    audit_log_enabled = true
    audit_log_path = "/var/log/spire/audit.log"
    
    # Include these events
    audit_log_events = [
        "entry_create",
        "entry_update", 
        "entry_delete",
        "svid_issued",
        "bundle_updated"
    ]
}
```

### Network Policies

```yaml
# Kubernetes NetworkPolicy for SPIRE
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: spire-server
spec:
  podSelector:
    matchLabels:
      app: spire-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: spire-agent
    ports:
    - protocol: TCP
      port: 8081
```

## Integration Examples

### Python Workload

```python
import time
from pyspiffe.workloadapi import default_workload_api_client
from pyspiffe.bundle import JwtBundleStore
from pyspiffe.svid import JwtSvid

class SPIFFEWorkload:
    def __init__(self):
        self.client = default_workload_api_client()
        self._refresh_svids()
        
    def _refresh_svids(self):
        """Fetch fresh SVIDs"""
        # X.509 SVID for mTLS
        self.x509_context = self.client.fetch_x509_context()
        
        # JWT bundle for validation
        self.jwt_bundle = self.client.fetch_jwt_bundles()
        
    def get_jwt_token(self, audience: str) -> str:
        """Get JWT-SVID for API calls"""
        jwt_svids = self.client.fetch_jwt_svid(audiences=[audience])
        return jwt_svids[0].token
        
    def validate_jwt_token(self, token: str, audience: str) -> JwtSvid:
        """Validate incoming JWT-SVID"""
        jwt_svid = JwtSvid.parse(token, self.jwt_bundle, audience)
        return jwt_svid
```

### Go Workload

```go
package main

import (
    "context"
    "log"
    "time"
    
    "github.com/spiffe/go-spiffe/v2/workloadapi"
    "github.com/spiffe/go-spiffe/v2/svid/jwtsvid"
)

type SPIFFEWorkload struct {
    client *workloadapi.Client
}

func NewSPIFFEWorkload(ctx context.Context) (*SPIFFEWorkload, error) {
    client, err := workloadapi.New(ctx)
    if err != nil {
        return nil, err
    }
    
    return &SPIFFEWorkload{client: client}, nil
}

func (w *SPIFFEWorkload) GetJWTToken(ctx context.Context, audience string) (string, error) {
    svid, err := w.client.FetchJWTSVID(ctx, jwtsvid.Params{
        Audience: audience,
    })
    if err != nil {
        return "", err
    }
    
    return svid.Marshal(), nil
}
```

## Monitoring & Metrics

### Prometheus Metrics

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'spire-server'
    static_configs:
      - targets: ['spire-server:9988']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'spire_server_.*'
        action: keep
        
  - job_name: 'spire-agent'
    static_configs:
      - targets: ['spire-agent:9988']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'spire_agent_.*'
        action: keep
```

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `spire_server_svid_issued_total` | SVIDs issued | Rate > 1000/min |
| `spire_server_registration_entry_count` | Active registrations | Count < 10 |
| `spire_agent_svid_renewed_total` | SVID renewals | Rate = 0 for 30min |
| `spire_agent_workload_api_connections` | Active connections | Count > 1000 |

## Disaster Recovery

### Backup Strategy

1. **Daily Backups**
   - Registration entries
   - Trust bundles
   - Database snapshots

2. **Real-time Replication**
   - PostgreSQL streaming replication
   - Multi-region bundle sync

3. **Recovery Testing**
   - Monthly DR drills
   - Automated recovery validation

### Recovery Procedures

```bash
#!/bin/bash
# disaster-recovery.sh

# 1. Deploy new SPIRE Server
kubectl apply -f spire-server-dr.yaml

# 2. Restore database
pg_restore -h new-server -d spire /backup/spire.dump

# 3. Verify entries
spire-server entry count

# 4. Update agent configurations
kubectl set env daemonset/spire-agent \
    SPIRE_SERVER_ADDR=new-server:8081

# 5. Verify workload connectivity
kubectl exec workload -- spiffe-fetch
```

## Best Practices

1. **Use Specific Selectors**
   ```bash
   # Good: Multiple selectors
   -selector docker:label:app:teg \
   -selector docker:label:version:2.0.0 \
   -selector docker:env:DEPLOYMENT:production
   
   # Bad: Too generic
   -selector docker:label:app:agentvault
   ```

2. **Implement Least Privilege**
   ```bash
   # Service-specific permissions
   -spiffeID spiffe://agentvault.com/service/teg-core/read-only
   -spiffeID spiffe://agentvault.com/service/teg-core/admin
   ```

3. **Regular Rotation**
   - X.509: 1-hour TTL
   - JWT: 5-minute TTL
   - Keys: 90-day rotation

4. **Monitor Everything**
   - SVID issuance/renewal
   - Failed attestations
   - Registration changes
   - Bundle updates

5. **Automate Operations**
   - Registration via CI/CD
   - Automated backups
   - Self-healing with operators