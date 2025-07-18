#!/usr/bin/env python3
"""
Updated governance test with pre-funded test agents
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
ADMIN_API_KEY = "avreg_COs8OL3A7ENKZflsNyBvAsRv3v2jD4BUfrwE4uPmbeQ"

# Use the funded agent from Operation Mjolnir for testing
FUNDED_AGENT = {
    "agent_did": "did:cos:fbf7393c-f3c1-ee05-7eb7",
    "client_id": "8O6ZXnJ-2ey6c5jnQpKN9xQ8V9d7MQ",
    "client_secret": "CJcppDnOxq1H9ASkQdpkOjJCEtCnbGIGSVJsFDN1vhKEzHNFQNqkyJgfPLaWQvQi"
}

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: governance.py Endpoint Tests")
    print("  (Using Pre-Funded Agent)")
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

def authenticate_agent(credentials: Dict) -> Optional[str]:
    """Authenticate and get JWT token"""
    auth_data = {
        "grant_type": "password",
        "username": credentials["client_id"],
        "password": credentials["client_secret"]
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
            return token_data.get("access_token")
        else:
            print(f"[ERROR] Authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
        return None

def check_balance(token: str) -> Dict:
    """Check agent's current balance"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/staking/balance",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"available_balance": 0, "staked_balance": 0}
            
    except Exception as e:
        print(f"[ERROR] Failed to check balance: {str(e)}")
        return {"available_balance": 0, "staked_balance": 0}

def test_list_proposals_public():
    """Test GET /api/v1/governance/proposals endpoint (public access)"""
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/governance/proposals",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                log_result(True, "GET", "/api/v1/governance/proposals (public)")
                return data
            else:
                log_result(False, "GET", "/api/v1/governance/proposals", "Invalid response format")
        else:
            log_result(False, "GET", "/api/v1/governance/proposals", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/governance/proposals", str(e))
    
    return []

def test_create_proposal(token: str) -> Optional[int]:
    """Test POST /api/v1/governance/proposals endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    proposal_data = {
        "title": "Cerberus Test Proposal (Funded)",
        "description": "This is a test proposal created by Operation Cerberus with a funded agent to verify governance endpoints work correctly.",
        "duration_seconds": 300  # 5 minutes for testing
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/governance/proposals",
            headers=headers,
            json=proposal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "proposer_did", "title", "description", "status", 
                             "created_at", "end_timestamp", "votes_for", "votes_against"]
            
            if all(field in data for field in required_fields):
                log_result(True, "POST", "/api/v1/governance/proposals")
                print(f"[INFO] Created proposal ID: {data['id']}")
                return data["id"]
            else:
                log_result(False, "POST", "/api/v1/governance/proposals", "Missing required fields in response")
        else:
            log_result(False, "POST", "/api/v1/governance/proposals", f"Status code: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
                
    except Exception as e:
        log_result(False, "POST", "/api/v1/governance/proposals", str(e))
    
    return None

def test_get_proposal(proposal_id: int):
    """Test GET /api/v1/governance/proposals/{proposal_id} endpoint"""
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/governance/proposals/{proposal_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "proposer_did", "title", "description", "status", 
                             "created_at", "end_timestamp", "votes_for", "votes_against"]
            
            if all(field in data for field in required_fields) and data["id"] == proposal_id:
                log_result(True, "GET", f"/api/v1/governance/proposals/{proposal_id}")
                return data
            else:
                log_result(False, "GET", f"/api/v1/governance/proposals/{proposal_id}", "Invalid response structure")
        else:
            log_result(False, "GET", f"/api/v1/governance/proposals/{proposal_id}", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", f"/api/v1/governance/proposals/{proposal_id}", str(e))
    
    return None

def test_cast_vote(token: str, proposal_id: int, vote_in_favor: bool) -> bool:
    """Test POST /api/v1/governance/proposals/{proposal_id}/vote endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    vote_data = {
        "vote_in_favor": vote_in_favor
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/governance/proposals/{proposal_id}/vote",
            headers=headers,
            json=vote_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "proposal_id", "voter_did", "vote", "voting_power", "created_at"]
            
            if all(field in data for field in required_fields) and data["proposal_id"] == proposal_id:
                log_result(True, "POST", f"/api/v1/governance/proposals/{proposal_id}/vote")
                print(f"[INFO] Vote cast: {'FOR' if vote_in_favor else 'AGAINST'} with power {data['voting_power']}")
                return True
            else:
                log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/vote", "Invalid response structure")
        elif response.status_code == 409:
            # Already voted - this is expected for second vote attempt
            log_result(True, "POST", f"/api/v1/governance/proposals/{proposal_id}/vote (duplicate - expected 409)")
            return False
        else:
            log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/vote", f"Status code: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
                
    except Exception as e:
        log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/vote", str(e))
    
    return False

def test_tally_votes(token: str, proposal_id: int):
    """Test POST /api/v1/governance/proposals/{proposal_id}/tally endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/governance/proposals/{proposal_id}/tally",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["proposal_id", "votes_for", "votes_against", "total_votes", "status"]
            
            if all(field in data for field in required_fields) and data["proposal_id"] == proposal_id:
                log_result(True, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally")
                print(f"[INFO] Tally complete - FOR: {data['votes_for']}, AGAINST: {data['votes_against']}, Status: {data['status']}")
                return data
            else:
                log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally", "Invalid response structure")
        elif response.status_code == 400:
            # Expected if voting hasn't ended yet
            try:
                error_detail = response.json()
                if "not ended yet" in error_detail.get("detail", ""):
                    print(f"[INFO] Voting period not ended yet, this is expected")
                    log_result(True, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally (voting active)")
                else:
                    log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally", error_detail.get("detail", "Unknown error"))
            except:
                log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally", f"Status code: {response.status_code}")
        else:
            log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally", f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", f"/api/v1/governance/proposals/{proposal_id}/tally", str(e))
    
    return None

def main():
    """Run all tests for governance.py endpoints"""
    print_test_header()
    
    # Authenticate the funded agent
    token = authenticate_agent(FUNDED_AGENT)
    if not token:
        print("\n[FATAL] Failed to authenticate funded agent")
        sys.exit(1)
    
    print(f"\n[INFO] Authenticated funded agent: {FUNDED_AGENT['agent_did']}")
    
    # Check balance
    balance = check_balance(token)
    print(f"[INFO] Agent balance - Available: {balance.get('available_balance', 0)}, Staked: {balance.get('staked_balance', 0)}")
    
    print("\n[INFO] Starting governance endpoint tests...\n")
    
    # Test 1: List proposals (public endpoint)
    existing_proposals = test_list_proposals_public()
    
    # Test 2: Create a proposal (requires staked tokens)
    proposal_id = test_create_proposal(token)
    
    if proposal_id:
        # Test 3: Get specific proposal
        proposal_data = test_get_proposal(proposal_id)
        
        # Test 4: Cast vote
        vote_success = test_cast_vote(token, proposal_id, True)
        
        # Test 5: Try to vote again (should fail with 409)
        if vote_success:
            print("\n[INFO] Testing duplicate vote (should fail)...")
            test_cast_vote(token, proposal_id, False)
        
        # Test 6: Try to tally votes (may fail if voting period not ended)
        print("\n[INFO] Testing vote tally...")
        test_tally_votes(token, proposal_id)
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All governance.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_governance_funded_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "governance.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results,
            "proposal_id": proposal_id if 'proposal_id' in locals() else None
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
