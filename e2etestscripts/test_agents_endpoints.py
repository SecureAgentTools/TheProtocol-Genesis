#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for agents.py endpoints
========================================================
This script tests all endpoints in the agents router.
All endpoints require agent authentication.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
ADMIN_API_KEY = "avreg_COs8OL3A7ENKZflsNyBvAsRv3v2jD4BUfrwE4uPmbeQ"
ADMIN_EMAIL = "commander@agentvault.com"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: agents.py Endpoint Tests")
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

def load_agent_credentials() -> Optional[Dict]:
    """Load existing agent credentials or create new ones"""
    # Try to load existing credentials
    creds_files = [
        "first_citizen_credentials.json",
        "attestation_test_agent.json"
    ]
    
    for creds_file in creds_files:
        if os.path.exists(creds_file):
            print(f"[INFO] Loading credentials from {creds_file}")
            with open(creds_file, "r") as f:
                return json.load(f)
    
    print("[INFO] No existing credentials found, creating test agent...")
    return create_test_agent()

def create_test_agent() -> Optional[Dict]:
    """Create a new test agent for testing"""
    # Get bootstrap token
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
            headers={
                "X-Api-Key": ADMIN_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "agent_type_hint": "test-agent",
                "requested_by": ADMIN_EMAIL,
                "description": "Cerberus test agent for agents.py endpoints"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to get bootstrap token: {response.status_code}")
            return None
            
        bootstrap_token = response.json()["bootstrap_token"]
        print("[INFO] Bootstrap token acquired")
        
    except Exception as e:
        print(f"[ERROR] Failed to get bootstrap token: {str(e)}")
        return None
    
    # Create agent
    agent_card = {
        "schemaVersion": "1.0",
        "humanReadableId": "cerberus-agents-test",
        "agentVersion": "1.0.0",
        "name": "Cerberus Agents Test Agent",
        "description": "Test agent for agents.py endpoint verification",
        "url": f"http://localhost:8000/agents/cerberus-agents-test",
        "provider": {
            "name": "Operation Cerberus",
            "url": "https://www.theprotocol.cloud",
            "support_contact": "cerberus@agentvault.com"
        },
        "capabilities": {
            "a2aVersion": "1.0",
            "supportedMessageParts": ["text", "data"],
            "supportsPushNotifications": True,
            "teeDetails": None,
            "mcpVersion": None
        },
        "authSchemes": [
            {
                "scheme": "apiKey",
                "description": "API Key authentication for programmatic access."
            }
        ],
        "tags": ["test", "cerberus", "automated"],
        "skills": [],
        "iconUrl": None,
        "privacyPolicyUrl": None,
        "termsOfServiceUrl": None,
        "lastUpdated": None
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/create_agent",
            headers={
                "Bootstrap-Token": bootstrap_token,
                "Content-Type": "application/json"
            },
            json={
                "agent_did_method": "cos",
                "public_key_jwk": None,
                "proof_of_work_solution": None,
                "agent_card": agent_card
            },
            timeout=30
        )
        
        if response.status_code != 201:
            print(f"[ERROR] Failed to create agent: {response.status_code}")
            return None
        
        data = response.json()
        print(f"[INFO] Test agent created: {data['agent_did']}")
        
        # Prepare credentials
        credentials = {
            "agent_did": data["agent_did"],
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "agent_card_id": data["agent_card_id"],
            "api_key": data.get("api_key", ""),
            "registry_url": REGISTRY_A_URL,
            "created_at": datetime.now().isoformat()
        }
        
        # Save credentials
        with open("cerberus_agents_test.json", "w") as f:
            json.dump(credentials, f, indent=2)
        
        return credentials
        
    except Exception as e:
        print(f"[ERROR] Failed to create agent: {str(e)}")
        return None

def authenticate_agent(credentials: Dict) -> Optional[str]:
    """Authenticate and get JWT token"""
    # Use OAuth2PasswordRequestForm format for agent auth
    # The agent/token endpoint expects username/password fields
    auth_data = {
        "grant_type": "password",
        "username": credentials["client_id"],  # client_id goes in username field
        "password": credentials["client_secret"]  # client_secret goes in password field
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/agent/token",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"[INFO] Authentication successful")
            return token_data.get("access_token")
        else:
            print(f"[ERROR] Authentication failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
        return None

def test_get_agent_me(token: str, agent_did: str):
    """Test GET /api/v1/agents/me endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/agents/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if (data.get("did") == agent_did and 
                "client_id" in data and 
                "status" in data):
                log_result(True, "GET", "/api/v1/agents/me")
            else:
                log_result(False, "GET", "/api/v1/agents/me", "Invalid response structure")
        else:
            log_result(False, "GET", "/api/v1/agents/me", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/agents/me", str(e))

def test_get_agent_health(token: str):
    """Test GET /api/v1/agents/health endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/agents/health",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if (data.get("status") == "healthy" and 
                "did" in data and 
                data.get("message") == "Agent authentication successful"):
                log_result(True, "GET", "/api/v1/agents/health")
            else:
                log_result(False, "GET", "/api/v1/agents/health", "Invalid response structure")
        else:
            log_result(False, "GET", "/api/v1/agents/health", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/agents/health", str(e))

def test_post_agent_heartbeat(token: str, agent_did: str):
    """Test POST /api/v1/agents/heartbeat endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/agents/heartbeat",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Verify response contains expected fields
            if (data.get("status") == "acknowledged" and 
                data.get("did") == agent_did and 
                data.get("message") == "Heartbeat received"):
                log_result(True, "POST", "/api/v1/agents/heartbeat")
            else:
                log_result(False, "POST", "/api/v1/agents/heartbeat", "Invalid response structure")
        else:
            log_result(False, "POST", "/api/v1/agents/heartbeat", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/agents/heartbeat", str(e))

def main():
    """Run all tests for agents.py endpoints"""
    print_test_header()
    
    # Load or create agent credentials
    credentials = load_agent_credentials()
    if not credentials:
        print("\n[FATAL] Failed to obtain agent credentials")
        sys.exit(1)
    
    agent_did = credentials["agent_did"]
    
    # Authenticate agent
    token = authenticate_agent(credentials)
    if not token:
        print("\n[FATAL] Failed to authenticate agent")
        sys.exit(1)
    
    print(f"\n[INFO] Testing as agent: {agent_did}\n")
    
    # Run all endpoint tests
    test_get_agent_me(token, agent_did)
    test_get_agent_health(token)
    test_post_agent_heartbeat(token, agent_did)
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All agents.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_agents_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "agents.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
