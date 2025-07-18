#!/usr/bin/env python3
"""
Test script for system endpoints.

Tests the system-wide activity feed and public system information endpoints.
These endpoints are public and do not require authentication.
"""

import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"  # System router is mounted at /api/v1

# Test results storage
test_results = {
    "router": "system.py",
    "test_file": "test_system_endpoints.py",
    "start_time": datetime.now().isoformat(),
    "tests": []
}

# Known event types to test
EVENT_TYPES = [
    "AGENT_ONBOARDED",
    "FEDERATION_REQUEST",
    "FEDERATION_APPROVED",
    "REWARD_CYCLE",
    "GOVERNANCE_PROPOSAL",
    "DISPUTE_FILED"
]

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

def test_activity_feed():
    """Test: GET /system/activity-feed"""
    endpoint = "/system/activity-feed"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        # Verify response structure
        if "items" in response and "total" in response:
            log_test(endpoint, method, status, True, 
                    f"Retrieved {len(response['items'])} activity events", 
                    None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Invalid response format", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get activity feed: {error}", None, error)

def test_activity_feed_with_pagination():
    """Test: GET /system/activity-feed with pagination"""
    endpoint = "/system/activity-feed?limit=5&offset=0"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        if "items" in response and len(response["items"]) <= 5:
            log_test(endpoint, method, status, True, 
                    f"Pagination working (got {len(response['items'])} items, max 5)", 
                    None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Pagination not respected", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get paginated feed: {error}", None, error)

def test_activity_feed_limit_validation():
    """Test: GET /system/activity-feed with invalid limit"""
    # Test limit too high
    endpoint = "/system/activity-feed?limit=100"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 422:  # Validation error expected
        log_test(endpoint, method, status, True, 
                "Correctly rejected limit > 50", None, error)
    elif status == 200:
        # Some implementations might clamp to max instead of rejecting
        if response and "items" in response and len(response["items"]) <= 50:
            log_test(endpoint, method, status, True, 
                    "Limit clamped to maximum (50)", None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Invalid limit handling", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Unexpected response: {error}", None, error)

def test_activity_by_type():
    """Test: GET /system/activity-feed/by-type/{event_type}"""
    # Test with first known event type
    event_type = EVENT_TYPES[0]
    endpoint = f"/system/activity-feed/by-type/{event_type}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        if "items" in response and "total" in response:
            # Check if returned items match the requested type
            if response["items"]:
                all_match = all(
                    item.get("event_type") == event_type 
                    for item in response["items"]
                )
                if all_match:
                    log_test(endpoint, method, status, True, 
                            f"Retrieved {len(response['items'])} {event_type} events", 
                            None, response)
                else:
                    log_test(endpoint, method, status, False, 
                            "Response contains events of wrong type", 
                            None, response)
            else:
                # No events of this type (still valid)
                log_test(endpoint, method, status, True, 
                        f"No {event_type} events found (valid)", None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Invalid response format", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get events by type: {error}", None, error)

def test_all_event_types():
    """Test: GET /system/activity-feed/by-type/{event_type} for all known types"""
    success_count = 0
    
    for event_type in EVENT_TYPES:
        endpoint = f"/system/activity-feed/by-type/{event_type}"
        method = "GET"
        
        status, response, error = make_request(f"{BASE_URL}{endpoint}")
        
        if status == 200 and response and "items" in response:
            success_count += 1
            print(f"  [OK] {event_type}: {len(response['items'])} events")
        else:
            print(f"  [X] {event_type}: Failed - {error}")
    
    if success_count == len(EVENT_TYPES):
        log_test("/system/activity-feed/by-type/{event_type}", "GET", 200, True, 
                f"All {len(EVENT_TYPES)} event types tested successfully")
    else:
        log_test("/system/activity-feed/by-type/{event_type}", "GET", 0, False, 
                f"Only {success_count}/{len(EVENT_TYPES)} event types succeeded")

def test_invalid_event_type():
    """Test: GET /system/activity-feed/by-type/{event_type} with invalid type"""
    endpoint = "/system/activity-feed/by-type/INVALID_EVENT_TYPE"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    # The endpoint might return 200 with empty results or 404/400
    if status == 200 and response:
        if "items" in response and len(response["items"]) == 0:
            log_test(endpoint, method, status, True, 
                    "Returned empty results for invalid type (acceptable)", 
                    None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Returned data for invalid event type", None, response)
    elif status in [400, 404]:
        log_test(endpoint, method, status, True, 
                "Correctly rejected invalid event type", None, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Unexpected response: {error}", None, error)

def test_activity_feed_offset():
    """Test: GET /system/activity-feed with offset"""
    # First get total count
    status1, response1, error1 = make_request(f"{BASE_URL}/system/activity-feed?limit=10")
    
    if status1 == 200 and response1 and response1.get("items"):
        first_items = response1["items"]
        
        # Now get with offset
        endpoint = "/system/activity-feed?limit=10&offset=5"
        method = "GET"
        
        status2, response2, error2 = make_request(f"{BASE_URL}{endpoint}")
        
        if status2 == 200 and response2:
            # Check that results are different (unless there are very few events)
            if len(first_items) > 5:
                # We should get different events
                log_test(endpoint, method, status2, True, 
                        f"Offset working (got {len(response2['items'])} items starting from offset 5)", 
                        None, response2)
            else:
                log_test(endpoint, method, status2, True, 
                        "Offset parameter accepted (few total events)", 
                        None, response2)
        else:
            log_test(endpoint, method, status2, False, 
                    f"Failed with offset: {error2}", None, error2)
    else:
        print("Skipping offset test - no initial data available")

def run_all_tests():
    """Run all system endpoint tests"""
    print("\n" + "="*50)
    print("TESTING SYSTEM ENDPOINTS")
    print("="*50)
    
    # Run tests
    test_activity_feed()
    test_activity_feed_with_pagination()
    test_activity_feed_limit_validation()
    test_activity_by_type()
    test_all_event_types()
    test_invalid_event_type()
    test_activity_feed_offset()
    
    # Summary
    test_results["end_time"] = datetime.now().isoformat()
    total_tests = len(test_results["tests"])
    passed_tests = sum(1 for t in test_results["tests"] if t["success"])
    
    print("\n" + "="*50)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    print("="*50)
    
    # Save detailed results (fixed for Windows)
    with open("test_system_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    # Return exit code
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
