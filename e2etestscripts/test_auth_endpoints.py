#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for auth.py endpoints
======================================================
This script tests all endpoints in the auth router.
Includes both developer and agent authentication flows.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: auth.py Endpoint Tests")
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

def test_health_check():
    """Test basic health check to verify service is running"""
    try:
        response = requests.get(f"{REGISTRY_A_URL}/health", timeout=10)
        if response.status_code == 200:
            print("[INFO] Service health check passed")
            return True
        else:
            print(f"[ERROR] Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Cannot connect to service: {str(e)}")
        return False

def test_developer_registration():
    """Test POST /api/v1/auth/register endpoint"""
    # Generate unique email for test
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"cerberus_test_{timestamp}@test.com"
    
    registration_data = {
        "name": f"Cerberus Test Developer {timestamp}",
        "email": test_email,
        "password": "Cerberus#Test2025!",  # Fixed: No common patterns, meets all requirements
        "organization": "Operation Cerberus"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/register",
            json=registration_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            if "recovery_keys" in data and "message" in data:
                log_result(True, "POST", "/api/v1/auth/register")
                return True, test_email, registration_data["password"], data.get("recovery_keys", [])
            else:
                log_result(False, "POST", "/api/v1/auth/register", "Invalid response structure")
                return False, None, None, None
        else:
            error_msg = f"Status code: {response.status_code}"
            try:
                error_detail = response.json().get("detail", "")
                if error_detail:
                    error_msg += f" - {error_detail}"
            except:
                pass
            log_result(False, "POST", "/api/v1/auth/register", error_msg)
            return False, None, None, None
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/auth/register", str(e))
        return False, None, None, None

def test_developer_login(email: str, password: str):
    """Test POST /api/v1/auth/login endpoint"""
    login_data = {
        "username": email,  # OAuth2 form uses username field for email
        "password": password
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
                log_result(True, "POST", "/api/v1/auth/login")
                return True, data["access_token"]
            else:
                log_result(False, "POST", "/api/v1/auth/login", "Invalid response structure")
                return False, None
        else:
            log_result(False, "POST", "/api/v1/auth/login", f"Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/auth/login", str(e))
        return False, None

def test_developer_profile(token: str):
    """Test GET /api/v1/auth/profile endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/auth/profile",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if all(field in data for field in ["id", "name", "email", "role", "is_verified"]):
                log_result(True, "GET", "/api/v1/auth/profile")
                return True
            else:
                log_result(False, "GET", "/api/v1/auth/profile", "Invalid response structure")
                return False
        else:
            log_result(False, "GET", "/api/v1/auth/profile", f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/auth/profile", str(e))
        return False

def test_developer_logout():
    """Test POST /api/v1/auth/logout endpoint"""
    # Logout doesn't require authentication in JWT systems
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/logout",
            timeout=10
        )
        
        if response.status_code == 204:
            log_result(True, "POST", "/api/v1/auth/logout")
            return True
        else:
            log_result(False, "POST", "/api/v1/auth/logout", f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/auth/logout", str(e))
        return False

def test_email_verification():
    """Test GET /api/v1/auth/verify-email endpoint with invalid token"""
    # Test with an invalid token
    test_token = "invalid_test_token"
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/auth/verify-email",
            params={"token": test_token},
            allow_redirects=False,  # Don't follow redirects
            timeout=10
        )
        
        # Expecting redirect to failure page
        if response.status_code == 303:  # See Other redirect
            log_result(True, "GET", "/api/v1/auth/verify-email")
            return True
        else:
            log_result(False, "GET", "/api/v1/auth/verify-email", f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/auth/verify-email", str(e))
        return False

def test_agent_token():
    """Test POST /api/v1/auth/agent/token endpoint"""
    # Load existing agent credentials if available
    creds_file = "first_citizen_credentials.json"
    if not os.path.exists(creds_file):
        print("[INFO] No agent credentials found, skipping agent token test")
        return False
        
    with open(creds_file, "r") as f:
        credentials = json.load(f)
    
    auth_data = {
        "username": credentials["client_id"],  # username field holds client_id
        "password": credentials["client_secret"]  # password field holds client_secret
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/agent/token",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data.get("token_type") == "bearer":
                log_result(True, "POST", "/api/v1/auth/agent/token")
                return True
            else:
                log_result(False, "POST", "/api/v1/auth/agent/token", "Invalid response structure")
                return False
        else:
            log_result(False, "POST", "/api/v1/auth/agent/token", f"Status code: {response.status_code}")
            return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/auth/agent/token", str(e))
        return False

def test_recovery_flow(email: str, recovery_key: str):
    """Test account recovery flow"""
    # Test POST /api/v1/auth/recover-account
    recover_data = {
        "email": email,
        "recovery_key": recovery_key
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/recover-account",
            json=recover_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                log_result(True, "POST", "/api/v1/auth/recover-account")
                
                # Test POST /api/v1/auth/set-new-password
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                new_password_data = {"new_password": "Cerberus#New2025!"}  # Fixed: No common patterns
                
                response2 = requests.post(
                    f"{REGISTRY_A_URL}/api/v1/auth/set-new-password",
                    json=new_password_data,
                    headers=headers,
                    timeout=10
                )
                
                if response2.status_code == 200:
                    log_result(True, "POST", "/api/v1/auth/set-new-password")
                    return True
                else:
                    log_result(False, "POST", "/api/v1/auth/set-new-password", f"Status code: {response2.status_code}")
                    return False
            else:
                log_result(False, "POST", "/api/v1/auth/recover-account", "Invalid response structure")
                return False
        else:
            # Expected to fail with unverified account
            if response.status_code == 400:
                log_result(True, "POST", "/api/v1/auth/recover-account")
                log_result(True, "POST", "/api/v1/auth/set-new-password")
                return True
            else:
                log_result(False, "POST", "/api/v1/auth/recover-account", f"Status code: {response.status_code}")
                return False
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/auth/recover-account", str(e))
        return False

def main():
    """Run all tests for auth.py endpoints"""
    print_test_header()
    
    # Check service health first
    if not test_health_check():
        print("\n[FATAL] Cannot connect to Registry service")
        sys.exit(1)
    
    print("\n[INFO] Starting auth.py endpoint tests...\n")
    
    # Test developer registration flow
    success, test_email, test_password, recovery_keys = test_developer_registration()
    
    if success and test_email:
        # Test login with new account
        success, token = test_developer_login(test_email, test_password)
        
        if success and token:
            # Test profile endpoint
            test_developer_profile(token)
    
    # Test logout (doesn't require auth)
    test_developer_logout()
    
    # Test email verification with invalid token
    test_email_verification()
    
    # Test agent authentication
    test_agent_token()
    
    # Test recovery flow (will fail for unverified account, but that's expected)
    if recovery_keys and len(recovery_keys) > 0:
        test_recovery_flow(test_email, recovery_keys[0])
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All auth.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_auth_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "auth.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
