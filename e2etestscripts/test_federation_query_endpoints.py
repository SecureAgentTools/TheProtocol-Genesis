#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for federation_query.py endpoints
==================================================================
This script tests all endpoints in the federation_query router.
This router provides internal federation query endpoints for peer registries.
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
    print("  OPERATION CERBERUS: federation_query.py Endpoint Tests")
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

def test_federation_query_no_auth():
    """Test POST /internal/federation/query without authentication"""
    headers = {"Content-Type": "application/json"}
    
    print("[INFO] Testing federation query without authentication")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/internal/federation/query",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            log_result(True, "POST", "/internal/federation/query (no auth)", 
                      "Correctly requires authentication")
        elif response.status_code == 422:
            # FastAPI returns 422 when required header is missing
            log_result(True, "POST", "/internal/federation/query (no auth)", 
                      "Correctly requires authentication (422 - missing header)")
        else:
            log_result(False, "POST", "/internal/federation/query (no auth)", 
                      f"Expected 401 or 422, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/internal/federation/query (no auth)", str(e))

def test_federation_query_invalid_auth():
    """Test POST /internal/federation/query with invalid authentication format"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "InvalidFormat"
    }
    
    print("[INFO] Testing federation query with invalid auth format")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/internal/federation/query",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            log_result(True, "POST", "/internal/federation/query (invalid auth)", 
                      "Correctly rejects invalid auth format")
        else:
            log_result(False, "POST", "/internal/federation/query (invalid auth)", 
                      f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/internal/federation/query (invalid auth)", str(e))

def test_federation_query_empty_token():
    """Test POST /internal/federation/query with empty Bearer token"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "
    }
    
    print("[INFO] Testing federation query with empty Bearer token")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/internal/federation/query",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            log_result(True, "POST", "/internal/federation/query (empty token)", 
                      "Correctly rejects empty token")
        else:
            log_result(False, "POST", "/internal/federation/query (empty token)", 
                      f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/internal/federation/query (empty token)", str(e))

def test_federation_query_with_dummy_token():
    """Test POST /internal/federation/query with dummy token (simulating peer auth)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-federation-token"
    }
    
    print("[INFO] Testing federation query with dummy Bearer token")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/internal/federation/query",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check required fields in response
            if "items" in data and "pagination" in data:
                if isinstance(data["items"], list) and isinstance(data["pagination"], dict):
                    log_result(True, "POST", "/internal/federation/query (dummy token)")
                else:
                    log_result(False, "POST", "/internal/federation/query (dummy token)", 
                              "Invalid response structure")
            else:
                log_result(False, "POST", "/internal/federation/query (dummy token)", 
                          f"Missing required fields: {data}")
        else:
            log_result(False, "POST", "/internal/federation/query (dummy token)", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/internal/federation/query (dummy token)", str(e))

def test_federation_query_with_search():
    """Test POST /internal/federation/query with search parameter"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-federation-token"
    }
    
    params = {
        "search": "test",
        "limit": 10,
        "offset": 0
    }
    
    print("[INFO] Testing federation query with search parameter")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/internal/federation/query",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and "pagination" in data:
                pagination = data["pagination"]
                # Check pagination fields
                required_pagination_fields = ["total_items", "limit", "offset", "total_pages", "current_page"]
                if all(field in pagination for field in required_pagination_fields):
                    log_result(True, "POST", "/internal/federation/query (with search)")
                else:
                    missing = [f for f in required_pagination_fields if f not in pagination]
                    log_result(False, "POST", "/internal/federation/query (with search)", 
                              f"Missing pagination fields: {missing}")
            else:
                log_result(False, "POST", "/internal/federation/query (with search)", 
                          f"Missing required fields: {data}")
        else:
            log_result(False, "POST", "/internal/federation/query (with search)", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/internal/federation/query (with search)", str(e))

def test_federation_query_with_filters():
    """Test POST /internal/federation/query with various filters"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-federation-token"
    }
    
    params = {
        "tags": ["ai", "agent"],
        "active_only": True,
        "has_tee": True,
        "limit": 5
    }
    
    print("[INFO] Testing federation query with multiple filters")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/internal/federation/query",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and isinstance(data["items"], list):
                # Each item should have origin_registry_name field
                if len(data["items"]) > 0:
                    # Check first item structure
                    first_item = data["items"][0]
                    if "origin_registry_name" in first_item:
                        log_result(True, "POST", "/internal/federation/query (with filters)")
                    else:
                        log_result(False, "POST", "/internal/federation/query (with filters)", 
                                  "Missing origin_registry_name in items")
                else:
                    # Empty result is valid
                    log_result(True, "POST", "/internal/federation/query (with filters)", 
                              "Empty results (no matching agents)")
            else:
                log_result(False, "POST", "/internal/federation/query (with filters)", 
                          "Invalid response structure")
        else:
            log_result(False, "POST", "/internal/federation/query (with filters)", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/internal/federation/query (with filters)", str(e))

def main():
    """Run all tests for federation_query.py endpoints"""
    print_test_header()
    
    print("[NOTE] Federation query is an internal endpoint for peer registries")
    print("[NOTE] Requires Bearer token authentication (any non-empty token accepted in test mode)\n")
    
    # Run all endpoint tests
    test_federation_query_no_auth()
    test_federation_query_invalid_auth()
    test_federation_query_empty_token()
    test_federation_query_with_dummy_token()
    test_federation_query_with_search()
    test_federation_query_with_filters()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All federation_query.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_federation_query_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "federation_query.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
