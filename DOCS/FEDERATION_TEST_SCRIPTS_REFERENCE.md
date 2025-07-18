# Federation Test Scripts Reference

**Created:** January 7, 2025  
**Purpose:** Document the working federation test scripts

---

## Working Test Scripts

These scripts have been verified to work correctly with the current AgentVault federation implementation.

### 1. Check and Activate Federation Peers
**File:** `check_and_activate_federation_peers.py`

**Purpose:**
- Login as admin to both registries
- Check peer registry relationships
- Approve pending peers if needed
- Show federation status summary

**Key Features:**
- Handles paginated API responses correctly
- Uses form-urlencoded authentication
- Safe dictionary access with `.get()`
- Comprehensive error handling

**Usage:**
```bash
python check_and_activate_federation_peers.py
```

### 2. Test Federation Agent Discovery
**File:** `test_federation_agents_discovery.py`

**Purpose:**
- Demonstrate federated agent discovery
- Search Registry B with federation enabled
- Show Registry A agents in results
- Test specific agent searches

**Key Features:**
- Simple and focused on demonstration
- Shows origin registry for each agent
- Tests both general and specific searches
- Clear success/failure indicators

**Usage:**
```bash
python test_federation_agents_discovery.py
```

### 3. Verify and Test Federation (Comprehensive)
**File:** `verify_and_test_federation.py`

**Purpose:**
- Complete federation infrastructure check
- Test all aspects of federation
- Provide detailed diagnostics
- Check internal federation endpoints

**Key Features:**
- Async implementation for efficiency
- Tests both registries thoroughly
- Includes debug output
- Comprehensive error handling

**Usage:**
```bash
python verify_and_test_federation.py
```

---

## Key Implementation Details

### Authentication
All scripts use the correct OAuth2 form-urlencoded format:
```python
data = {
    "username": ADMIN_EMAIL,  # Note: 'username' field for email
    "password": ADMIN_PASSWORD,
    "grant_type": "password"
}
```

### API Response Handling
The admin federation endpoints return paginated responses:
```python
{
    "items": [...],  # List of peer registries
    "pagination": {  # Pagination metadata
        "total_items": 8,
        "limit": 100,
        "offset": 0,
        "total_pages": 1,
        "current_page": 1
    }
}
```

### Federation Query Parameter
To enable federated search:
```python
params = {
    "include_federated": "true",  # Must be string "true"
    "limit": 100
}
```

---

## Test Configuration

### Credentials
- **Admin Email:** `commander@agentvault.com`
- **Admin Password:** `SovereignKey!2025`
- **Registry A API Key:** `avreg_eJx7JyZWspw29zO8A_EcsMPsA6_lrL7O6eFwzKaIG6I`
- **Registry B API Key:** `avreg_d2yxb_VO1L9IieWEr4SF6oogMrOdNu2P7T3K5dKOcHk`

### Endpoints
- **Registry A:** `http://localhost:8000`
- **Registry B:** `http://localhost:8001`

---

## Verified Working

All three scripts have been tested and confirmed working on January 7, 2025. They successfully demonstrate that federation is fully operational between Registry A and Registry B.
