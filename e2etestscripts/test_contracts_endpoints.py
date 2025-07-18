#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for contracts.py endpoints
==========================================================
This script tests all endpoints in the contracts router.
The contracts system manages Refactoring & Upgrade Contracts (RUC)
between Client Agents and Upgrader Agents.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
ADMIN_API_KEY = "avreg_COs8OL3A7ENKZflsNyBvAsRv3v2jD4BUfrwE4uPmbeQ"
ADMIN_EMAIL = "commander@agentvault.com"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: contracts.py Endpoint Tests")
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

def test_create_contract() -> Optional[int]:
    """Test POST /api/v1/contracts endpoint"""
    contract_data = {
        "client_agent_did": "did:cos:cerberus-client-agent",
        "scope_description": "Refactor authentication module to use JWT tokens instead of API keys",
        "source_code_repo_url": "https://github.com/example/agent-repo",
        "source_code_branch": "main",
        "acceptance_criteria": {
            "type": "automated_tests",
            "requirements": [
                "All existing tests must pass",
                "JWT authentication must be implemented",
                "Backwards compatibility maintained"
            ],
            "test_suite": "tests/auth_test.py",
            "coverage_threshold": 90
        },
        "payment_amount": 1000
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/contracts",
            json=contract_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            # Verify response structure
            required_fields = ["id", "client_agent_did", "status", "scope_description", 
                             "source_code_repo_url", "source_code_branch", "acceptance_criteria",
                             "payment_amount", "created_at", "updated_at"]
            
            if all(field in data for field in required_fields) and data["status"] == "PROPOSED":
                log_result(True, "POST", "/api/v1/contracts")
                print(f"[INFO] Created contract ID: {data['id']}")
                return data["id"]
            else:
                log_result(False, "POST", "/api/v1/contracts", "Invalid response structure")
        else:
            log_result(False, "POST", "/api/v1/contracts", f"Status code: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
                
    except Exception as e:
        log_result(False, "POST", "/api/v1/contracts", str(e))
    
    return None

def test_get_contract(contract_id: int):
    """Test GET /api/v1/contracts/{contract_id} endpoint"""
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/contracts/{contract_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure and ID matches
            if data.get("id") == contract_id and "status" in data:
                log_result(True, "GET", f"/api/v1/contracts/{contract_id}")
                return data
            else:
                log_result(False, "GET", f"/api/v1/contracts/{contract_id}", "Invalid response structure")
        else:
            log_result(False, "GET", f"/api/v1/contracts/{contract_id}", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", f"/api/v1/contracts/{contract_id}", str(e))
    
    return None

def test_get_nonexistent_contract():
    """Test GET /api/v1/contracts/{contract_id} with non-existent ID"""
    non_existent_id = 99999
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/contracts/{non_existent_id}",
            timeout=10
        )
        
        if response.status_code == 404:
            log_result(True, "GET", f"/api/v1/contracts/{non_existent_id} (404 expected)")
        else:
            log_result(False, "GET", f"/api/v1/contracts/{non_existent_id}", 
                      f"Expected 404, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", f"/api/v1/contracts/{non_existent_id}", str(e))

def test_list_contracts():
    """Test GET /api/v1/contracts endpoint"""
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/contracts",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should return a list
            if isinstance(data, list):
                log_result(True, "GET", "/api/v1/contracts")
                print(f"[INFO] Found {len(data)} available contracts")
                return data
            else:
                log_result(False, "GET", "/api/v1/contracts", "Expected list response")
        else:
            log_result(False, "GET", "/api/v1/contracts", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/contracts", str(e))
    
    return []

def test_list_contracts_with_limit():
    """Test GET /api/v1/contracts?limit=5 endpoint"""
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/contracts?limit=5",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) <= 5:
                log_result(True, "GET", "/api/v1/contracts?limit=5")
            else:
                log_result(False, "GET", "/api/v1/contracts?limit=5", 
                          f"Expected max 5 items, got {len(data)}")
        else:
            log_result(False, "GET", "/api/v1/contracts?limit=5", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/contracts?limit=5", str(e))

def test_accept_contract(contract_id: int) -> bool:
    """Test POST /api/v1/contracts/{contract_id}/accept endpoint"""
    accept_data = {
        "upgrader_agent_did": "did:cos:cerberus-upgrader-agent"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/contracts/{contract_id}/accept",
            json=accept_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify status changed to ACCEPTED and credentials were generated
            if (data.get("status") == "ACCEPTED" and 
                data.get("upgrader_agent_did") == accept_data["upgrader_agent_did"] and
                data.get("access_credentials_id")):
                log_result(True, "POST", f"/api/v1/contracts/{contract_id}/accept")
                print(f"[INFO] Contract accepted with credentials: {data['access_credentials_id']}")
                return True
            else:
                log_result(False, "POST", f"/api/v1/contracts/{contract_id}/accept", 
                          "Invalid response structure")
        else:
            log_result(False, "POST", f"/api/v1/contracts/{contract_id}/accept", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", f"/api/v1/contracts/{contract_id}/accept", str(e))
    
    return False

def test_submit_contract_work(contract_id: int) -> bool:
    """Test POST /api/v1/contracts/{contract_id}/submit endpoint"""
    submit_data = {
        "pr_url": "https://github.com/example/agent-repo/pull/42"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/contracts/{contract_id}/submit",
            json=submit_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify status changed to PENDING_MERGE and PR URL is saved
            if (data.get("status") == "PENDING_MERGE" and 
                data.get("pr_url") == submit_data["pr_url"]):
                log_result(True, "POST", f"/api/v1/contracts/{contract_id}/submit")
                return True
            else:
                log_result(False, "POST", f"/api/v1/contracts/{contract_id}/submit", 
                          "Invalid response structure")
        else:
            log_result(False, "POST", f"/api/v1/contracts/{contract_id}/submit", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", f"/api/v1/contracts/{contract_id}/submit", str(e))
    
    return False

def test_approve_completion(contract_id: int) -> bool:
    """Test POST /api/v1/contracts/{contract_id}/approve-completion endpoint"""
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/contracts/{contract_id}/approve-completion",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify status changed to COMPLETED
            if data.get("status") == "COMPLETED" and data.get("completed_at"):
                log_result(True, "POST", f"/api/v1/contracts/{contract_id}/approve-completion")
                return True
            else:
                log_result(False, "POST", f"/api/v1/contracts/{contract_id}/approve-completion", 
                          "Invalid response structure")
        else:
            log_result(False, "POST", f"/api/v1/contracts/{contract_id}/approve-completion", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", f"/api/v1/contracts/{contract_id}/approve-completion", str(e))
    
    return False

def test_get_agent_contracts(agent_did: str):
    """Test GET /api/v1/contracts/agent/{agent_did} endpoint"""
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/contracts/agent/{agent_did}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_result(True, "GET", f"/api/v1/contracts/agent/{agent_did}")
                print(f"[INFO] Agent has {len(data)} contracts")
                return data
            else:
                log_result(False, "GET", f"/api/v1/contracts/agent/{agent_did}", 
                          "Expected list response")
        else:
            log_result(False, "GET", f"/api/v1/contracts/agent/{agent_did}", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", f"/api/v1/contracts/agent/{agent_did}", str(e))
    
    return []

def test_get_agent_contracts_by_role(agent_did: str):
    """Test GET /api/v1/contracts/agent/{agent_did}?role=client endpoint"""
    roles = ["client", "upgrader"]
    
    for role in roles:
        try:
            response = requests.get(
                f"{REGISTRY_A_URL}/api/v1/contracts/agent/{agent_did}?role={role}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    log_result(True, "GET", f"/api/v1/contracts/agent/{agent_did}?role={role}")
                else:
                    log_result(False, "GET", f"/api/v1/contracts/agent/{agent_did}?role={role}", 
                              "Expected list response")
            else:
                log_result(False, "GET", f"/api/v1/contracts/agent/{agent_did}?role={role}", 
                          f"Status code: {response.status_code}")
                
        except Exception as e:
            log_result(False, "GET", f"/api/v1/contracts/agent/{agent_did}?role={role}", str(e))

def test_create_malpractice_dispute():
    """Test POST /api/v1/contracts/malpractice endpoint"""
    dispute_data = {
        "contract_id": 1,
        "evidence": {
            "error_logs": ["Agent code failed to start after update"],
            "test_results": {"passed": 0, "failed": 15},
            "rollback_required": True
        },
        "claimed_damages": 5000
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/contracts/malpractice",
            json=dispute_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            # Verify basic response structure
            if "dispute_id" in data and data.get("status") == "PENDING_REVIEW":
                log_result(True, "POST", "/api/v1/contracts/malpractice")
            else:
                log_result(False, "POST", "/api/v1/contracts/malpractice", 
                          "Invalid response structure")
        else:
            log_result(False, "POST", "/api/v1/contracts/malpractice", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/contracts/malpractice", str(e))

def test_contract_validation():
    """Test contract creation with invalid data"""
    invalid_contracts = [
        {
            "name": "missing required fields",
            "data": {
                "client_agent_did": "did:cos:test",
                "scope_description": "Test"
                # Missing: source_code_repo_url, source_code_branch, etc.
            }
        },
        {
            "name": "invalid payment amount",
            "data": {
                "client_agent_did": "did:cos:test",
                "scope_description": "Test",
                "source_code_repo_url": "https://github.com/test/repo",
                "source_code_branch": "main",
                "acceptance_criteria": {},
                "payment_amount": -100  # Negative amount
            }
        },
        {
            "name": "invalid acceptance criteria",
            "data": {
                "client_agent_did": "did:cos:test",
                "scope_description": "Test",
                "source_code_repo_url": "https://github.com/test/repo",
                "source_code_branch": "main",
                "acceptance_criteria": "not a dict",  # Should be dict
                "payment_amount": 100
            }
        }
    ]
    
    for test_case in invalid_contracts:
        try:
            response = requests.post(
                f"{REGISTRY_A_URL}/api/v1/contracts",
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # We expect 400 or 422 for invalid data
            if response.status_code in [400, 422]:
                log_result(True, "POST", f"/api/v1/contracts ({test_case['name']} - validation)")
            else:
                log_result(False, "POST", f"/api/v1/contracts ({test_case['name']})", 
                          f"Expected 400/422, got {response.status_code}")
                
        except Exception as e:
            log_result(False, "POST", f"/api/v1/contracts ({test_case['name']})", str(e))

def main():
    """Run all tests for contracts.py endpoints"""
    print_test_header()
    
    print("[INFO] Testing contract endpoints...\n")
    
    # Test 1: Create a contract
    contract_id = test_create_contract()
    
    if contract_id:
        # Test 2: Get the created contract
        test_get_contract(contract_id)
        
        # Test 3: Get non-existent contract
        test_get_nonexistent_contract()
        
        # Test 4: List available contracts
        test_list_contracts()
        
        # Test 5: List contracts with limit
        test_list_contracts_with_limit()
        
        # Test 6: Accept the contract
        accepted = test_accept_contract(contract_id)
        
        if accepted:
            # Test 7: Submit work
            submitted = test_submit_contract_work(contract_id)
            
            if submitted:
                # Test 8: Approve completion
                test_approve_completion(contract_id)
        
        # Test 9: Get agent contracts
        test_get_agent_contracts("did:cos:cerberus-client-agent")
        test_get_agent_contracts("did:cos:cerberus-upgrader-agent")
        
        # Test 10: Get agent contracts by role
        test_get_agent_contracts_by_role("did:cos:cerberus-client-agent")
    
    # Test 11: Create malpractice dispute
    test_create_malpractice_dispute()
    
    # Test 12: Validation tests
    test_contract_validation()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All contracts.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_contracts_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "contracts.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results,
            "test_contract_id": contract_id if 'contract_id' in locals() else None
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
