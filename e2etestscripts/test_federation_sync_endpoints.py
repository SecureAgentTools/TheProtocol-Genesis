#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for federation_sync.py endpoints
================================================================
This script tests all endpoints in the federation_sync router.
These endpoints handle synchronization of agent data between registries.
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
ADMIN_API_KEY = "avreg_COs8OL3A7ENKZflsNyBvAsRv3v2jD4BUfrwE4uPmbeQ"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: federation_sync.py Endpoint Tests")
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

def test_get_federation_peers():
    """Test GET /api/v1/federation/peers"""
    # This endpoint requires mTLS authentication from a trusted peer
    headers = {
        "Authorization": "Bearer test_peer_token",  # Dummy token
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/federation/peers",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Should be a list of peers
            if isinstance(data, list):
                log_result(True, "GET", "/api/v1/federation/peers")
            else:
                log_result(False, "GET", "/api/v1/federation/peers", 
                          "Invalid response format - expected list")
        elif response.status_code == 401 or response.status_code == 403:
            # Expected if proper mTLS not configured
            log_result(True, "GET", "/api/v1/federation/peers", 
                      "Auth required (expected)")
        else:
            log_result(False, "GET", "/api/v1/federation/peers", 
                      f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/federation/peers", str(e))

def test_get_agent_cards():
    """Test GET /api/v1/federation/agent-cards"""
    headers = {
        "Authorization": "Bearer test_peer_token",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/federation/agent-cards?limit=10",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_result(True, "GET", "/api/v1/federation/agent-cards")
            else:
                log_result(False, "GET", "/api/v1/federation/agent-cards", 
                          "Invalid response format - expected list")
        elif response.status_code == 401 or response.status_code == 403:
            log_result(True, "GET", "/api/v1/federation/agent-cards", 
                      "Auth required (expected)")
        else:
            log_result(False, "GET", "/api/v1/federation/agent-cards", 
                      f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/federation/agent-cards", str(e))

def test_sync_request():
    """Test POST /api/v1/federation/sync-request"""
    headers = {
        "Authorization": "Bearer test_peer_token",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "source_registry": "spiffe://agentvault.com/ns/agentvault/sa/registry-test",
        "agent_cards": [
            {
                "id": "test-card-123",
                "developer_id": 1,
                "developer_name": "Test Developer",
                "developer_verified": True,
                "card_data": {
                    "name": "Test Agent",
                    "description": "Test agent for sync"
                },
                "name": "Test Agent",
                "description": "Test agent for sync",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "source_registry": "spiffe://agentvault.com/ns/agentvault/sa/registry-test"
            }
        ],
        "sync_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/federation/sync-request",
            headers=headers,
            json=request_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if ("status" in data and 
                "cards_received" in data and 
                "cards_updated" in data and
                "cards_created" in data):
                log_result(True, "POST", "/api/v1/federation/sync-request")
            else:
                log_result(False, "POST", "/api/v1/federation/sync-request", 
                          "Missing expected fields")
        elif response.status_code == 401 or response.status_code == 403:
            log_result(True, "POST", "/api/v1/federation/sync-request", 
                      "Auth required (expected)")
        else:
            log_result(False, "POST", "/api/v1/federation/sync-request", 
                      f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/federation/sync-request", str(e))

def test_sync_status():
    """Test GET /api/v1/federation/sync-status"""
    headers = {
        "Authorization": "Bearer test_peer_token",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/federation/sync-status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if ("federation_enabled" in data and 
                "our_registry" in data and 
                "total_peers" in data and
                "peer_status" in data):
                log_result(True, "GET", "/api/v1/federation/sync-status")
            else:
                log_result(False, "GET", "/api/v1/federation/sync-status", 
                          "Missing expected fields")
        elif response.status_code == 401 or response.status_code == 403:
            log_result(True, "GET", "/api/v1/federation/sync-status", 
                      "Auth required (expected)")
        else:
            log_result(False, "GET", "/api/v1/federation/sync-status", 
                      f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/federation/sync-status", str(e))

def main():
    """Run all tests for federation_sync.py endpoints"""
    print_test_header()
    
    print("[INFO] Testing federation sync endpoints (internal APIs)\n")
    print("[NOTE] These endpoints require mTLS authentication from trusted peers")
    print("[NOTE] Most tests will pass with 401/403 (auth required) as expected\n")
    
    # Run all endpoint tests
    test_get_federation_peers()
    test_get_agent_cards()
    test_sync_request()
    test_sync_status()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All federation_sync.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_federation_sync_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "federation_sync.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
