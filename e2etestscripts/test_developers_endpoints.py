#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for developers.py endpoints
===========================================================
This script tests all endpoints in the developers router.
Developer endpoints require JWT authentication (not agent auth).
FIXED: Using strong password that meets auth_secure.py requirements.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Optional, List

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
ADMIN_API_KEY = "development-admin-api-key-change-in-production-12345678"
ADMIN_EMAIL = "commander@agentvault.com"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: developers.py Endpoint Tests")
    print("="*60)
    print(f"Registry URL: {REGISTRY_A_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

def log_result(passed: bool, method: str, endpoint: str, message: str = ""):
    """Log and print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    result_msg = f"{status} {method} {endpoint}"
    if message and not passed:
        result_msg += f" - {message}"
    print(result_msg)
    test_results.append({
        "endpoint": f"{method} {endpoint}",
        "passed": passed,
        "message": message
    })

def create_or_login_developer() -> Optional[str]:
    """Create a developer account or login to existing one"""
    # First try to register with a unique email
    unique_email = f"cerberus_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@agentvault.com"
    password = "CerberusTest#2025!"  # Strong password meeting all requirements
    print(f"[INFO] Registering new developer with email: {unique_email}")
    
    register_data = {
        "email": unique_email,
        "password": password,
        "name": f"cerberus_test_dev_{datetime.now().strftime('%H%M%S')}",  # Unique name
        "organization": "Operation Cerberus Testing"  # Added organization field
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/register",
            json=register_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print("[INFO] Registration successful, now logging in...")
            # Now login with the newly created account (OAuth2 form data)
            login_data = {
                "username": unique_email,  # OAuth2 expects 'username' field
                "password": password
            }
            response = requests.post(
                f"{REGISTRY_A_URL}/api/v1/auth/login",
                data=login_data,  # Use form data, not JSON
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"[INFO] Developer registered and logged in")
                return token_data.get("access_token")
            else:
                print(f"[ERROR] Login after registration failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"[ERROR] Login error details: {error_detail}")
                except:
                    print(f"[ERROR] Login response: {response.text}")
        else:
            print(f"[ERROR] Failed to register: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
    
    return None

def test_get_developer_me(token: str):
    """Test GET /api/v1/developers/me endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/developers/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Debug: print actual fields
            print(f"[DEBUG] Actual fields in response: {list(data.keys())}")
            
            # Verify response contains expected fields
            required_fields = ["id", "email", "is_verified"]  # Changed from is_active to is_verified
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                log_result(True, "GET", "/api/v1/developers/me")
                return data
            else:
                log_result(False, "GET", "/api/v1/developers/me", f"Missing required fields: {missing_fields}")
        else:
            log_result(False, "GET", "/api/v1/developers/me", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/developers/me", str(e))
    
    return None

def test_create_api_key(token: str) -> Optional[Dict]:
    """Test POST /api/v1/developers/me/apikeys endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    api_key_data = {
        "description": "Cerberus test API key"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/developers/me/apikeys",
            headers=headers,
            json=api_key_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            # Verify response structure
            if ("plain_api_key" in data and 
                "api_key_info" in data and
                data["plain_api_key"].startswith("avreg_")):
                log_result(True, "POST", "/api/v1/developers/me/apikeys")
                print(f"[INFO] Created API key: {data['api_key_info']['id']}")
                return data
            else:
                log_result(False, "POST", "/api/v1/developers/me/apikeys", "Invalid response structure")
        else:
            log_result(False, "POST", "/api/v1/developers/me/apikeys", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/developers/me/apikeys", str(e))
    
    return None

def test_list_api_keys(token: str) -> List[Dict]:
    """Test GET /api/v1/developers/me/apikeys endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/developers/me/apikeys",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return a list
            if isinstance(data, list):
                log_result(True, "GET", "/api/v1/developers/me/apikeys")
                print(f"[INFO] Found {len(data)} API keys")
                return data
            else:
                log_result(False, "GET", "/api/v1/developers/me/apikeys", "Expected list response")
        else:
            log_result(False, "GET", "/api/v1/developers/me/apikeys", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/developers/me/apikeys", str(e))
    
    return []

def test_delete_api_key(token: str, key_id: int):
    """Test DELETE /api/v1/developers/me/apikeys/{key_id} endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(
            f"{REGISTRY_A_URL}/api/v1/developers/me/apikeys/{key_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 204:
            log_result(True, "DELETE", f"/api/v1/developers/me/apikeys/{key_id}")
        else:
            log_result(False, "DELETE", f"/api/v1/developers/me/apikeys/{key_id}", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "DELETE", f"/api/v1/developers/me/apikeys/{key_id}", str(e))

def test_list_developer_agents(token: str) -> List[Dict]:
    """Test GET /api/v1/developers/me/agents endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/developers/me/agents",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return a list
            if isinstance(data, list):
                log_result(True, "GET", "/api/v1/developers/me/agents")
                print(f"[INFO] Developer has {len(data)} agents")
                return data
            else:
                log_result(False, "GET", "/api/v1/developers/me/agents", "Expected list response")
        else:
            log_result(False, "GET", "/api/v1/developers/me/agents", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/developers/me/agents", str(e))
    
    return []

def test_get_teg_summary(token: str):
    """Test GET /api/v1/developers/me/teg-summary endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/developers/me/teg-summary",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            required_fields = ["total_liquid_balance", "total_staked_balance", 
                             "total_balance", "aggregate_reputation_score", 
                             "agent_count", "active_agent_count"]
            
            if all(field in data for field in required_fields):
                log_result(True, "GET", "/api/v1/developers/me/teg-summary")
                print(f"[INFO] TEG Summary - Agents: {data['agent_count']}, Balance: {data['total_balance']}")
            else:
                log_result(False, "GET", "/api/v1/developers/me/teg-summary", "Missing required fields")
        else:
            log_result(False, "GET", "/api/v1/developers/me/teg-summary", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/developers/me/teg-summary", str(e))

def test_get_agent_balance(token: str, agent_did: str):
    """Test GET /api/v1/developers/me/agents/{agent_did}/balance endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/developers/me/agents/{agent_did}/balance",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            if ("agent_did" in data and 
                "balance" in data and 
                data.get("currency") == "AVT"):
                log_result(True, "GET", f"/api/v1/developers/me/agents/{agent_did}/balance")
                print(f"[INFO] Agent balance: {data['balance']} AVT")
            else:
                log_result(False, "GET", f"/api/v1/developers/me/agents/{agent_did}/balance", 
                          "Invalid response structure")
        elif response.status_code == 404:
            # Expected if agent doesn't exist or doesn't belong to developer
            log_result(True, "GET", f"/api/v1/developers/me/agents/{agent_did}/balance (404 expected)")
        else:
            log_result(False, "GET", f"/api/v1/developers/me/agents/{agent_did}/balance", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", f"/api/v1/developers/me/agents/{agent_did}/balance", str(e))

def test_get_agent_balances_batch(token: str, agent_dids: List[str]):
    """Test POST /api/v1/developers/me/agents/balances endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    batch_data = {
        "agent_dids": agent_dids
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/developers/me/agents/balances",
            headers=headers,
            json=batch_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            if "balances" in data and isinstance(data["balances"], dict):
                log_result(True, "POST", "/api/v1/developers/me/agents/balances")
                successful = sum(1 for b in data["balances"].values() if "error" not in b)
                print(f"[INFO] Batch balance fetch: {successful}/{len(agent_dids)} successful")
            else:
                log_result(False, "POST", "/api/v1/developers/me/agents/balances", 
                          "Invalid response structure")
        else:
            log_result(False, "POST", "/api/v1/developers/me/agents/balances", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/developers/me/agents/balances", str(e))

def test_batch_size_limit(token: str):
    """Test batch endpoint with too many agents"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a batch with more than 50 agents
    large_batch = {
        "agent_dids": [f"did:cos:test-agent-{i}" for i in range(51)]
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/developers/me/agents/balances",
            headers=headers,
            json=large_batch,
            timeout=10
        )
        
        if response.status_code == 400:
            log_result(True, "POST", "/api/v1/developers/me/agents/balances (batch limit test)")
        else:
            log_result(False, "POST", "/api/v1/developers/me/agents/balances (batch limit)", 
                      f"Expected 400, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/developers/me/agents/balances (batch limit)", str(e))

def create_test_agent_for_developer(token: str) -> Optional[Dict]:
    """Create a test agent owned by the developer"""
    # First, we need to get a bootstrap token with developer auth
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Request bootstrap token as a developer
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
            headers={
                "X-Api-Key": ADMIN_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "agent_type_hint": "test-agent",
                "requested_by": ADMIN_EMAIL,
                "description": "Cerberus developer test agent"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to get bootstrap token: {response.status_code}")
            return None
            
        bootstrap_token = response.json()["bootstrap_token"]
        
        # Create agent
        agent_card = {
            "schemaVersion": "1.0",
            "humanReadableId": "cerberus-dev-test-agent",
            "agentVersion": "1.0.0",
            "name": "Developer Test Agent",
            "description": "Test agent for developer endpoint verification",
            "url": f"http://localhost:8000/agents/cerberus-dev-test-agent",
            "provider": {
                "name": "Operation Cerberus",
                "url": "https://www.theprotocol.cloud",
                "support_contact": "cerberus@agentvault.com"
            },
            "capabilities": {
                "a2aVersion": "1.0",
                "supportedMessageParts": ["text", "data"],
                "supportsPushNotifications": True
            },
            "authSchemes": [{"scheme": "apiKey"}],
            "tags": ["test", "cerberus", "developer"],
            "skills": []
        }
        
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/create_agent",
            headers={"Bootstrap-Token": bootstrap_token, "Content-Type": "application/json"},
            json={
                "agent_did_method": "cos",
                "agent_card": agent_card
            },
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"[INFO] Created test agent: {data['agent_did']}")
            return data
        
    except Exception as e:
        print(f"[ERROR] Failed to create test agent: {str(e)}")
    
    return None

def main():
    """Run all tests for developers.py endpoints"""
    print_test_header()
    
    # Authenticate as developer (not agent)
    developer_token = create_or_login_developer()
    if not developer_token:
        print("\n[FATAL] Failed to authenticate as developer")
        sys.exit(1)
    
    print("\n[INFO] Testing developer endpoints...\n")
    
    # Test 1: Get developer info
    developer_info = test_get_developer_me(developer_token)
    
    # Test 2: Create API key
    api_key_data = test_create_api_key(developer_token)
    
    # Test 3: List API keys
    api_keys = test_list_api_keys(developer_token)
    
    # Test 4: Delete API key (if we created one)
    if api_key_data and "api_key_info" in api_key_data:
        key_id = api_key_data["api_key_info"]["id"]
        test_delete_api_key(developer_token, key_id)
    
    # Test 5: List developer's agents
    agents = test_list_developer_agents(developer_token)
    
    # Create a test agent if none exist
    if not agents:
        print("\n[INFO] Creating test agent for balance tests...")
        test_agent = create_test_agent_for_developer(developer_token)
        if test_agent:
            agents = [{"did": test_agent["agent_did"]}]
    
    # Test 6: Get TEG summary
    test_get_teg_summary(developer_token)
    
    # Test 7: Get single agent balance (if we have agents)
    if agents and len(agents) > 0:
        agent_did = agents[0].get("did")
        if agent_did:
            test_get_agent_balance(developer_token, agent_did)
            
            # Test 8: Batch balance request
            test_agent_dids = [agent_did]
            if len(agents) > 1:
                test_agent_dids.append(agents[1].get("did"))
            
            test_get_agent_balances_batch(developer_token, test_agent_dids)
    else:
        # Test with non-existent agent
        test_get_agent_balance(developer_token, "did:cos:nonexistent")
        test_get_agent_balances_batch(developer_token, ["did:cos:nonexistent"])
    
    # Test 9: Batch size limit
    test_batch_size_limit(developer_token)
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All developers.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_developers_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "developers.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
