"""
Test script for Enhanced Staking endpoints (staking_enhanced router).
Tests the Beta Strike enhanced staking features.
"""
import urllib.request
import urllib.error
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test data
TEST_DID = f"did:key:test_staking_{int(time.time())}"


def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request using urllib"""
    if headers is None:
        headers = {}
    
    if data and method in ["POST", "PUT", "PATCH"]:
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode('utf-8')
    
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(request) as response:
            response_data = response.read()
            return {
                "status": response.status,
                "data": json.loads(response_data.decode()) if response_data else {},
                "headers": dict(response.headers)
            }
    except urllib.error.HTTPError as e:
        error_data = e.read()
        try:
            error_json = json.loads(error_data.decode()) if error_data else {}
        except:
            error_json = {"error": error_data.decode() if error_data else "Unknown error"}
        return {
            "status": e.code,
            "data": error_json,
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": 0,
            "error": str(e)
        }


def test_staking_enhanced_endpoints():
    """Test all enhanced staking endpoints"""
    print("\n" + "="*60)
    print("OPERATION CERBERUS - STAKING ENHANCED TESTING")
    print("Testing Enhanced Staking Endpoints")
    print("="*60 + "\n")
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "endpoints": {}
    }
    
    # Test 1: GET /staking/balance
    print("Testing GET /staking/balance...")
    results["total"] += 1
    
    response = make_request(f"{BASE_URL}{API_PREFIX}/staking/balance?agent_did={TEST_DID}")
    
    if response["status"] in [200, 401]:
        results["passed"] += 1
        print(f"[PASS] Balance endpoint accessible (status: {response['status']})")
    else:
        results["failed"] += 1
        print(f"[FAIL] Balance endpoint failed: {response['status']}")
    
    results["endpoints"]["GET /staking/balance"] = response["status"]
    
    # Test 2: GET /staking/status
    print("\nTesting GET /staking/status...")
    results["total"] += 1
    
    response = make_request(f"{BASE_URL}{API_PREFIX}/staking/status")
    
    if response["status"] in [200, 401]:
        results["passed"] += 1
        print(f"[PASS] Status endpoint accessible (status: {response['status']})")
    else:
        results["failed"] += 1
        print(f"[FAIL] Status endpoint failed: {response['status']}")
    
    results["endpoints"]["GET /staking/status"] = response["status"]
    
    # Test 3: POST /staking/stake (requires auth)
    print("\nTesting POST /staking/stake...")
    results["total"] += 1
    
    stake_data = {
        "amount": 100,
        "idempotency_key": f"stake_{int(time.time())}"
    }
    
    response = make_request(
        f"{BASE_URL}{API_PREFIX}/staking/stake",
        method="POST",
        data=stake_data
    )
    
    if response["status"] in [200, 201, 401]:
        results["passed"] += 1
        print(f"[PASS] Stake endpoint accessible (status: {response['status']})")
    else:
        results["failed"] += 1
        print(f"[FAIL] Stake endpoint failed: {response['status']}")
    
    results["endpoints"]["POST /staking/stake"] = response["status"]
    
    # Test 4: POST /staking/unstake (requires auth)
    print("\nTesting POST /staking/unstake...")
    results["total"] += 1
    
    unstake_data = {
        "amount": 50
    }
    
    response = make_request(
        f"{BASE_URL}{API_PREFIX}/staking/unstake",
        method="POST",
        data=unstake_data
    )
    
    if response["status"] in [200, 201, 401]:
        results["passed"] += 1
        print(f"[PASS] Unstake endpoint accessible (status: {response['status']})")
    else:
        results["failed"] += 1
        print(f"[FAIL] Unstake endpoint failed: {response['status']}")
    
    results["endpoints"]["POST /staking/unstake"] = response["status"]
    
    # Summary
    print("\n" + "="*60)
    print("STAKING ENHANCED TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
    
    print("\nEndpoint Results:")
    for endpoint, status in results['endpoints'].items():
        status_text = "[PASS]" if status in [200, 201, 401] else "[FAIL]"
        print(f"  {status_text} {endpoint}: {status}")
    
    return results


if __name__ == "__main__":
    test_staking_enhanced_endpoints()
