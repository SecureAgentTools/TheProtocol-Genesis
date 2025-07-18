#!/usr/bin/env python3
"""
Test script for disputes endpoints.

Tests the Decentralized Dispute Resolution (DDR) system endpoints that allow
agents to file disputes and submit evidence.
"""

import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Base configuration
BASE_URL = "http://localhost:8000"  # Note: no /api/v1 prefix based on router

# Test results storage
test_results = {
    "router": "disputes.py",
    "test_file": "test_disputes_endpoints.py",
    "start_time": datetime.now().isoformat(),
    "tests": []
}

# Track created resources
created_resources = {
    "dispute_id": None,
    "evidence_id": None
}

# Test agent DIDs (using some common test DIDs)
TEST_COMPLAINANT_DID = "did:cos:test_complainant_12345"
TEST_DEFENDANT_DID = "did:cos:test_defendant_67890"
TEST_THIRD_PARTY_DID = "did:cos:test_third_party_11111"

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

def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request using urllib"""
    if headers is None:
        headers = {}
    
    # Prepare data
    if data:
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

def test_create_dispute():
    """Test: POST /api/v1/disputes/"""
    endpoint = "/api/v1/disputes/"  # Fixed: Added trailing slash
    method = "POST"
    
    request_data = {
        "complainant_did": TEST_COMPLAINANT_DID,
        "defendant_did": TEST_DEFENDANT_DID
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data
    )
    
    if status == 201 and response:
        created_resources["dispute_id"] = response["id"]
        log_test(endpoint, method, status, True, 
                f"Successfully created dispute (ID: {response['id']})", 
                request_data, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to create dispute: {error}", request_data, error)

def test_create_dispute_same_agent():
    """Test: POST /api/v1/disputes/ with same agent as complainant and defendant"""
    endpoint = "/api/v1/disputes/"  # Fixed: Added trailing slash
    method = "POST"
    
    request_data = {
        "complainant_did": TEST_COMPLAINANT_DID,
        "defendant_did": TEST_COMPLAINANT_DID  # Same as complainant
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data
    )
    
    if status == 400:
        log_test(endpoint, method, status, True, 
                "Correctly rejected dispute with same complainant and defendant", 
                request_data, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 400, got {status}", request_data, error or response)

def test_get_dispute():
    """Test: GET /api/v1/disputes/{dispute_id}"""
    if not created_resources["dispute_id"]:
        log_test("/api/v1/disputes/{dispute_id}", "GET", 0, False, 
                "No dispute created to test")
        return
    
    endpoint = f"/api/v1/disputes/{created_resources['dispute_id']}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                f"Retrieved dispute details", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get dispute: {error}", None, error)

def test_get_nonexistent_dispute():
    """Test: GET /api/v1/disputes/{dispute_id} for non-existent dispute"""
    endpoint = "/api/v1/disputes/99999"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 404:
        log_test(endpoint, method, status, True, 
                "Correctly returned 404 for non-existent dispute", None, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 404, got {status}", None, error or response)

def test_submit_evidence():
    """Test: POST /api/v1/disputes/{dispute_id}/evidence"""
    if not created_resources["dispute_id"]:
        log_test("/api/v1/disputes/{dispute_id}/evidence", "POST", 0, False, 
                "No dispute created to test")
        return
    
    endpoint = f"/api/v1/disputes/{created_resources['dispute_id']}/evidence"
    method = "POST"
    
    request_data = {
        "submitter_did": TEST_COMPLAINANT_DID,
        "evidence_data": {
            "type": "screenshot",
            "description": "Screenshot of the incident",
            "url": "https://example.com/evidence/screenshot1.png",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data
    )
    
    if status == 201 and response:
        created_resources["evidence_id"] = response["id"]
        log_test(endpoint, method, status, True, 
                f"Successfully submitted evidence (ID: {response['id']})", 
                request_data, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to submit evidence: {error}", request_data, error)

def test_submit_evidence_by_defendant():
    """Test: Submit evidence by defendant"""
    if not created_resources["dispute_id"]:
        log_test("/api/v1/disputes/{dispute_id}/evidence", "POST", 0, False, 
                "No dispute created to test")
        return
    
    endpoint = f"/api/v1/disputes/{created_resources['dispute_id']}/evidence"
    method = "POST"
    
    request_data = {
        "submitter_did": TEST_DEFENDANT_DID,
        "evidence_data": {
            "type": "logs",
            "description": "System logs showing normal operation",
            "content": "2025-07-15 10:00:00 - All systems normal",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data
    )
    
    if status == 201 and response:
        log_test(endpoint, method, status, True, 
                "Defendant successfully submitted evidence", 
                request_data, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to submit evidence by defendant: {error}", 
                request_data, error)

def test_submit_evidence_by_third_party():
    """Test: Attempt to submit evidence by uninvolved third party"""
    if not created_resources["dispute_id"]:
        log_test("/api/v1/disputes/{dispute_id}/evidence", "POST", 0, False, 
                "No dispute created to test")
        return
    
    endpoint = f"/api/v1/disputes/{created_resources['dispute_id']}/evidence"
    method = "POST"
    
    request_data = {
        "submitter_did": TEST_THIRD_PARTY_DID,
        "evidence_data": {
            "type": "witness",
            "description": "I saw what happened"
        }
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data
    )
    
    if status == 403:
        log_test(endpoint, method, status, True, 
                "Correctly rejected evidence from third party", 
                request_data, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 403, got {status}", request_data, error or response)

def test_get_agent_disputes():
    """Test: GET /api/v1/disputes/agent/{agent_did}"""
    endpoint = f"/api/v1/disputes/agent/{TEST_COMPLAINANT_DID}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response is not None:
        # Response should be a list of dispute objects
        if isinstance(response, list):
            log_test(endpoint, method, status, True, 
                    f"Retrieved {len(response)} disputes for agent", None, response)
        else:
            log_test(endpoint, method, status, True, 
                    "Retrieved disputes for agent", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get agent disputes: {error}", None, error)

def test_get_agent_disputes_with_role():
    """Test: GET /api/v1/disputes/agent/{agent_did}?role=complainant"""
    endpoint = f"/api/v1/disputes/agent/{TEST_COMPLAINANT_DID}?role=complainant"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response is not None:
        # Response should be a list of dispute objects
        if isinstance(response, list):
            log_test(endpoint, method, status, True, 
                    f"Retrieved {len(response)} disputes as complainant", None, response)
        else:
            log_test(endpoint, method, status, True, 
                    "Retrieved disputes as complainant", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get filtered disputes: {error}", None, error)

def test_get_agent_disputes_invalid_role():
    """Test: GET /api/v1/disputes/agent/{agent_did}?role=invalid"""
    endpoint = f"/api/v1/disputes/agent/{TEST_COMPLAINANT_DID}?role=observer"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 400:
        log_test(endpoint, method, status, True, 
                "Correctly rejected invalid role parameter", None, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 400, got {status}", None, error or response)

def run_all_tests():
    """Run all disputes endpoint tests"""
    print("\n" + "="*50)
    print("TESTING DISPUTES ENDPOINTS")
    print("="*50)
    
    # Run tests
    test_create_dispute()
    test_create_dispute_same_agent()
    test_get_dispute()
    test_get_nonexistent_dispute()
    test_submit_evidence()
    test_submit_evidence_by_defendant()
    test_submit_evidence_by_third_party()
    test_get_agent_disputes()
    test_get_agent_disputes_with_role()
    test_get_agent_disputes_invalid_role()
    
    # Summary
    test_results["end_time"] = datetime.now().isoformat()
    total_tests = len(test_results["tests"])
    passed_tests = sum(1 for t in test_results["tests"] if t["success"])
    
    print("\n" + "="*50)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    print("="*50)
    
    # Save detailed results (fixed for Windows)
    with open("test_disputes_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    # Return exit code
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
