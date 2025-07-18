# AgentVault Identity Fabric - Operations Guide

## 🎯 Purpose
This guide provides operational procedures for managing the AgentVault Identity Fabric in production.

## 🚀 Initial Setup

### Prerequisites
- Docker and Docker Compose installed
- Access to AgentVault repository
- Windows or Linux environment

### First Time Setup

1. **Clone and navigate to the project:**
   ```bash
   cd D:\Agentvault2
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d --force-recreate --build
   ```

3. **Initialize SPIRE Agent (after ~15 seconds):**
   ```bash
   .\fix_spire_simple.bat
   ```

4. **Verify setup:**
   ```bash
   .\check_spire_status.bat
   ```

## 📋 Daily Operations

### Health Monitoring

**Check component status:**
```bash
# SPIRE Server
docker exec agentvault-spire-server /opt/spire/bin/spire-server healthcheck

# View registered entries
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show

# Check agent logs
docker logs --tail 50 agentvault-spire-agent
```

**Monitor certificate renewals:**
```bash
# Look for "Renewing X509-SVID" messages
docker logs agentvault-spire-agent | grep "Renewing"
```

### Managing Workload Registrations

**Register a new service:**
```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry create \
    -parentID spiffe://agentvault.com/agent \
    -spiffeID spiffe://agentvault.com/service/new-service \
    -selector docker:label:com.agentvault.service:new-service \
    -ttl 3600
```

**List all registrations:**
```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show
```

**Delete a registration:**
```bash
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry delete \
    -entryID <ENTRY_ID>
```

## 🔧 Troubleshooting

### Common Issues

#### Agent Won't Start
**Symptom:** "no identity issued" or "join token was not provided"

**Solution:**
```bash
.\fix_spire_simple.bat
```

#### Services Can't Get Certificates
**Symptom:** Services report "permission denied" when accessing agent socket

**Check:**
1. Verify socket mount in docker-compose.yml:
   ```yaml
   volumes:
     - spire-agent-socket:/opt/spire/sockets:ro
   ```

2. Check if entry exists for the service:
   ```bash
   docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show | grep <service-name>
   ```

#### Certificate Renewal Issues
**Symptom:** "Failed to renew X509-SVID" in logs

**Actions:**
1. Check server connectivity
2. Verify entry hasn't expired
3. Restart agent if necessary

### Emergency Procedures

#### Complete Identity Fabric Reset
```bash
# Stop all services
docker-compose down

# Remove SPIRE data volumes
docker volume rm agentvault_spire_server_data agentvault_spire_agent_socket

# Restart everything
docker-compose up -d --force-recreate --build

# Re-initialize agent
.\fix_spire_simple.bat
```

#### Backup SPIRE Server Data
```bash
# Create backup
docker exec agentvault-spire-server tar -czf /tmp/spire-backup.tar.gz /opt/spire/data
docker cp agentvault-spire-server:/tmp/spire-backup.tar.gz ./spire-backup-$(date +%Y%m%d).tar.gz
```

## 🔐 Security Operations

### Rotate Join Tokens
Join tokens should be rotated periodically:

```bash
# Generate new token
docker exec agentvault-spire-server /opt/spire/bin/spire-server token generate \
    -spiffeID spiffe://agentvault.com/agent

# Update agent configuration and restart
.\fix_spire_simple.bat
```

### Audit Workload Identities
```bash
# Export all entries to JSON for audit
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show -output json > entries-audit.json
```

### Monitor for Anomalies
Watch for:
- Unexpected registration requests
- Failed attestations
- Certificate renewal failures
- Unusual SPIFFE ID patterns

## 📊 Metrics and Monitoring

### Key Metrics to Track
- SVID issuance rate
- Attestation success/failure ratio
- Certificate expiration times
- Agent health status

### Log Analysis
```bash
# Count successful attestations
docker logs agentvault-spire-agent | grep -c "Node attestation was successful"

# Find failed operations
docker logs agentvault-spire-server | grep -i error

# Monitor registration changes
docker logs agentvault-spire-server | grep "Entry created\|Entry deleted"
```

## 🔄 Maintenance Windows

### Monthly Tasks
1. Review and clean up unused registrations
2. Verify all services are getting certificates
3. Check for SPIRE updates
4. Backup server data

### Quarterly Tasks
1. Rotate infrastructure credentials
2. Review security policies
3. Update SPIRE components
4. Disaster recovery drill

## 📚 Additional Resources

- [SPIRE Quick Start Guide](./SPIRE_QUICK_START.md)
- [SPIRE Agent Token Solution](./SPIRE_AGENT_TOKEN_SOLUTION.md)
- [Identity Fabric Architecture](./IDENTITY_FABRIC.md)
- [OPA Policy Guide](./IDENTITY_FABRIC_OPA_POLICIES.md)

## 🆘 Support

For issues:
1. Check troubleshooting section above
2. Review agent and server logs
3. Consult SPIFFE/SPIRE documentation
4. Contact AgentVault team

---

*Remember: The Identity Fabric is the security foundation of AgentVault. Handle with care!* 🛡️
