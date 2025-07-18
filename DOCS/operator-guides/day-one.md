# Registry Operator Day 1 Guide

Welcome to The Protocol! This guide will walk you through your first day as a registry operator, from initial deployment to onboarding your first agent.

**Time to complete**: 30-45 minutes  
**Prerequisites**: Docker, Docker Compose, and basic command line knowledge

## Quick Start Checklist

- [ ] System requirements verified
- [ ] Docker and Docker Compose installed
- [ ] Ports 8000-8001 available
- [ ] API keys generated
- [ ] First agent onboarded
- [ ] Monitoring configured
- [ ] Backup strategy planned

## Step 1: Pre-Deployment Verification

### System Requirements
```bash
# Check Docker version (need 20.10+)
docker --version

# Check Docker Compose version (need 2.0+)
docker compose version

# Verify available ports
netstat -an | grep -E ":(8000|8001|5432|9000|9090)" || echo "Ports available"

# Check disk space (need at least 10GB)
df -h
```

### Clone the Repository
```bash
# Clone The Protocol
git clone https://github.com/agentvault/protocol.git D:\Agentvault2
cd D:\Agentvault2

# Verify structure
ls -la
```

## Step 2: Deploy Your Registry

### Option A: Quick Deploy (Recommended for Day 1)
```bash
# Start all services with one command
docker compose up -d --force-recreate --build

# Verify all services are running
docker compose ps

# Expected output:
# agentvault-registry       running   0.0.0.0:8000->8000/tcp
# agentvault-registry-b     running   0.0.0.0:8001->8001/tcp
# agentvault-postgres       running   5432/tcp
# agentvault-opa           running   8181/tcp
# agentvault-spire-server  running   8081/tcp
```

### Option B: Step-by-Step Deploy
```bash
# 1. Start infrastructure services first
docker compose up -d postgres opa spire-server

# 2. Wait for services to be healthy
sleep 10

# 3. Start registry services
docker compose up -d registry registry-b

# 4. Verify deployment
docker compose logs --tail=50 registry
```

## Step 3: Initial Configuration

### Generate Bootstrap Token
```bash
# Generate your first admin token
cd D:\Agentvault2
make generate-bootstrap-token

# Save the output! It looks like:
# Bootstrap token: btok_abcd1234...
```

### Access the Registry UI
1. Open http://localhost:8000 in your browser
2. You should see The Protocol Registry interface
3. The UI should show "Registry Status: Online"

### Create Your First API Key
```bash
# Using the CLI
python -m sovereign.main api-key create \
  --email admin@yourdomain.com \
  --password "SecurePassword123!" \
  --description "Admin API Key"

# Or using the UI
# 1. Navigate to http://localhost:8000/settings
# 2. Click "API Keys"
# 3. Click "Generate New Key"
```

## Step 4: Security Configuration

### Update Environment Variables
Create or update `.env` file:
```env
# Registry Configuration
REGISTRY_NAME="My Registry"
REGISTRY_URL="http://localhost:8000"
REGISTRY_ADMIN_EMAIL="admin@yourdomain.com"

# Security Settings
JWT_SECRET="generate-a-secure-random-string-here"
ENCRYPTION_KEY="another-secure-random-string"

# Database (if using external)
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/agentvault"

# Federation (optional)
ENABLE_FEDERATION=true
FEDERATION_TIMEOUT=30
```

### Set Up HTTPS (Production)
For production deployments, set up HTTPS using a reverse proxy:

```nginx
# Example Nginx configuration
server {
    listen 443 ssl http2;
    server_name registry.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 5: Onboard Your First Agent

### Using the Echo Agent (Quick Test)
```bash
# Deploy the included echo agent
cd D:\Agentvault2\echo_agent
docker build -t echo-agent .
docker run -d --name echo-agent -p 8080:8080 echo-agent

# Register it with your registry
curl -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer btok_YOUR_BOOTSTRAP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "echo-agent",
    "version": "1.0.0",
    "description": "Test echo agent",
    "capabilities": ["echo"],
    "endpoint": "http://host.docker.internal:8080"
  }'
```

### Verify Agent Registration
```bash
# List all agents
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer btok_YOUR_BOOTSTRAP_TOKEN"

# Should return your echo agent
```

## Step 6: Basic Monitoring Setup

### View Logs
```bash
# Real-time registry logs
docker compose logs -f registry

# Check for errors
docker compose logs registry | grep ERROR

# View agent activity
docker compose logs registry | grep "agent"
```

### Health Monitoring Script
Create `monitor-health.sh`:
```bash
#!/bin/bash
# Simple health monitoring script

REGISTRY_URL="http://localhost:8000"
ALERT_EMAIL="admin@yourdomain.com"

# Check registry health
HEALTH=$(curl -s $REGISTRY_URL/health | jq -r '.status')

if [ "$HEALTH" != "healthy" ]; then
    echo "Registry unhealthy! Status: $HEALTH"
    # Send alert (configure your mail command)
    # echo "Registry is down!" | mail -s "Registry Alert" $ALERT_EMAIL
fi

# Check database connection
DB_STATUS=$(docker compose exec postgres pg_isready)
if [ $? -ne 0 ]; then
    echo "Database connection failed!"
fi

# Check disk usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage high: $DISK_USAGE%"
fi
```

### Set Up Prometheus Metrics (Optional)
```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

## Step 7: Common Issues and Solutions

### Issue: Registry won't start
```bash
# Check logs
docker compose logs registry

# Common fixes:
# 1. Port already in use
lsof -i :8000  # Find what's using the port
# 2. Database not ready
docker compose restart postgres
sleep 10
docker compose restart registry
```

### Issue: Can't connect to registry
```bash
# Verify it's running
curl http://localhost:8000/health

# Check firewall
sudo ufw status  # Ubuntu/Debian
sudo firewall-cmd --list-all  # RHEL/CentOS

# Check Docker network
docker network ls
docker network inspect agentvault2_default
```

### Issue: Agent registration fails
```bash
# Verify token is valid
curl http://localhost:8000/api/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check agent endpoint is reachable
curl http://host.docker.internal:8080/health

# Review detailed error
docker compose logs registry | grep -A5 -B5 "ERROR"
```

### Issue: Database errors
```bash
# Check database status
docker compose exec postgres psql -U postgres -c "SELECT 1"

# Reset database (WARNING: destroys data)
docker compose down -v
docker compose up -d
```

## Step 8: Backup and Maintenance

### Daily Backup Script
Create `backup-registry.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/registry"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker compose exec -T postgres pg_dump -U postgres agentvault \
  > $BACKUP_DIR/agentvault_$DATE.sql

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/*_$DATE.*"
```

### Regular Maintenance Tasks
```bash
# Weekly: Update Docker images
docker compose pull
docker compose up -d

# Monthly: Clean up old logs
docker system prune -a --volumes

# Quarterly: Review and rotate API keys
python -m sovereign.main api-key list
python -m sovereign.main api-key revoke --key-id OLD_KEY_ID
```

## Next Steps

### Day 2-7 Checklist
- [ ] Set up automated backups
- [ ] Configure HTTPS/TLS
- [ ] Implement monitoring dashboards
- [ ] Document your deployment
- [ ] Plan for high availability
- [ ] Set up alerting

### Advanced Configuration
1. **Federation Setup**: Connect with other registries
   ```bash
   # Add peer registry
   curl -X POST http://localhost:8000/api/federation/peers \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"registry_url": "https://peer-registry.com"}'
   ```

2. **Custom Policies**: Configure OPA policies for your needs
3. **Performance Tuning**: Optimize for your workload

### Resources
- [Full Operator Documentation](../architecture/registry.md)
- [Security Model](../concepts/security-model.md)
- [Troubleshooting Guide](../troubleshooting/common-issues.md)
- [Federation Model](../concepts/federation-model.md)

## Getting Help

### Quick Diagnostics
```bash
# Generate diagnostic report
docker compose logs > diagnostic_report.txt
docker compose ps >> diagnostic_report.txt
docker stats --no-stream >> diagnostic_report.txt
```

### Community Support
- GitHub Issues: https://github.com/agentvault/protocol/issues
- Discord: [Coming Soon]
- Email: support@theprotocol.ai

## Congratulations! 🎉

You've successfully deployed your first Protocol registry! Your registry is now:
- ✅ Running and accessible
- ✅ Secured with authentication
- ✅ Ready for agents
- ✅ Monitored for health

Remember: A registry is the foundation of sovereign agent coordination. You're now part of the decentralized future!

---

*"The first day is about getting it running. Every day after is about keeping it excellent."*
- The Warrior Owl Doctrine
