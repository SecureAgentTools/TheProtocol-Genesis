# SPIRE Quick Reference

## Common SPIRE Commands for AgentVault Federation

### Agent Management
```bash
# List all attested agents
docker exec agentvault-spire-server /opt/spire/bin/spire-server agent list

# Show specific agent details
docker exec agentvault-spire-server /opt/spire/bin/spire-server agent show -spiffeID <AGENT_SPIFFE_ID>
```

### Workload Registration
```bash
# Register Registry A (replace PARENT_ID with current agent ID)
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://agentvault.com/registry-a \
  -parentID spiffe://agentvault.com/spire/agent/join_token/YOUR_TOKEN_HERE \
  -selector docker:label:com.agentvault.service:registry-a

# Register Registry B
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://agentvault.com/registry-b \
  -parentID spiffe://agentvault.com/spire/agent/join_token/YOUR_TOKEN_HERE \
  -selector docker:label:com.agentvault.service:registry-b
```

### Entry Management
```bash
# List all entries
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry list

# Show entries by selector
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show -selector docker:label:com.agentvault.service:registry-a

# Delete an entry
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry delete -entryID <ENTRY_ID>
```

### Health Checks
```bash
# SPIRE Server health
docker exec agentvault-spire-server /opt/spire/bin/spire-server healthcheck

# SPIRE Agent health (may show "unhealthy" but check socket instead)
docker exec agentvault-spire-agent /opt/spire/bin/spire-agent healthcheck

# Check agent socket
docker exec agentvault-spire-agent ls -la /opt/spire/sockets/agent.sock
```

### SVID Operations
```bash
# Fetch X.509 SVID from agent
docker exec agentvault-spire-agent /opt/spire/bin/spire-agent api fetch x509 -socketPath /opt/spire/sockets/agent.sock

# Check if registry can access socket
docker exec agentvault_registry_a ls -la /opt/spire/sockets/agent.sock
```

### Debugging
```bash
# View SPIRE Server logs
docker logs agentvault-spire-server --tail 50

# View SPIRE Agent logs  
docker logs agentvault-spire-agent --tail 50

# Check container labels
docker inspect agentvault_registry_a | grep -A 10 Labels
```

## Quick Setup After Fresh Deploy

1. Get current agent ID:
   ```bash
   docker exec agentvault-spire-server /opt/spire/bin/spire-server agent list | grep -A 3 "SPIFFE ID"
   ```

2. Use the most recent (check expiration) agent ID to register both registries

3. Verify with:
   ```bash
   docker exec agentvault-spire-server /opt/spire/bin/spire-server entry list
   ```
