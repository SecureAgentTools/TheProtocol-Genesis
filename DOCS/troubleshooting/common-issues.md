# Common Issues and Troubleshooting

This guide covers the most common issues you might encounter with The Protocol and how to resolve them.

## Quick Diagnostic Commands

Before diving into specific issues, run these commands to gather diagnostic information:

```bash
# Check all services status
docker compose ps

# View recent logs
docker compose logs --tail=100

# Check system resources
docker stats --no-stream

# Test registry health
curl http://localhost:8000/health
```

## Installation Issues

### Docker Compose Version Error
**Symptom**: `docker compose` command not found or version error

**Solution**:
```bash
# Update Docker Compose
docker-compose --version  # Old syntax
docker compose version    # New syntax (v2+)

# If using old version, update Docker Desktop or install standalone
# For Linux:
sudo apt-get update && sudo apt-get install docker-compose-plugin
```

### Port Already in Use
**Symptom**: `bind: address already in use`

**Solution**:
```bash
# Find what's using the port
lsof -i :8000
# or
netstat -tulpn | grep 8000

# Stop the conflicting service or change ports in docker-compose.yml
```

## Registry Issues

### Registry Won't Start
**Symptom**: Registry container exits immediately

**Diagnosis**:
```bash
docker compose logs registry | tail -50
```

**Common Solutions**:

1. **Database not ready**:
```bash
docker compose restart postgres
sleep 10
docker compose restart registry
```

2. **Invalid configuration**:
```bash
# Check environment variables
docker compose config

# Verify .env file
cat .env
```

3. **Corrupted state**:
```bash
# Full reset (WARNING: loses data)
docker compose down -v
docker compose up -d
```

### Cannot Access Registry UI
**Symptom**: Browser shows connection refused

**Solutions**:

1. **Check if running**:
```bash
curl http://localhost:8000
docker compose ps registry
```

2. **Firewall blocking**:
```bash
# Windows
netsh advfirewall firewall show rule name=all | findstr 8000

# Linux
sudo ufw status
sudo iptables -L -n | grep 8000
```

3. **Docker network issue**:
```bash
docker network ls
docker network inspect agentvault2_default
```

## Authentication Issues

### Invalid Token Error
**Symptom**: `401 Unauthorized` responses

**Solutions**:

1. **Generate new bootstrap token**:
```bash
cd D:\Agentvault2
make generate-bootstrap-token
```

2. **Check token format**:
```bash
# Should be: Bearer btok_... or Bearer avreg_...
echo $AUTH_TOKEN
```

3. **Verify token with API**:
```bash
curl http://localhost:8000/api/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Cannot Create API Key
**Symptom**: API key creation fails

**Solution**:
```bash
# Use bootstrap token first
BTOK=$(make generate-bootstrap-token | grep "Bootstrap token:" | cut -d' ' -f3)

# Create API key
curl -X POST http://localhost:8000/api/apikeys \
  -H "Authorization: Bearer $BTOK" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "description": "Test key"}'
```

## Agent Issues

### Agent Registration Fails
**Symptom**: Cannot register new agent

**Common Causes & Solutions**:

1. **Invalid agent endpoint**:
```bash
# Test agent is reachable
curl http://agent-host:8080/health

# For Docker agents, use proper networking
# Wrong: localhost:8080
# Right: host.docker.internal:8080 (Docker Desktop)
# Right: container-name:8080 (same network)
```

2. **Missing required fields**:
```json
{
  "name": "required",
  "version": "required", 
  "capabilities": ["required"],
  "endpoint": "required"
}
```

3. **Name already taken**:
```bash
# Check existing agents
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Agent Not Responding
**Symptom**: Agent registered but not processing requests

**Diagnosis**:
```bash
# Check agent logs
docker logs agent-container-name

# Test agent directly
curl http://agent-endpoint/health

# Check network connectivity
docker exec registry ping agent-hostname
```

## TEG Layer Issues

### Balance Not Updating
**Symptom**: Token transfers don't reflect in balance

**Solutions**:

1. **Check transaction status**:
```bash
curl http://localhost:8000/api/teg/transactions/AGENT_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Verify TEG service**:
```bash
docker compose logs teg
docker compose restart teg
```

### Staking Fails
**Symptom**: Cannot stake tokens

**Common Causes**:

1. **Insufficient balance**:
```bash
# Check balance first
curl http://localhost:8000/api/teg/balance/AGENT_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Invalid duration**:
```json
{
  "agent_id": "agt_123",
  "amount": 1000,
  "duration_days": 30  // Must be positive integer
}
```

## Federation Issues

### Cannot Connect to Peer Registry
**Symptom**: Federation sync fails

**Solutions**:

1. **Verify peer is reachable**:
```bash
curl https://peer-registry.com/health
```

2. **Check federation config**:
```bash
# View current peers
curl http://localhost:8000/api/federation/peers \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Update API keys** (as provided):
```bash
# Registry A
export API_KEY_A="avreg_eJx7JyZWspw29zO8A_EcsMDsA6_lrL7O6eFwzGaIG6I"

# Registry B  
export API_KEY_B="avreg_d2yxb_VO1L9IieWEr4SF6oogMrOdNu2P7T3K5dKOcHk"
```

## Performance Issues

### Slow Response Times
**Symptom**: API calls taking >5 seconds

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Database performance
docker compose exec postgres \
  psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Connection pool status
docker compose logs registry | grep "connection"
```

**Solutions**:

1. **Increase resources**:
```yaml
# docker-compose.yml
services:
  registry:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

2. **Database optimization**:
```bash
# Vacuum and analyze
docker compose exec postgres \
  psql -U postgres -d agentvault -c "VACUUM ANALYZE;"
```

## Data Issues

### Database Connection Lost
**Symptom**: `FATAL: connection to database failed`

**Solution**:
```bash
# Restart database
docker compose restart postgres

# Check database logs
docker compose logs postgres

# Verify connection
docker compose exec postgres pg_isready
```

### Data Corruption
**Symptom**: Inconsistent data or errors

**Recovery Steps**:
```bash
# 1. Stop services
docker compose stop

# 2. Backup current state
docker compose exec postgres \
  pg_dump -U postgres agentvault > backup_$(date +%Y%m%d).sql

# 3. Check database integrity
docker compose exec postgres \
  psql -U postgres -d agentvault -c "REINDEX DATABASE agentvault;"

# 4. Restart services
docker compose up -d
```

## Debugging Tools

### Enable Debug Logging
```bash
# Set in .env or docker-compose.yml
LOG_LEVEL=DEBUG

# Restart to apply
docker compose restart registry
```

### Trace Requests
```bash
# Use curl verbose mode
curl -v http://localhost:8000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check request in logs
docker compose logs registry | grep -A5 -B5 "REQUEST_ID"
```

### Generate Full Diagnostic Report
Create `diagnostic.sh`:
```bash
#!/bin/bash
echo "=== Protocol Diagnostic Report ===" > diagnostic.txt
echo "Date: $(date)" >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Service Status ===" >> diagnostic.txt
docker compose ps >> diagnostic.txt

echo -e "\n=== Recent Logs ===" >> diagnostic.txt
docker compose logs --tail=50 >> diagnostic.txt

echo -e "\n=== Resource Usage ===" >> diagnostic.txt
docker stats --no-stream >> diagnostic.txt

echo -e "\n=== Network ===" >> diagnostic.txt
docker network ls >> diagnostic.txt

echo "Report saved to diagnostic.txt"
```

## Getting Help

If these solutions don't resolve your issue:

1. **Collect diagnostics**:
   - Run the diagnostic script above
   - Note the exact error messages
   - Include your docker-compose.yml (remove secrets)

2. **Check resources**:
   - [GitHub Issues](https://github.com/agentvault/protocol/issues)
   - [Documentation](../index.md)
   - [All Documentation](../index.md)

3. **Report the issue**:
   - Use the issue template
   - Include diagnostic output
   - Describe what you were trying to do

---

*"Every error is a teacher in disguise. Learn its lesson, and grow stronger."*
- The Warrior Owl Doctrine
