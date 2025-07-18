# Running the Stack

This guide covers operating the unified Sovereign Stack services in your development environment.

## Service Architecture

The Sovereign Stack consists of multiple integrated services:

```
┌─────────────────────┐     ┌─────────────────────┐
│   Registry A & B    │────▶│   TEG Layer API     │
│   (8000, 8001)      │     │   (Port 8100)       │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           │      ┌─────────────────────┐
           └─────▶│  Identity Fabric    │
                  │  SPIRE (8281)       │
                  │  OPA (8288)         │
                  └─────────────────────┘
```

## Starting the Entire Stack

### Quick Start (One Command)

From the project root directory:

```bash
docker compose up -d
```

This single command will:
- Start both Registry instances (A and B) with their databases
- Launch the TEG Layer service
- Initialize the Identity Fabric (SPIRE Server, Agent, OPA)
- Create all necessary networks and volumes
- Apply database migrations automatically

### Verify All Services Are Running

```bash
# Check all containers
docker compose ps

# Quick health check of all services
curl http://localhost:8000/health      # Registry A
curl http://localhost:8001/health      # Registry B
curl http://localhost:8100/health      # TEG Layer
curl http://localhost:8281/health      # SPIRE Server
curl http://localhost:8288/health      # OPA
```

### Service Port Mapping

| Service | External Port | Internal Port | Purpose |
|---------|--------------|---------------|----------|
| Registry A | 8000 | 8000 | Primary Registry Instance |
| Registry B | 8001 | 8000 | Secondary Registry Instance |
| TEG Layer | 8100 | 8080 | Token Economy Governance |
| SPIRE Server | 8281 | 8081 | Identity Management |
| OPA | 8288 | 8181 | Policy Engine |
| PostgreSQL A | 5433 | 5432 | Registry A Database |
| PostgreSQL B | 5434 | 5432 | Registry B Database |

## Managing the Stack

### Common Commands

```bash
# Start all services
docker compose up -d

# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f registry-a
docker compose logs -f teg-layer

# Stop all services
docker compose down

# Stop and remove all data (careful!)
docker compose down -v

# Restart a specific service
docker compose restart teg-layer

# Check service status
docker compose ps
```

## Service Health Monitoring

### Health Check Endpoints

All services expose health endpoints for monitoring:

```bash
# Registry Health
curl http://localhost:8000/health
curl http://localhost:8001/health

# TEG Layer Health  
curl http://localhost:8100/api/v1/health

# SPIRE Server Health
curl http://localhost:8281/health

# OPA Health
curl http://localhost:8288/health
```

### Monitoring Script

Create `monitor-stack.sh`:

```bash
#!/bin/bash

echo "🔍 Checking Sovereign Stack Services..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check function
check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null; then
        echo -e "${GREEN}✓${NC} $name is healthy"
    else
        echo -e "${RED}✗${NC} $name is down"
    fi
}

# Check all services
check_service "Registry A" "http://localhost:8000/health"
check_service "Registry B" "http://localhost:8001/health"
check_service "TEG Layer API" "http://localhost:8100/api/v1/health"
check_service "SPIRE Server" "http://localhost:8281/health"
check_service "OPA Server" "http://localhost:8288/health"
```

Make it executable: `chmod +x monitor-stack.sh`

## Common Operations

### Database Management

#### Backup Registry Database
```bash
# Create backup
docker exec agentvault_registry_db_a pg_dump -U postgres agentvault_registry_a > registry_backup.sql

# Restore backup
docker exec -i agentvault_registry_db_a psql -U postgres agentvault_registry_a < registry_backup.sql
```

#### Run Database Migrations
```bash
cd agentvault_registry
alembic upgrade head  # Apply all migrations
alembic current      # Check current version
alembic history      # View migration history
```

### Token Management

#### Initialize TEG Treasury
```bash
cd agentvault_teg_layer_mvp
poetry run python scripts/issue_initial_tokens.py did:agentvault:teg_system_treasury 10000.0
```

#### Create Bootstrap Token
```bash
# Using CLI
agentvault_cli auth login --email admin@example.com
agentvault_cli onboard request-token --agent-type "research-agent"

# Using API
curl -X POST http://localhost:8000/api/v1/onboard/bootstrap/request-token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_type_hint": "research-agent"}'
```

### Identity Management

#### Register New Workload with SPIRE
```bash
# Register a workload
docker exec -it agentvault-spire-server \
  /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://agentvault.com/agent/my-agent \
  -parentID spiffe://agentvault.com/spire-agent \
  -selector docker:label:app:my-agent
```

#### Update OPA Policies
```bash
# Edit policy
vim identity-fabric/policies/agent_authorization.rego

# Policies auto-reload, check logs
docker logs agentvault-opa
```

## Logging and Debugging

### Enable Debug Mode

```bash
# Registry
LOG_LEVEL=DEBUG uvicorn agentvault_registry.main:app

# TEG Layer
LOG_LEVEL=DEBUG uvicorn teg_core_service.main:app

# View Docker logs with timestamps
docker compose logs -f --timestamps registry-a
```

### Common Issues and Solutions

#### Service Won't Start
```bash
# Check port availability
lsof -i :8000

# Check Docker resources
docker system df
docker system prune -a  # Clean up unused resources
```

#### Database Connection Failed
```bash
# Test PostgreSQL connection
docker exec -it agentvault_registry_db_a psql -U postgres -c "SELECT 1"

# Check network connectivity
docker network ls
docker network inspect agentvault-network
```

#### Identity Verification Failed
```bash
# Check SPIRE agent status
docker logs agentvault-spire-agent

# Verify workload registration
docker exec -it agentvault-spire-server \
  /opt/spire/bin/spire-server entry list
```

## Production Considerations

### Security Hardening

1. **Use Strong Secrets**
   ```bash
   # Generate secure keys
   openssl rand -hex 32  # For SECRET_KEY
   openssl rand -hex 64  # For JWT_SECRET_KEY
   ```

2. **Enable TLS**
   - Use reverse proxy (Nginx/Traefik) for TLS termination
   - Enable mTLS between services using SPIRE

3. **Network Isolation**
   - Use Docker networks to isolate services
   - Implement firewall rules

### Performance Tuning

1. **Database Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_agents_did ON agents(did);
   CREATE INDEX idx_transactions_created_at ON transactions(created_at);
   ```

2. **Service Scaling**
   ```yaml
   # docker-compose.override.yml
   services:
     registry:
       deploy:
         replicas: 3
   ```

## Maintenance Tasks

### Daily Operations
- Check service health endpoints
- Review error logs
- Monitor disk space

### Weekly Tasks
- Backup databases
- Review security logs
- Update dependencies (dev only)

## Next Steps

Now that you have the stack running:
- [Building an Agent](../developer-guides/building-an-agent.md) - Create your first agent
- [CLI Reference](../developer-guides/cli-reference.md) - Learn all CLI commands
- [Architecture Overview](../architecture/overview.md) - Deep dive into system design

---

*"The Warrior Owl maintains vigilant watch over its domain. Monitor your services as you would guard your nest."*
