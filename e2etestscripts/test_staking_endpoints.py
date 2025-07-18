#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for staking.py endpoints
=========================================================
This script tests all endpoints in the staking router.
FIXED: Staking endpoints require DEVELOPER authentication, not agent authentication.
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

def setup_test_developer() -> Tuple[bool, Optional[str], Optional[str]]:
    """Create or use existing test developer and get authentication token"""
    # Generate unique test credentials
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"cerberus_staking_test_{timestamp}@test.com"
    test_password = "CerberusStaking#2025!"
    
    # First try to register a new developer
    print("[INFO] Creating test developer for staking tests...")
    registration_data = {
        "name": f"Cerberus Staking Test {timestamp}",
        "email": test_email,
        "password": test_password,
        "organization": "Operation Cerberus Staking Tests"
    }
    
    try:
        # Register developer
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/register",
            json=registration_data,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"[INFO] Test developer registered: {test_email}")
        else:
            # Try with a known test account if registration fails
            test_email = "cerberus@agentvault.com"
            test_password = "Cerberus#Test2025!"
            print(f"[INFO] Using existing test account: {test_email}")
    except Exception as e:
        print(f"[WARN] Registration attempt failed: {e}")
        # Use fallback credentials
        test_email = "cerberus@agentvault.com"
        test_password = "Cerberus#Test2025!"
    
    # Now login to get token
    print("[INFO] Authenticating developer...")
    login_data = {
        "username": test_email,  # OAuth2 form uses username field for email
        "password": test_password
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/login",
            data=login_data,  # Form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data.get("token_type") == "bearer":
                print(f"[INFO] Developer authentication successful")
                return True, data["access_token"], test_email
            else:
                print(f"[ERROR] Invalid login response structure")
                return False, None, None
        else:
            print(f"[ERROR] Developer login failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
            return False, None, None
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
        return False, None, None

def test_get_stake_balance(token: str, developer_email: str):
    """Test GET /api/v1/staking/balance endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/staking/balance",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if all(field in data for field in ["agent_did", "liquid_balance", "staked_balance", "total_balance"]):
                log_result(True, "GET", "/api/v1/staking/balance")
                print(f"   DID: {data['agent_did']}")
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
            # Check for expected structure
            if "system_status" in data or "integration_active" in data:
                log_result(True, "GET", "/api/v1/staking/status")
                if "system_status" in data:
                    print(f"   System Status: {data['system_status'].get('integration_active', 'N/A')}")
                    print(f"   TEG Connection: {data['system_status'].get('teg_connection', {}).get('connected', 'N/A')}")
                else:
                    print(f"   Integration Active: {data.get('integration_active', 'N/A')}")
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
    
    try:
        # The error says amount is required in query params, not body
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/staking/stake?amount={amount}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected fields in stub response
            if "transaction_id" in data and "amount" in data:
                log_result(True, "POST", "/api/v1/staking/stake")
                print(f"   Transaction ID: {data.get('transaction_id', 'N/A')}")
                print(f"   Amount: {data.get('amount', 'N/A')} AVT")
                print(f"   Status: {data.get('status', 'N/A')}")
                return True
            else:
                log_result(False, "POST", "/api/v1/staking/stake", "Invalid response structure")
                return False
        else:
            error_msg = f"Status code: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {response.text or 'No error details'}"
            log_result(False, "POST", "/api/v1/staking/stake", error_msg)
            return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/staking/stake", str(e))
        return False

def test_unstake_tokens(token: str, amount: str = "5"):
    """Test POST /api/v1/staking/unstake endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Amount in query params, not body
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/staking/unstake?amount={amount}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected fields in stub response
            if "transaction_id" in data and "amount" in data:
                log_result(True, "POST", "/api/v1/staking/unstake")
                print(f"   Transaction ID: {data.get('transaction_id', 'N/A')}")
                print(f"   Amount: {data.get('amount', 'N/A')} AVT")
                print(f"   Status: {data.get('status', 'N/A')}")
                return True
            else:
                log_result(False, "POST", "/api/v1/staking/unstake", "Invalid response structure")
                return False
        else:
            error_msg = f"Status code: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {response.text or 'No error details'}"
            log_result(False, "POST", "/api/v1/staking/unstake", error_msg)
            return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/staking/unstake", str(e))
        return False

def main():
    """Run all tests for staking.py endpoints"""
    print_test_header()
    
    # Setup test developer and authenticate
    success, token, developer_email = setup_test_developer()
    if not success or not token:
        print("\n[FATAL] Failed to authenticate as developer")
        sys.exit(1)
    
    print(f"\n[INFO] Testing staking endpoints as developer: {developer_email}\n")
    
    # Run all endpoint tests
    # Test balance and status first
    success, balance_data = test_get_stake_balance(token, developer_email)
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
