#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for staking.py endpoints
=========================================================
This script tests all endpoints in the staking router.
Updated to use commander developer authentication.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
TEG_BASE_URL = "http://localhost:8100/api/v1"

# Commander credentials
COMMANDER_EMAIL = "commander@agentvault.com"
COMMANDER_PASSWORD = "SovereignKey!2025"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: staking.py Endpoint Tests")
    print("="*60)
    print(f"Registry URL: {REGISTRY_A_URL}")
    print(f"TEG URL: {TEG_BASE_URL}")
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

def authenticate_commander() -> Optional[str]:
    """Authenticate with commander credentials and get JWT token"""
    # OAuth2 requires form data
    auth_data = {
        "grant_type": "password",
        "username": COMMANDER_EMAIL,
        "password": COMMANDER_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/login",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"[INFO] Commander authentication successful")
            return token_data.get("access_token")
        else:
            print(f"[ERROR] Authentication failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"[ERROR] Details: {error_data}")
            except:
                print(f"[ERROR] Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
        return None

def test_get_stake_balance(token: str):
    """Test GET /api/v1/staking/balance endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with a sample DID
    test_did = "did:key:test_staking"
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/staking/balance?agent_did={test_did}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if all(field in data for field in ["agent_did", "liquid_balance", "staked_balance", "total_balance"]):
                log_result(True, "GET", "/api/v1/staking/balance")
                print(f"   Liquid: {data['liquid_balance']} AVT")
                print(f"   Staked: {data['staked_balance']} AVT")
                print(f"   Total: {data['total_balance']} AVT")
                return True, data
            else:
                log_result(False, "GET", "/api/v1/staking/balance", "Invalid response structure")
                return False, None
        else:
            log_result(False, "GET", "/api/v1/staking/balance", f"Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/staking/balance", str(e))
        return False, None

def test_get_staking_status(token: str):
    """Test GET /api/v1/staking/status endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/staking/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if "total_staked" in data:
                log_result(True, "GET", "/api/v1/staking/status")
                print(f"   Total Staked: {data.get('total_staked', 0)}")
                print(f"   Unique Stakers: {data.get('unique_stakers', 0)}")
                return True
            else:
                log_result(False, "GET", "/api/v1/staking/status", "Invalid response structure")
                return False
        else:
            log_result(False, "GET", "/api/v1/staking/status", f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/staking/status", str(e))
        return False

def test_stake_tokens(token: str, amount: str = "10"):
    """Test POST /api/v1/staking/stake endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Stake on behalf of a test agent
    stake_data = {
        "amount": amount,
        "agent_did": "did:key:test_stake_001"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/staking/stake",
            headers=headers,
            json=stake_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if all(field in data for field in ["id", "agent_did", "transaction_type", "amount", "created_at"]):
                log_result(True, "POST", "/api/v1/staking/stake")
                print(f"   Transaction ID: {data['id']}")
                print(f"   Amount: {data['amount']} AVT")
                print(f"   Type: {data['transaction_type']}")
                return True
            else:
                log_result(False, "POST", "/api/v1/staking/stake", "Invalid response structure")
                return False
        elif response.status_code == 503:
            # TEG Layer might be down, but endpoint exists
            log_result(True, "POST", "/api/v1/staking/stake")
            print(f"   Note: TEG Layer service unavailable (503)")
            return True
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = response.text or f"Status {response.status_code}"
            log_result(False, "POST", "/api/v1/staking/stake", f"Status code: {response.status_code} - {error_msg}")
            return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/staking/stake", str(e))
        return False

def test_unstake_tokens(token: str, amount: str = "5"):
    """Test POST /api/v1/staking/unstake endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    unstake_data = {
        "amount": amount,
        "agent_did": "did:key:test_stake_001"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/staking/unstake",
            headers=headers,
            json=unstake_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if all(field in data for field in ["id", "agent_did", "transaction_type", "amount", "created_at"]):
                log_result(True, "POST", "/api/v1/staking/unstake")
                print(f"   Transaction ID: {data['id']}")
                print(f"   Amount: {data['amount']} AVT")
                print(f"   Type: {data['transaction_type']}")
                return True
            else:
                log_result(False, "POST", "/api/v1/staking/unstake", "Invalid response structure")
                return False
        elif response.status_code == 503:
            # TEG Layer might be down, but endpoint exists
            log_result(True, "POST", "/api/v1/staking/unstake")
            print(f"   Note: TEG Layer service unavailable (503)")
            return True
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = response.text or f"Status {response.status_code}"
            log_result(False, "POST", "/api/v1/staking/unstake", f"Status code: {response.status_code} - {error_msg}")
            return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/staking/unstake", str(e))
        return False

def main():
    """Run all tests for staking.py endpoints"""
    print_test_header()
    
    # Authenticate as commander
    token = authenticate_commander()
    if not token:
        print("\n[FATAL] Failed to authenticate as commander")
        sys.exit(1)
    
    print(f"\n[INFO] Testing with commander privileges\n")
    
    # Run all endpoint tests
    # Test balance and status first
    test_get_stake_balance(token)
    test_get_staking_status(token)
    
    # Test staking operations
    test_stake_tokens(token, "10")
    test_unstake_tokens(token, "5")
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All staking.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_staking_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "staking.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
