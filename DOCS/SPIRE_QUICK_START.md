# SPIRE Quick Start Guide

## 🚀 TL;DR - Get SPIRE Running in 3 Steps

1. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

2. **Wait 10-15 seconds**, then run:
   ```bash
   .\fix_spire_simple.bat
   ```

3. **Verify it's working:**
   ```bash
   .\check_spire_status.bat
   ```

That's it! Your SPIRE identity fabric is now operational.

## 📁 Important Files

| File | Purpose |
|------|---------|
| `fix_spire_simple.bat` | Generates join token and fixes agent configuration |
| `check_spire_status.bat` | Verifies SPIRE is working correctly |
| `identity-fabric/spire-agent/agent.conf` | Agent configuration template |
| `identity-fabric/spire-server/server.conf` | Server configuration |

## ✅ Success Indicators

Look for these in the logs:
- "Node attestation was successful"
- "Renewing X509-SVID" for registry-a and registry-b
- Socket file exists at `/opt/spire/sockets/agent.sock` in service containers

## 🔍 Common Commands

```bash
# List all registered entries
docker exec agentvault-spire-server /opt/spire/bin/spire-server entry show

# Check agent logs
docker logs agentvault-spire-agent

# Generate a new join token manually
docker exec agentvault-spire-server /opt/spire/bin/spire-server token generate -spiffeID spiffe://agentvault.com/agent

# Restart SPIRE components
docker restart agentvault-spire-server agentvault-spire-agent
```

## 🎯 What This Achieves

- **Zero-Trust Security**: Every service gets a cryptographic identity
- **Automatic mTLS**: Services can authenticate each other without passwords
- **Dynamic Updates**: Certificates rotate automatically
- **Federation Ready**: Can connect with other SPIFFE-compliant systems

---

*Part of the AgentVault Open Agent Economy Initiative* 🌟
