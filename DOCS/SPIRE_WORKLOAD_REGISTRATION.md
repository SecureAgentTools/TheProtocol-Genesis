# SPIRE Workload Registration Guide

This guide documents the process of registering SPIRE workloads for the AgentVault Registry federation system.

## Prerequisites

1. SPIRE server and agent must be running
2. Docker containers must have proper labels (`com.agentvault.service`)
3. SPIRE agent must be attested with a join token

## Step 1: Check SPIRE Agent Status

First, verify that the SPIRE agent is properly attested:

```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server agent list
```

You should see output like:
```
Found 3 attested agents:
SPIFFE ID         : spiffe://agentvault.com/spire/agent/join_token/8a9b7a0e-0da7-48d0-967b-db367610c49b
Attestation type  : join_token
Expiration time   : 2025-07-06 18:07:39 +0000 UTC
Serial number     : 313851442361433147587353690473723381433
Can re-attest     : false
```

## Step 2: Register Registry Workloads

Use the most recent agent's SPIFFE ID (check expiration dates) as the parent ID for workload registration.

### Register Registry A:
```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://agentvault.com/registry-a \
  -parentID spiffe://agentvault.com/spire/agent/join_token/8a9b7a0e-0da7-48d0-967b-db367610c49b \
  -selector docker:label:com.agentvault.service:registry-a
```

### Register Registry B:
```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://agentvault.com/registry-b \
  -parentID spiffe://agentvault.com/spire/agent/join_token/8a9b7a0e-0da7-48d0-967b-db367610c49b \
  -selector docker:label:com.agentvault.service:registry-b
```

## Step 3: Verify Registration

Check that the entries were created successfully:

```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show -selector docker:label:com.agentvault.service:registry-a
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show -selector docker:label:com.agentvault.service:registry-b
```

## Step 4: Verify SVID Issuance

Check the SPIRE server logs to confirm SVIDs are being issued:

```bash
docker logs agentvault-spire-server --tail 20
```

You should see entries like:
```
level=debug msg="Signed X509 SVID" ... spiffe_id="spiffe://agentvault.com/registry-a"
level=debug msg="Signed X509 SVID" ... spiffe_id="spiffe://agentvault.com/registry-b"
```

## Important Notes

1. **Join Token Expiration**: The SPIRE agent uses join tokens that expire. You may need to re-attest the agent with a new token periodically.

2. **Parent ID**: Always use the current agent's SPIFFE ID as the parent ID. Don't use expired agent IDs.

3. **Docker Labels**: The registries must have the correct Docker labels set in docker-compose.yml:
   ```yaml
   labels:
     - "com.agentvault.service=registry-a"  # or registry-b
   ```

4. **Socket Mount**: Both registries must have the SPIRE agent socket mounted:
   ```yaml
   volumes:
     - spire-agent-socket:/opt/spire/sockets:ro
   ```

## Troubleshooting

If workloads aren't getting SVIDs:

1. Check that containers have the correct labels:
   ```bash
   docker inspect agentvault_registry_a | grep -A 5 Labels
   ```

2. Verify socket is mounted:
   ```bash
   docker exec agentvault_registry_a ls -la /opt/spire/sockets/
   ```

3. Check SPIRE agent logs:
   ```bash
   docker logs agentvault-spire-agent --tail 50
   ```

4. List all registered entries:
   ```bash
   docker exec agentvault-spire-server /opt/spire/bin/spire-server entry list
   ```

## Federation Testing

After registering workloads, the federation endpoints should work:
- Public endpoints (like `/api/v1/api/v1/federation/info`) are accessible without authentication
- mTLS endpoints will use the issued SVIDs for authentication
- The peer list endpoint requires authentication (401 without proper credentials is expected)
