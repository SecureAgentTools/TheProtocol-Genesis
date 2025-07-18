# Installation Guide

This guide will walk you through setting up the complete Sovereign Stack development environment.

## System Requirements

### Operating System
- **Linux** (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- **macOS** (10.15 Catalina or later)
- **Windows** (Windows 10/11 with WSL2 or native)

### Required Software

#### Python
- **Python 3.10 or 3.11** (3.12 is not yet supported)
- Verify with: `python --version`

#### Poetry
The Sovereign Stack uses Poetry for dependency management.
```bash
# Install Poetry (Linux/macOS/WSL)
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

#### Docker & Docker Compose
Required for running the identity fabric and registry services.
```bash
# Verify Docker
docker --version  # Should be 20.10+

# Verify Docker Compose
docker compose version  # Should be 2.0+
```

#### Additional Tools
- **Git** (2.25+)
- **Make** (optional, for convenience commands)
- **OpenSSL** (for certificate generation)

## Windows-Specific Setup

### Option 1: WSL2 (Recommended)

WSL2 provides the best compatibility for The Protocol's toolchain.

#### Installing WSL2

1. **Enable WSL2**
   ```powershell
   # Run as Administrator in PowerShell
   wsl --install
   
   # If already installed, ensure WSL2 is default
   wsl --set-default-version 2
   ```

2. **Install Ubuntu**
   ```powershell
   # Install Ubuntu 22.04 LTS
   wsl --install -d Ubuntu-22.04
   
   # Set as default
   wsl --setdefault Ubuntu-22.04
   ```

3. **Configure WSL2**
   ```bash
   # Inside WSL2 Ubuntu
   # Update packages
   sudo apt update && sudo apt upgrade -y
   
   # Install build essentials
   sudo apt install build-essential git curl python3-pip -y
   ```

#### Docker Desktop with WSL2

1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. During installation, ensure "Use WSL 2 instead of Hyper-V" is checked
3. After installation, go to Settings → Resources → WSL Integration
4. Enable integration with your Ubuntu distro
5. Restart Docker Desktop

#### File System Considerations

- **Best Practice**: Clone projects inside WSL2 filesystem
  ```bash
  # Good - WSL2 native filesystem (fast)
  cd ~/projects
  git clone https://github.com/SecureAgentTools/SovereignStack.git
  
  # Avoid - Windows filesystem mounted in WSL2 (slow)
  # cd /mnt/c/Users/YourName/projects
  ```

- **Accessing Files**: 
  - From Windows: `\\wsl$\Ubuntu-22.04\home\username\projects`
  - From WSL2: Native Linux paths work normally

### Option 2: Native Windows

For native Windows development without WSL2.

#### Python Setup

1. **Install Python**
   - Download Python 3.11 from [python.org](https://www.python.org/downloads/)
   - During installation, CHECK "Add Python to PATH"
   - Choose "Customize installation" → Check "pip" and "py launcher"

2. **Verify Installation**
   ```powershell
   python --version
   pip --version
   ```

#### Poetry on Windows

```powershell
# Install Poetry using PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Add to PATH (replace USERNAME with your Windows username)
$env:Path += ";C:\Users\USERNAME\AppData\Roaming\Python\Scripts"

# Make permanent (run as Administrator)
[Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::User)

# Verify
poetry --version
```

#### Docker on Native Windows

1. Install Docker Desktop (without WSL2 integration)
2. Ensure Hyper-V is enabled:
   ```powershell
   # Run as Administrator
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   ```
3. Restart computer after Hyper-V installation

#### Git Configuration

```powershell
# Configure Git for Windows line endings
git config --global core.autocrlf true

# Configure Git to use Windows-compatible paths
git config --global core.longpaths true
```

### Windows Firewall Configuration

The Protocol services need specific ports open:

```powershell
# Run as Administrator
# Registry Service
New-NetFirewallRule -DisplayName "AgentVault Registry" -Direction Inbound -LocalPort 8000,8001 -Protocol TCP -Action Allow

# TEG Layer
New-NetFirewallRule -DisplayName "AgentVault TEG" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow

# SPIRE Server
New-NetFirewallRule -DisplayName "SPIRE Server" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow

# PostgreSQL (if not using Docker)
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

### Windows-Specific Environment Variables

#### Using PowerShell
```powershell
# Set environment variables for current session
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentvault_registry"
$env:API_KEY_SECRET = "your-secret-key-here"

# Set permanently (user level)
[System.Environment]::SetEnvironmentVariable('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/agentvault_registry', 'User')
```

#### Using .env Files
Create `.env` files with Windows-style line endings:
```powershell
# Ensure Windows line endings
@"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agentvault_registry
API_KEY_SECRET=your-secret-key-here
"@ | Out-File -FilePath .env -Encoding UTF8
```

### Visual Studio Code for Windows

1. **Install Extensions**:
   - Python
   - WSL (if using WSL2)
   - Docker
   - GitLens

2. **Configure for WSL2** (if applicable):
   - Open VS Code
   - Press `Ctrl+Shift+P`
   - Type "WSL: Connect to WSL"
   - Select your Ubuntu distribution

3. **Configure Python Interpreter**:
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose Poetry environment

### Common Windows Issues and Solutions

#### Issue: "Python not found"
**Solution**: Ensure Python is in PATH
```powershell
# Check current PATH
$env:Path -split ';' | Select-String python

# Add Python to PATH if missing
$env:Path += ";C:\Python311;C:\Python311\Scripts"
```

#### Issue: Long Path Errors
**Solution**: Enable long path support
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

#### Issue: Docker Not Starting
**Solutions**:
1. Ensure virtualization is enabled in BIOS
2. Check Hyper-V is enabled
3. Restart Docker Desktop service:
   ```powershell
   Restart-Service com.docker.service
   ```

#### Issue: Port Already in Use
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

#### Issue: SSL Certificate Errors
**Solution**: Configure certificate bundle
```powershell
# Set certificate bundle path
$env:SSL_CERT_FILE = "C:\Path\To\cacert.pem"
$env:REQUESTS_CA_BUNDLE = "C:\Path\To\cacert.pem"
```

### Performance Optimization for Windows

1. **Exclude from Windows Defender**:
   ```powershell
   # Run as Administrator
   Add-MpPreference -ExclusionPath "C:\Users\USERNAME\projects\SovereignStack"
   Add-MpPreference -ExclusionProcess "python.exe", "poetry.exe", "docker.exe"
   ```

2. **Use SSD**: Place projects on SSD for better performance

3. **Increase Docker Resources**:
   - Docker Desktop → Settings → Resources
   - Increase CPU and Memory allocation

## Installation Steps

### 1. Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/SecureAgentTools/SovereignStack.git
cd SovereignStack

# Initialize submodules if any
git submodule update --init --recursive
```

### 2. Set Up Python Environment

```bash
# Create and activate virtual environment
poetry install

# Install with OS keyring support (optional)
poetry install --extras os-keyring

# Activate the virtual environment
poetry shell
```

### 3. Configure Environment Variables

Each component requires specific environment variables. Create `.env` files in the respective directories:

#### Registry Service (.env in agentvault_registry/)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agentvault_registry

# Security
API_KEY_SECRET=your-secret-key-here
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Email (optional, for notifications)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_FROM=noreply@example.com
```

#### TEG Layer (.env in agentvault_teg_layer_mvp/)
```bash
# Database
DATABASE_URL=sqlite:///./teg_layer.db

# Admin
ADMIN_API_KEY=your-admin-key-here

# Treasury
TEG_SYSTEM_TREASURY_DID=did:agentvault:teg_system_treasury
ATTESTATION_SUBMISSION_REWARD=0.1

# AVTP Integration
AVTP_SYSTEM_API_KEY=your-avtp-key-here
```

### 4. Initialize Databases

#### Registry Database
```bash
cd agentvault_registry
alembic upgrade head
cd ..
```

#### TEG Layer Database
```bash
cd agentvault_teg_layer_mvp
poetry run python scripts/initialize_db.py

# Fund the treasury for rewards
poetry run python scripts/issue_initial_tokens.py did:agentvault:teg_system_treasury 1000.0
cd ..
```

### 5. Start Core Services

#### Option A: Using Docker Compose (Recommended)

```bash
# Start Registry (includes federated setup)
cd agentvault_registry
docker compose up -d
cd ..

# Start Identity Fabric
cd ../identity-fabric
make init  # First time only
make up
cd ../SovereignStack
```

#### Option B: Manual Service Start

```bash
# Terminal 1: Registry Service
cd agentvault_registry
poetry run uvicorn agentvault_registry.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: TEG Layer Service
cd agentvault_teg_layer_mvp
poetry run uvicorn teg_core_service.main:app --reload --host 0.0.0.0 --port 8080
```

### 6. Verify Installation

```bash
# Check Registry API
curl http://localhost:8000/health

# Check TEG Layer API
curl http://localhost:8080/api/v1/health

# Check Identity Fabric
cd ../identity-fabric
make status

# Run CLI smoke test
cd ../SovereignStack
poetry run agentvault_cli --version
```

## Development Setup

### IDE Configuration

#### VS Code
1. Install Python extension
2. Select Poetry environment: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose the Poetry virtual environment

#### PyCharm
1. Go to Settings → Project → Python Interpreter
2. Add existing environment → Poetry environment

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

## Troubleshooting

### Common Issues

#### Poetry Lock Issues
```bash
# Remove lock file and regenerate
rm poetry.lock
poetry lock --no-update
poetry install
```

#### Port Conflicts
If you get "address already in use" errors:
```bash
# Find process using port (example for 8000)
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill the process or change the port in configuration
```

#### Docker Permission Issues (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

#### Database Connection Issues
- Ensure PostgreSQL is running for registry
- Check DATABASE_URL in .env files
- Verify firewall settings allow connections

### Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Search existing [GitHub issues](https://github.com/SecureAgentTools/SovereignStack/issues)
3. Create a new issue with detailed error logs

## Next Steps

Congratulations! You now have the Sovereign Stack running locally. Continue to:
- [Running the Stack](running-the-stack.md) - Learn how to operate the services
- [Building an Agent](../developer-guides/building-an-agent.md) - Create your first agent
- [Architecture Overview](../architecture/overview.md) - Understand the system design

---

*Remember: The Warrior Owl flies on properly configured wings. Take time to set up your environment correctly - it will save hours of debugging later.*
