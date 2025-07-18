#!/usr/bin/env python3
"""
Test script for onboarding endpoints - using urllib instead of requests.
"""

import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
DEVELOPER_EMAIL = f"onboard_test_{int(time.time())}@example.com"
DEVELOPER_PASSWORD = "Test123!Pass"
DEVELOPER_NAME = f"OnboardTest_{int(time.time())}"

# Test results storage
test_results = {
    "router": "onboarding.py",
    "test_file": "test_onboarding_endpoints.py",
    "start_time": datetime.now().isoformat(),
    "tests": []
}

# Track created resources
created_resources = {
    "developer_token": None,
    "bootstrap_token": None,
    "agent_did": None,
    "agent_credentials": None
}

def log_test(endpoint, method, status_code, success, error_msg="", request_data=None, response_data=None):
    """Log test results"""
    test_results["tests"].append({
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "success": success,
        "error": error_msg,
        "request_data": request_data,
        "response_data": response_data,
        "timestamp": datetime.now().isoformat()
    })
    
    status = "[PASS] PASS" if success else "[FAIL] FAIL"
    print(f"{status} | {method} {endpoint} | Status: {status_code} | {error_msg}")

def make_request(url, method="GET", data=None, headers=None, is_form_data=False):
    """Make HTTP request using urllib"""
    if headers is None:
        headers = {}
    
    # Prepare data
    if data:
        if is_form_data:
            # URL encode form data
            data = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            # JSON encode
            data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
    
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        response = urllib.request.urlopen(request)
        status_code = response.getcode()
        response_data = json.loads(response.read().decode('utf-8'))
        return status_code, response_data, None
    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            error_data = json.loads(e.read().decode('utf-8'))
        except:
            error_data = {"detail": str(e)}
        return status_code, None, error_data
    except Exception as e:
        return 0, None, {"detail": str(e)}

def test_request_bootstrap_token():
    """Test: POST /onboard/bootstrap/request-token"""
    endpoint = "/onboard/bootstrap/request-token"
    method = "POST"
    
    # First, let's try with the default test developer
    print("\nTrying to authenticate with default test developer...")
    
    # Login with default test developer
    login_data = {
        "username": "test@example.com",
        "password": "securepassword123",
        "grant_type": "password"
    }
    
    status, response, error = make_request(
        f"{BASE_URL}/auth/login",
        method="POST",
        data=login_data,
        is_form_data=True
    )
    
    if status == 200 and response:
        token = response.get("access_token")
        if token:
            created_resources["developer_token"] = token
            print("Successfully authenticated as test developer")
            
            # Now request bootstrap token
            headers = {"Authorization": f"Bearer {token}"}
            request_data = {
                "agent_type_hint": "test_agent",
                "requested_by": "onboarding_test"
            }
            
            status, response, error = make_request(
                f"{BASE_URL}{endpoint}",
                method="POST",
                data=request_data,
                headers=headers
            )
            
            if status == 200 and response:
                created_resources["bootstrap_token"] = response["bootstrap_token"]
                log_test(endpoint, method, status, True, 
                        "Successfully got bootstrap token", request_data, response)
            else:
                log_test(endpoint, method, status, False, 
                        f"Failed to get bootstrap token: {error}", request_data, error)
    else:
        log_test("/auth/login", "POST", status, False, 
                f"Failed to authenticate: {error}", login_data, error)

def test_register_agent_deprecated():
    """Test: POST /onboard/register (deprecated endpoint)"""
    endpoint = "/onboard/register"
    method = "POST"
    
    if not created_resources["bootstrap_token"]:
        log_test(endpoint, method, 0, False, "No bootstrap token available")
        return
    
    # Test agent registration
    request_data = {
        "agent_did_method": "cos",
        "public_key_jwk": {
            "kty": "RSA",
            "n": "test_key_n",
            "e": "AQAB"
        }
    }
    
    headers = {"Bootstrap-Token": created_resources["bootstrap_token"]}
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data,
        headers=headers
    )
    
    if status == 201 and response:
        created_resources["agent_did"] = response["agent_did"]
        created_resources["agent_credentials"] = {
            "client_id": response["client_id"],
            "client_secret": response["client_secret"]
        }
        log_test(endpoint, method, status, True, 
                "Successfully registered agent", request_data, response)
    elif status == 409:
        log_test(endpoint, method, status, True, 
                "Bootstrap token already used (expected)", request_data, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Registration failed: {error}", request_data, error)

def test_register_with_used_token():
    """Test: Attempt to reuse a bootstrap token"""
    endpoint = "/onboard/register"
    method = "POST"
    
    if not created_resources["bootstrap_token"]:
        log_test(endpoint, method, 0, False, "No bootstrap token to test reuse")
        return
    
    # Try to use the same token again
    request_data = {
        "agent_did_method": "cos",
        "public_key_jwk": None
    }
    
    headers = {"Bootstrap-Token": created_resources["bootstrap_token"]}
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data,
        headers=headers
    )
    
    if status == 409:
        log_test(endpoint, method, status, True, 
                "Correctly rejected reused token", request_data, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 409, got {status}: {error}", request_data, error)

def test_create_agent_with_card():
    """Test: POST /onboard/create_agent (new unified endpoint)"""
    endpoint = "/onboard/create_agent"
    method = "POST"
    
    # Need a fresh bootstrap token
    print("\nGetting fresh bootstrap token for create_agent test...")
    
    if created_resources["developer_token"]:
        headers = {"Authorization": f"Bearer {created_resources['developer_token']}"}
        
        # Request new bootstrap token
        status, response, error = make_request(
            f"{BASE_URL}/onboard/bootstrap/request-token",
            method="POST",
            data={"agent_type_hint": "agent_with_card"},
            headers=headers
        )
        
        if status == 200 and response:
            bootstrap_token = response["bootstrap_token"]
            
            # Create agent with card
            request_data = {
                "agent_did_method": "cos",
                "public_key_jwk": {
                    "kty": "RSA",
                    "n": "test_key_n_2",
                    "e": "AQAB"
                },
                "agent_card": {
                    "name": "Test Agent With Card",
                    "description": "An agent created through the unified endpoint",
                    "capabilities": ["test", "demo"],
                    "version": "1.0.0",
                    "author": "test_developer",
                    "tags": ["test", "onboarding"],
                    "endpoints": {
                        "api": "http://test-agent:8000"
                    }
                }
            }
            
            headers = {"Bootstrap-Token": bootstrap_token}
            
            status, response, error = make_request(
                f"{BASE_URL}{endpoint}",
                method="POST",
                data=request_data,
                headers=headers
            )
            
            if status == 201 and response:
                log_test(endpoint, method, status, True, 
                        "Successfully created agent with card", request_data, response)
            else:
                log_test(endpoint, method, status, False, 
                        f"Failed to create agent: {error}", request_data, error)
        else:
            log_test(endpoint, method, 0, False, 
                    f"Could not get bootstrap token: {error}")
    else:
        log_test(endpoint, method, 0, False, "No developer token available")

def test_invalid_bootstrap_token():
    """Test: Use invalid bootstrap token"""
    endpoint = "/onboard/register"
    method = "POST"
    
    request_data = {
        "agent_did_method": "cos"
    }
    
    headers = {"Bootstrap-Token": "bst_invalid_token_12345"}
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data,
        headers=headers
    )
    
    if status == 401:
        log_test(endpoint, method, status, True, 
                "Correctly rejected invalid token", request_data, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 401, got {status}", request_data, error)

def run_all_tests():
    """Run all onboarding endpoint tests"""
    print("\n" + "="*50)
    print("TESTING ONBOARDING ENDPOINTS")
    print("="*50)
    
    # Run tests
    test_request_bootstrap_token()
    test_register_agent_deprecated()
    test_register_with_used_token()
    test_create_agent_with_card()
    test_invalid_bootstrap_token()
    
    # Summary
    test_results["end_time"] = datetime.now().isoformat()
    total_tests = len(test_results["tests"])
    passed_tests = sum(1 for t in test_results["tests"] if t["success"])
    
    print("\n" + "="*50)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    print("="*50)
    
    # Save detailed results
    with open("/tmp/test_onboarding_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    # Return exit code
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
