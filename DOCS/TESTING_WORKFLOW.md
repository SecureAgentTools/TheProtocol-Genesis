# AgentVault Testing Workflow Documentation

**Created**: January 8, 2025  
**Purpose**: Complete reference for testing AgentVault's dockerized multi-service architecture

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Test Types and Locations](#test-types-and-locations)
3. [Running Tests](#running-tests)
4. [Common Issues and Solutions](#common-issues-and-solutions)
5. [Test Analysis Tools](#test-analysis-tools)
6. [Testing Workflow](#testing-workflow)
7. [Quick Reference](#quick-reference)

---

## Architecture Overview

AgentVault consists of multiple dockerized services:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Environment                         │
├─────────────────────┬────────────────────┬─────────────────────┤
│   Registry A        │   Registry B       │   TEG Layer         │
│   Port: 8000        │   Port: 8001       │   Port: 8100        │
│   DB: PostgreSQL    │   DB: PostgreSQL   │   DB: SQLite        │
│   Container:        │   Container:        │   Container:        │
│   agentvault_       │   agentvault_      │   agentvault_       │
│   registry_a        │   registry_b       │   teg_layer         │
└─────────────────────┴────────────────────┴─────────────────────┘
                                │
                    ┌───────────┴────────────┐
                    │   SPIRE Identity       │
                    │   OPA Policies         │
                    │   Cognitive Shield     │
                    └────────────────────────┘
```

## Test Types and Locations

### 1. TEG Layer Tests (Unit/Integration)
- **Location**: `D:\Agentvault2\AgentVault\agentvault_teg_layer_mvp\tests\`
- **Test Count**: ~239 tests
- **Database**: In-memory SQLite (for test isolation)
- **Must Run**: Inside Docker container
- **Results**: `test_results/latest_report.json`

### 2. Registry Tests
- **Location**: `D:\Agentvault2\AgentVault\agentvault_registry\tests\`
- **Database**: PostgreSQL (test database)
- **Must Run**: Inside respective Docker containers

### 3. Integration Tests (Cross-Service)
- **Location**: Various, including the fixes in `D:\Agentvault2\`
- **Purpose**: Test API interactions between services
- **Can Run**: From host machine against running services

### 4. Browser/UI Tests
- **Location**: Frontend test files
- **Purpose**: Test UI interactions with backend APIs
- **Issue**: CORS requires using Registry proxy endpoints

## Running Tests

### TEG Layer Tests

```bash
# Run all TEG tests (inside container)
docker exec -it agentvault_teg_layer python -m pytest -n auto

# Run specific test file
docker exec -it agentvault_teg_layer python -m pytest tests/test_token_operations.py -v

# Run with visible output
docker exec -it agentvault_teg_layer python -m pytest -s

# Run only failed tests from last run
docker exec -it agentvault_teg_layer python -m pytest --lf

# Run tests matching pattern
docker exec -it agentvault_teg_layer python -m pytest -k "test_create"
```

### Registry Tests

```bash
# Registry A tests
docker exec -it agentvault_registry_a pytest -n auto

# Registry B tests  
docker exec -it agentvault_registry_b pytest -n auto
```

### Integration Tests (Host Machine)

```bash
# Run the fixed integration test suite
python teg_test_suite_fixed.py

# Quick connectivity test
python test_teg_quick.py

# Test with curl
./test_teg_curl.sh  # Linux/Mac
test_teg_curl.bat   # Windows
```

## Common Issues and Solutions

### Issue 1: "pytest: executable file not found"

**Cause**: Production Docker image doesn't include dev dependencies

**Solution**: 
```bash
# Install pytest in container
docker exec -it agentvault_teg_layer pip install pytest pytest-asyncio pytest-xdist httpx pytest-json-report

# Use python -m pytest instead of pytest directly
docker exec -it agentvault_teg_layer python -m pytest -n auto
```

### Issue 2: "no such table: teg_policies"

**Cause**: Running tests locally without database initialization

**Solution**: Always run tests inside Docker container where database exists

### Issue 3: CORS Errors in Browser Tests

**Cause**: Direct browser calls to TEG API are blocked

**Solution**: Use Registry proxy endpoints (`/api/v1/teg/*`)

### Issue 4: Authentication Failures

**Cause**: Missing or incorrect auth tokens

**Solution**: 
- Agent operations: Use Registry JWT token
- Service operations: Use admin API key
- Check environment variables in docker-compose.yml

## Test Analysis Tools

### Automated Analysis Scripts

1. **analyze_teg_failures.py**
   - Comprehensive failure analysis
   - Extracts patterns from large JSON report
   - Creates summary file

2. **quick_analyze.py**
   - Quick summary of failures
   - Lists failing tests by file

3. **teg_test_helper.bat**
   - Interactive menu for all operations
   - Run tests, analyze failures, etc.

### Manual Analysis

```bash
# View test summary
docker exec -it agentvault_teg_layer python -m pytest --tb=short

# Generate HTML report
docker exec -it agentvault_teg_layer python -m pytest --html=report.html

# Copy report from container
docker cp agentvault_teg_layer:/app/test_results/latest_report.json ./
```

## Testing Workflow

### 1. Initial Setup

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker ps | grep agentvault

# Check service health
curl http://localhost:8000/health  # Registry A
curl http://localhost:8001/health  # Registry B
curl http://localhost:8100/health  # TEG Layer
```

### 2. Running Tests

```bash
# Step 1: Run TEG tests
docker exec -it agentvault_teg_layer python -m pytest -n auto

# Step 2: Run Registry tests
docker exec -it agentvault_registry_a pytest -n auto
docker exec -it agentvault_registry_b pytest -n auto

# Step 3: Run integration tests
python teg_test_suite_fixed.py
```

### 3. Analyzing Failures

```bash
# For TEG tests
python analyze_teg_failures.py

# View summary
teg_summary.bat

# List specific failures
list_failures.bat
```

### 4. Fixing Tests

1. Identify pattern from analysis
2. Fix the root cause
3. Re-run affected tests
4. Verify fix worked

### 5. Continuous Testing

```bash
# Watch mode (if available)
docker exec -it agentvault_teg_layer python -m pytest-watch

# Or use a loop
while true; do
    docker exec -it agentvault_teg_layer python -m pytest --lf -x
    read -p "Press enter to re-run..."
done
```

## Quick Reference

### File Locations

| Component | Source Code | Tests | Results |
|-----------|-------------|-------|---------|
| TEG Layer | `AgentVault/agentvault_teg_layer_mvp/` | `tests/` | `test_results/` |
| Registry | `AgentVault/agentvault_registry/` | `tests/` | `htmlcov/` |
| Integration | Project root | Various | Logs |

### Helper Scripts

| Script | Purpose |
|--------|---------|
| `test.bat` | Quick run all TEG tests |
| `teg_test_helper.bat` | Interactive test menu |
| `analyze_teg_failures.py` | Analyze test failures |
| `teg_test_suite_fixed.py` | Integration tests |

### Docker Commands

```bash
# View logs
docker logs agentvault_teg_layer --tail 100

# Shell access
docker exec -it agentvault_teg_layer /bin/bash

# Copy files
docker cp agentvault_teg_layer:/app/file.txt ./

# Restart service
docker-compose restart teg-layer

# Rebuild service
docker-compose build teg-layer
docker-compose up -d teg-layer
```

### Environment Variables

Key variables from docker-compose.yml:

```yaml
# TEG Layer
ADMIN_API_KEY: "development-admin-api-key-change-in-production-12345678"
DATABASE_URL: sqlite:///./teg_database.db

# Registry
TEG_API_BASE_URL: http://teg-layer:8080
```

## Test Metrics

### Current Status (as of last run)

**TEG Layer Tests**:
- Total: 239 tests
- Passed: 172 (72%)
- Failed: 13
- Errors: 5
- Skipped: 49

**Common Failure Categories**:
1. Authentication/Authorization
2. Missing fixtures
3. Database state issues
4. API endpoint problems

### Test Performance

- Average duration: ~60 seconds for full suite
- Parallel execution: Yes (`-n auto`)
- Coverage: Run with `--cov=src` for metrics

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs teg-layer

# Check port conflicts
netstat -an | findstr 8100

# Force recreate
docker-compose up -d --force-recreate teg-layer
```

### Database Issues

```bash
# Check database file
docker exec agentvault_teg_layer ls -la *.db

# Reset database
docker exec agentvault_teg_layer rm -f teg_database.db
docker-compose restart teg-layer
```

### Network Issues

```bash
# Test internal connectivity
docker exec agentvault_registry_a ping teg-layer

# Check network
docker network ls
docker network inspect agentvault_main_network
```

## Best Practices

1. **Always run tests in Docker** - Ensures consistent environment
2. **Use parallel execution** - `-n auto` for speed
3. **Fix by category** - Group similar failures
4. **Check logs first** - Often reveals the issue
5. **Keep tests isolated** - Each test should be independent
6. **Use fixtures** - For common setup/teardown
7. **Document failures** - Add comments when fixing

## Future Improvements

1. **CI/CD Integration**
   - GitHub Actions workflow
   - Automated test runs on PR

2. **Test Coverage**
   - Add coverage requirements
   - Generate coverage reports

3. **Performance Testing**
   - Load testing endpoints
   - Benchmark critical paths

4. **Development Mode**
   - Dockerfile.dev with dev dependencies
   - Hot reload for faster iteration

---

**Note**: This workflow assumes Docker Desktop is running and all services are properly configured. For production testing, additional security and isolation measures should be implemented.