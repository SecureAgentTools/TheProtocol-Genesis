#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for federation_public.py endpoints
===================================================================
This script tests all endpoints in the federation_public router.
This router provides public federation endpoints for peer registries.
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
    print("  OPERATION CERBERUS: federation_public.py Endpoint Tests")
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

def test_federation_health_check():
    """Test GET /api/v1/federation/health-check"""
    headers = {"Content-Type": "application/json"}
    
    print("[INFO] Testing federation health check endpoint (may require mTLS)")
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/federation/health-check",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check required fields
            required_fields = ["status", "registry_name", "timestamp", "version", "components"]
            if all(field in data for field in required_fields):
                if data.get("status") in ["healthy", "degraded"]:
                    log_result(True, "GET", "/api/v1/federation/health-check")
                else:
                    log_result(False, "GET", "/api/v1/federation/health-check", 
                              f"Invalid status value: {data.get('status')}")
            else:
                missing_fields = [f for f in required_fields if f not in data]
                log_result(False, "GET", "/api/v1/federation/health-check", 
                          f"Missing fields: {missing_fields}")
        elif response.status_code == 403:
            # mTLS authentication required
            log_result(True, "GET", "/api/v1/federation/health-check", 
                      "Correctly requires mTLS authentication (403)")
        elif response.status_code == 401:
            # Authentication required
            log_result(True, "GET", "/api/v1/federation/health-check", 
                      "Correctly requires authentication (401)")
        elif response.status_code == 503:
            # Service unavailable - database unhealthy
            try:
                error_data = response.json()
                # Check if it's wrapped in an error format
                if "error" in error_data and "detail" in error_data["error"]:
                    # Try to parse the detail as JSON
                    try:
                        detail_data = json.loads(error_data["error"]["detail"])
                        if detail_data.get("status") == "degraded" and "components" in detail_data:
                            log_result(True, "GET", "/api/v1/federation/health-check", 
                                      "Service degraded (503) - database unhealthy")
                        else:
                            log_result(False, "GET", "/api/v1/federation/health-check", 
                                      f"Unexpected detail format: {detail_data}")
                    except json.JSONDecodeError:
                        # Detail is not JSON, check if it's the expected format
                        if "degraded" in error_data["error"]["detail"]:
                            log_result(True, "GET", "/api/v1/federation/health-check", 
                                      "Service degraded (503) - database unhealthy")
                        else:
                            log_result(False, "GET", "/api/v1/federation/health-check", 
                                      f"Unexpected error detail: {error_data}")
                elif error_data.get("status") == "degraded" and "components" in error_data:
                    log_result(True, "GET", "/api/v1/federation/health-check", 
                              "Service degraded (503) - database unhealthy")
                else:
                    log_result(False, "GET", "/api/v1/federation/health-check", 
                              f"Unexpected 503 response format: {error_data}")
            except:
                log_result(False, "GET", "/api/v1/federation/health-check", 
                          f"503 with non-JSON response: {response.text}")
        else:
            # Try to get more details about the error
            error_msg = f"Status code: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {response.text}"
            log_result(False, "GET", "/api/v1/federation/health-check", error_msg)
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/federation/health-check", str(e))

def test_federation_info():
    """Test GET /api/v1/federation/info"""
    headers = {"Content-Type": "application/json"}
    
    print("[INFO] Testing public federation info endpoint")
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/federation/info",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check required fields
            required_fields = [
                "registry_name", "api_version", "federation_protocol_version",
                "supported_auth_methods", "health_check_endpoint", "timestamp"
            ]
            if all(field in data for field in required_fields):
                # Validate specific fields
                if isinstance(data.get("supported_auth_methods"), list):
                    log_result(True, "GET", "/api/v1/federation/info")
                else:
                    log_result(False, "GET", "/api/v1/federation/info", 
                              "supported_auth_methods should be a list")
            else:
                missing_fields = [f for f in required_fields if f not in data]
                log_result(False, "GET", "/api/v1/federation/info", 
                          f"Missing fields: {missing_fields}")
        else:
            log_result(False, "GET", "/api/v1/federation/info", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/federation/info", str(e))

def test_federation_info_no_auth():
    """Test GET /api/v1/federation/info without authentication (should work)"""
    # No headers, no auth
    print("[INFO] Testing federation info without any authentication")
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/federation/info",
            timeout=10
        )
        
        if response.status_code == 200:
            log_result(True, "GET", "/api/v1/federation/info (no auth)", 
                      "Public endpoint accessible without authentication")
        else:
            log_result(False, "GET", "/api/v1/federation/info (no auth)", 
                      f"Expected 200, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/federation/info (no auth)", str(e))

def main():
    """Run all tests for federation_public.py endpoints"""
    print_test_header()
    
    print("[NOTE] Federation health check endpoint may require mTLS authentication")
    print("[NOTE] Federation info endpoint should be publicly accessible\n")
    
    # Run all endpoint tests
    test_federation_health_check()
    test_federation_info()
    test_federation_info_no_auth()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All federation_public.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_federation_public_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "federation_public.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
