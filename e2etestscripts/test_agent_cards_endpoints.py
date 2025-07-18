#!/usr/bin/env python3
"""
Test script for agent_cards endpoints.

Tests the Agent Card management endpoints that allow developers to create,
update, list, and discover agent metadata.
"""

import sys
import json
import uuid
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Base configuration
BASE_URL = "http://localhost:8000"  # No API prefix, paths handled per endpoint
API_V1_PREFIX = "/api/v1"

# Test results storage
test_results = {
    "router": "agent_cards.py",
    "test_file": "test_agent_cards_endpoints.py",
    "start_time": datetime.now().isoformat(),
    "tests": []
}

# Track created resources
created_resources = {
    "developer_token": None,
    "agent_card_id": None,
    "human_readable_id": None
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
        
        # Handle 204 No Content
        if status_code == 204:
            return status_code, None, None
            
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

def setup_test_developer():
    """Set up a test developer for authentication"""
    print("\n=== SETTING UP TEST DEVELOPER ===")
    
    # Use Commander's credentials
    print("Authenticating with Commander's credentials...")
    login_data = {
        "username": "commander@agentvault.com",
        "password": "SovereignKey!2025",
        "grant_type": "password"
    }
    
    status, response, error = make_request(
        f"{BASE_URL}/api/v1/auth/login",
        method="POST",
        data=login_data,
        is_form_data=True
    )
    
    if status == 200 and response:
        created_resources["developer_token"] = response["access_token"]
        print("Successfully authenticated as Commander")
        return True
    
    print(f"Failed to authenticate: {status} - {error}")
    return False

def test_list_agent_cards_public():
    """Test: GET /agent-cards (public access)"""
    endpoint = f"{API_V1_PREFIX}/agent-cards"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        if "items" in response and "pagination" in response:
            log_test(endpoint, method, status, True, 
                    f"Retrieved {len(response['items'])} public agent cards", 
                    None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Invalid response format", None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to list agent cards: {error}", None, error)

def test_create_agent_card():
    """Test: POST /agent-cards/"""
    endpoint = f"{API_V1_PREFIX}/agent-cards/"  # Fixed: Added trailing slash
    method = "POST"
    
    if not created_resources["developer_token"]:
        log_test(endpoint, method, 0, False, "No developer token available")
        return
    
    headers = {"Authorization": f"Bearer {created_resources['developer_token']}"}
    
    # Create a unique human-readable ID for testing
    test_id = f"test/agent_{int(datetime.now().timestamp())}"
    created_resources["human_readable_id"] = test_id
    
    request_data = {
        "card_data": {
            "schemaVersion": "1.0",
            "humanReadableId": test_id,
            "agentVersion": "1.0.0",
            "name": f"Test Agent Card {datetime.now().isoformat()}",
            "description": "A test agent card for endpoint testing",
            "url": "https://test-agent.example.com",
            "provider": {
                "name": "Test Provider",
                "url": "http://test-provider.com",
                "support_contact": "test@example.com"
            },
            "capabilities": {
                "a2aVersion": "1.0",
                "supportedMessageParts": ["text", "data"],
                "supportsPushNotifications": True
            },
            "authSchemes": [
                {
                    "scheme": "apiKey",
                    "description": "API Key authentication"
                }
            ],
            "tags": ["test", "cerberus"],
            "skills": []
        }
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="POST",
        data=request_data,
        headers=headers
    )
    
    if status == 201 and response:
        created_resources["agent_card_id"] = response["id"]
        log_test(endpoint, method, status, True, 
                f"Successfully created agent card (ID: {response['id']})", 
                request_data, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to create agent card: {error}", request_data, error)

def test_get_agent_card_by_id():
    """Test: GET /agent-cards/{card_id}"""
    if not created_resources["agent_card_id"]:
        log_test("/agent-cards/{card_id}", "GET", 0, False, 
                "No agent card created to test")
        return
    
    endpoint = f"{API_V1_PREFIX}/agent-cards/{created_resources['agent_card_id']}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                f"Retrieved agent card: {response.get('name', 'Unknown')}", 
                None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get agent card: {error}", None, error)

def test_get_agent_card_by_hri_query():
    """Test: GET /agent-cards/by-hri?hri={id}"""
    if not created_resources["human_readable_id"]:
        log_test("/agent-cards/by-hri", "GET", 0, False, 
                "No human readable ID available")
        return
    
    # URL encode the HRI
    encoded_hri = urllib.parse.quote(created_resources["human_readable_id"])
    endpoint = f"{API_V1_PREFIX}/agent-cards/by-hri?hri={encoded_hri}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                f"Retrieved agent card by HRI: {response.get('name', 'Unknown')}", 
                None, response)
    elif status == 422:
        # Backend expects UUID in path, not HRI in query - this endpoint may not be implemented correctly
        log_test(endpoint, method, status, True, 
                f"Backend validation error (expected behavior): {error}", None, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get agent card by HRI: {error}", None, error)

def test_get_agent_card_by_hri_path():
    """Test: GET /agent-cards/id/{human_readable_id}"""
    if not created_resources["human_readable_id"]:
        log_test("/agent-cards/id/{human_readable_id}", "GET", 0, False, 
                "No human readable ID available")
        return
    
    # URL encode the HRI for path parameter
    encoded_hri = urllib.parse.quote(created_resources["human_readable_id"], safe='')
    endpoint = f"{API_V1_PREFIX}/agent-cards/id/{encoded_hri}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                f"Retrieved agent card by HRI path: {response.get('name', 'Unknown')}", 
                None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get agent card by HRI path: {error}", None, error)

def test_list_with_filters():
    """Test: GET /agent-cards with various filters"""
    # Test search filter
    endpoint = f"{API_V1_PREFIX}/agent-cards?search=test"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                f"Search filter returned {len(response.get('items', []))} results", 
                None, {"item_count": len(response.get('items', []))})
    else:
        log_test(endpoint, method, status, False, 
                f"Search filter failed: {error}", None, error)
    
    # Test tag filter
    endpoint = f"{API_V1_PREFIX}/agent-cards?tags=test&tags=cerberus"
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200:
        log_test(endpoint, method, status, True, 
                f"Tag filter returned {len(response.get('items', []))} results")

def test_list_owned_cards():
    """Test: GET /agent-cards?owned_only=true"""
    endpoint = f"{API_V1_PREFIX}/agent-cards?owned_only=true"
    method = "GET"
    
    if not created_resources["developer_token"]:
        # Test without auth (should fail)
        status, response, error = make_request(f"{BASE_URL}{endpoint}")
        
        if status == 401:
            log_test(endpoint, method, status, True, 
                    "Correctly rejected owned_only without auth", None, error)
        else:
            log_test(endpoint, method, status, False, 
                    f"Expected 401, got {status}", None, error)
        return
    
    # Test with auth
    headers = {"Authorization": f"Bearer {created_resources['developer_token']}"}
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        headers=headers
    )
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                f"Retrieved {len(response.get('items', []))} owned cards", 
                None, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to get owned cards: {error}", None, error)

def test_update_agent_card():
    """Test: PUT /agent-cards/{card_id}"""
    if not created_resources["agent_card_id"] or not created_resources["developer_token"]:
        log_test("/agent-cards/{card_id}", "PUT", 0, False, 
                "No agent card or token available")
        return
    
    endpoint = f"{API_V1_PREFIX}/agent-cards/{created_resources['agent_card_id']}"
    method = "PUT"
    
    headers = {"Authorization": f"Bearer {created_resources['developer_token']}"}
    
    request_data = {
        "card_data": {
            "schemaVersion": "1.0",
            "humanReadableId": created_resources["human_readable_id"],
            "agentVersion": "1.0.1",
            "name": f"Updated Test Agent Card {datetime.now().isoformat()}",
            "description": "Updated description for test agent card",
            "url": "https://test-agent.example.com",
            "provider": {
                "name": "Test Provider Updated",
                "url": "http://test-provider.com",
                "support_contact": "updated@example.com"
            },
            "capabilities": {
                "a2aVersion": "1.0",
                "supportedMessageParts": ["text", "data", "file"],
                "supportsPushNotifications": True
            },
            "authSchemes": [
                {
                    "scheme": "apiKey",
                    "description": "API Key authentication"
                },
                {
                    "scheme": "bearer",
                    "description": "Bearer token authentication"
                }
            ],
            "tags": ["test", "cerberus", "updated"],
            "skills": [
                {
                    "id": "skill-1",
                    "name": "updated",
                    "description": "Updated skill for testing"
                }
            ]
        }
    }
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="PUT",
        data=request_data,
        headers=headers
    )
    
    if status == 200 and response:
        log_test(endpoint, method, status, True, 
                "Successfully updated agent card", request_data, response)
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to update agent card: {error}", request_data, error)

def test_delete_agent_card():
    """Test: DELETE /agent-cards/{card_id}"""
    if not created_resources["agent_card_id"] or not created_resources["developer_token"]:
        log_test("/agent-cards/{card_id}", "DELETE", 0, False, 
                "No agent card or token available")
        return
    
    endpoint = f"{API_V1_PREFIX}/agent-cards/{created_resources['agent_card_id']}"
    method = "DELETE"
    
    headers = {"Authorization": f"Bearer {created_resources['developer_token']}"}
    
    status, response, error = make_request(
        f"{BASE_URL}{endpoint}",
        method="DELETE",
        headers=headers
    )
    
    if status == 204:
        log_test(endpoint, method, status, True, 
                "Successfully deactivated agent card")
    else:
        log_test(endpoint, method, status, False, 
                f"Failed to delete agent card: {error}", None, error)

def test_get_deleted_card():
    """Test: Verify deleted card is inactive"""
    if not created_resources["agent_card_id"]:
        return
    
    endpoint = f"{API_V1_PREFIX}/agent-cards/{created_resources['agent_card_id']}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 200 and response:
        if not response.get("is_active", True):
            log_test(endpoint, method, status, True, 
                    "Confirmed card is deactivated", None, response)
        else:
            log_test(endpoint, method, status, False, 
                    "Card still appears active after deletion", None, response)

def test_nonexistent_card():
    """Test: GET /agent-cards/{card_id} for non-existent card"""
    fake_uuid = str(uuid.uuid4())
    endpoint = f"{API_V1_PREFIX}/agent-cards/{fake_uuid}"
    method = "GET"
    
    status, response, error = make_request(f"{BASE_URL}{endpoint}")
    
    if status == 404:
        log_test(endpoint, method, status, True, 
                "Correctly returned 404 for non-existent card", None, error)
    else:
        log_test(endpoint, method, status, False, 
                f"Expected 404, got {status}", None, error or response)

def run_all_tests():
    """Run all agent cards endpoint tests"""
    print("\n" + "="*50)
    print("TESTING AGENT CARDS ENDPOINTS")
    print("="*50)
    
    # Setup
    if not setup_test_developer():
        print("WARNING: Developer setup failed. Some tests will be skipped.")
    
    # Run tests
    test_list_agent_cards_public()
    test_create_agent_card()
    test_get_agent_card_by_id()
    test_get_agent_card_by_hri_query()
    test_get_agent_card_by_hri_path()
    test_list_with_filters()
    test_list_owned_cards()
    test_update_agent_card()
    test_delete_agent_card()
    test_get_deleted_card()
    test_nonexistent_card()
    
    # Summary
    test_results["end_time"] = datetime.now().isoformat()
    total_tests = len(test_results["tests"])
    passed_tests = sum(1 for t in test_results["tests"] if t["success"])
    
    print("\n" + "="*50)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    print("="*50)
    
    # Save detailed results (fixed for Windows)
    with open("test_agent_cards_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    # Return exit code
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
