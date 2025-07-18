# AgentVault Test Architecture Quick Reference

## Test Distribution

```
Total Tests Across System
├── TEG Layer (239 tests)
│   ├── Unit Tests: ~150
│   ├── Integration Tests: ~70
│   └── E2E Tests: ~19
│
├── Registry A & B (estimated ~200+ each)
│   ├── API Tests
│   ├── Database Tests
│   ├── Auth Tests
│   └── Federation Tests
│
└── Cross-Service Integration Tests
    ├── Registry → TEG
    ├── TEG → Registry
    └── Full Stack E2E
```

## Test Execution Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Developer PC   │     │  Docker Host    │     │  Container      │
│                 │     │                 │     │                 │
│  Run Command    │────▶│  docker exec    │────▶│  python -m      │
│  test.bat       │     │  -it container  │     │  pytest         │
│                 │     │  python -m      │     │                 │
│                 │     │  pytest         │     │  ┌───────────┐  │
│                 │     │                 │     │  │ In-Memory │  │
│  Results        │◀────│  JSON Report    │◀────│  │  SQLite   │  │
│  Analysis       │     │  test_results/  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Commands Cheat Sheet

```bash
# === TEG LAYER TESTS ===
# Run all (what you were trying to do)
docker exec -it agentvault_teg_layer python -m pytest -n auto

# Run specific file
docker exec -it agentvault_teg_layer python -m pytest tests/test_token_operations.py

# Run failed only
docker exec -it agentvault_teg_layer python -m pytest --lf

# === REGISTRY TESTS ===
# Registry A
docker exec -it agentvault_registry_a pytest

# Registry B  
docker exec -it agentvault_registry_b pytest

# === INTEGRATION TESTS ===
# From host machine
python teg_test_suite_fixed.py
```

## Test Results Locations

| Service | Test Results Path | Container Path |
|---------|------------------|----------------|
| TEG Layer | `AgentVault/agentvault_teg_layer_mvp/test_results/latest_report.json` | `/app/test_results/` |
| Registry A | `AgentVault/agentvault_registry/htmlcov/` | `/app/htmlcov/` |
| Registry B | `AgentVault/agentvault_registry/htmlcov/` | `/app/htmlcov/` |

## Current Test Status

### TEG Layer (as of last run)
- **Total**: 239 tests
- **Passed**: 172 (72.0%)
- **Failed**: 13 (5.4%)
- **Errors**: 5 (2.1%)
- **Skipped**: 49 (20.5%)

### Why Different Numbers?
1. **First attempt** (53 failed): Included setup errors, wrong environment
2. **Second attempt** (35 failed): After installing pytest in container  
3. **Current** (13 failed + 5 errors): Actual test failures after proper setup

## Common Fixes Applied

1. **pytest not found** → Use `python -m pytest`
2. **No such table** → Run inside Docker container
3. **CORS errors** → Use Registry proxy endpoints
4. **Auth failures** → Use correct tokens for each service

## One-Click Tools

| Tool | Purpose |
|------|---------|
| `test.bat` | Run TEG tests quickly |
| `teg_test_helper.bat` | Interactive menu |
| `analyze_teg_failures.py` | Analyze 5.7MB JSON |
| `teg_summary.bat` | Quick summary |

---
*Generated: January 8, 2025*