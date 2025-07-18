# SPIRE Agent Quick Fix Guide

## If SPIRE Agent is Crashing

### Quick Fix Command Sequence
```bash
# 1. Clean up
docker rm -f agentvault-spire-agent

# 2. Start fresh with docker-compose  
docker-compose up -d spire-agent

# 3. Apply token fix
.\fix_spire_simple.bat
```

### Common Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `certificate signed by unknown authority` | Missing or invalid trust bundle | Run `fix_spire_simple.bat` |
| `no PEM blocks` | Bundle file is empty or unreadable | Check bundle exists, run fix script |
| `join token was not provided` | Token missing from config | Run `fix_spire_simple.bat` |
| `unable to parse docker host` | Missing `unix://` prefix | Fix docker_socket_path in config |
| `Container name conflict` | Duplicate containers | `docker rm -f agentvault-spire-agent` |

### The Magic Script: `fix_spire_simple.bat`

**What it does:**
1. Generates fresh join token from server
2. Creates agent.conf with token INSIDE the config
3. Copies config into running container
4. Restarts agent

**Why it works:**
- Token goes IN the config file, not command line
- Uses correct docker socket format
- Works with existing docker-compose container
- Preserves volume mounts

### Verification Commands
```bash
# Check if agent is running
docker ps | findstr spire-agent

# Check agent logs
docker logs --tail 30 agentvault-spire-agent

# Look for successful attestation in server logs
docker logs agentvault-spire-server | findstr "Signed X509 SVID"
```

### DO NOT:
- ❌ Pass join token on command line with `-joinToken`
- ❌ Mix `docker run` and `docker-compose` 
- ❌ Use `/var/run/docker.sock` without `unix://` prefix
- ❌ Try to modify trust bundles manually

### DO:
- ✅ Always use `docker-compose` for container management
- ✅ Run `fix_spire_simple.bat` for token issues
- ✅ Keep join_token in the config file
- ✅ Clean up old containers before starting fresh
