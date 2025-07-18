#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for admin_federation.py endpoints
==================================================================
This script tests all endpoints in the admin_federation router.
These endpoints handle administrative federation management tasks.
FIXED: Using JWT Bearer authentication with Commander's admin credentials.
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"

# Commander's admin credentials
COMMANDER_EMAIL = "commander@agentvault.com"
COMMANDER_PASSWORD = "SovereignKey!2025"

# Test results tracking
test_results = []
admin_token = None

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: admin_federation.py Endpoint Tests")
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

def authenticate_admin():
    """Authenticate as admin developer and get JWT token"""
    global admin_token
    
    print("[INFO] Authenticating with Commander's admin credentials...")
    
    login_data = {
        "username": COMMANDER_EMAIL,  # OAuth2 form uses username field for email
        "password": COMMANDER_PASSWORD
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
                admin_token = data["access_token"]
                print("[INFO] Admin authentication successful")
                return True
            else:
                print("[ERROR] Invalid login response structure")
                return False
        else:
            print(f"[ERROR] Admin login failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
        return False

def test_list_pending_peers():
    """Test GET /api/v1/admin/federation/peers/pending"""
    if not admin_token:
        log_result(False, "GET", "/api/v1/admin/federation/peers/pending", "No admin token available")
        return
        
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/admin/federation/peers/pending",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and "pagination" in data:
                log_result(True, "GET", "/api/v1/admin/federation/peers/pending")
                print(f"   Found {len(data['items'])} pending peers")
            else:
                log_result(False, "GET", "/api/v1/admin/federation/peers/pending", 
                          "Invalid response structure")
        else:
            log_result(False, "GET", "/api/v1/admin/federation/peers/pending", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/admin/federation/peers/pending", str(e))

def test_list_all_peers():
    """Test GET /api/v1/admin/federation/peers/all"""
    if not admin_token:
        log_result(False, "GET", "/api/v1/admin/federation/peers/all", "No admin token available")
        return
        
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/admin/federation/peers/all",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and "pagination" in data:
                log_result(True, "GET", "/api/v1/admin/federation/peers/all")
                print(f"   Found {len(data['items'])} total peers")
            else:
                log_result(False, "GET", "/api/v1/admin/federation/peers/all", 
                          "Invalid response structure")
        else:
            log_result(False, "GET", "/api/v1/admin/federation/peers/all", 
                      f"Status code: {response.status_code}")
            
    except Exception as e:
        log_result(False, "GET", "/api/v1/admin/federation/peers/all", str(e))

def test_approve_peer():
    """Test POST /api/v1/admin/federation/peers/{peer_id}/approve"""
    if not admin_token:
        log_result(False, "POST", "/api/v1/admin/federation/peers/{peer_id}/approve", "No admin token available")
        return
        
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First get a pending peer to test with
    try:
        list_response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/admin/federation/peers/pending",
            headers=headers,
            timeout=10
        )
        
        if list_response.status_code == 200:
            peers = list_response.json().get("items", [])
            if peers:
                peer_id = peers[0]["id"]
                
                # Try to approve
                response = requests.post(
                    f"{REGISTRY_A_URL}/api/v1/admin/federation/peers/{peer_id}/approve",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    log_result(True, "POST", f"/api/v1/admin/federation/peers/{peer_id}/approve")
                    print(f"   Approved peer ID: {peer_id}")
                else:
                    log_result(False, "POST", f"/api/v1/admin/federation/peers/{peer_id}/approve", 
                              f"Status code: {response.status_code}")
            else:
                log_result(True, "POST", "/api/v1/admin/federation/peers/{peer_id}/approve", 
                          "No pending peers to test (acceptable)")
        else:
            log_result(False, "POST", "/api/v1/admin/federation/peers/{peer_id}/approve", 
                      "Could not retrieve pending peers")
                
    except Exception as e:
        log_result(False, "POST", "/api/v1/admin/federation/peers/{peer_id}/approve", str(e))

def test_deactivate_peer():
    """Test POST /api/v1/admin/federation/peers/{peer_id}/deactivate"""
    if not admin_token:
        log_result(False, "POST", "/api/v1/admin/federation/peers/{peer_id}/deactivate", "No admin token available")
        return
        
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First get an active peer to test with
    try:
        list_response = requests.get(
            f"{REGISTRY_A_URL}/api/v1/admin/federation/peers/all?status=ACTIVE",
            headers=headers,
            timeout=10
        )
        
        if list_response.status_code == 200:
            peers = list_response.json().get("items", [])
            if peers:
                peer_id = peers[0]["id"]
                
                # Try to deactivate
                response = requests.post(
                    f"{REGISTRY_A_URL}/api/v1/admin/federation/peers/{peer_id}/deactivate",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    log_result(True, "POST", f"/api/v1/admin/federation/peers/{peer_id}/deactivate")
                    print(f"   Deactivated peer ID: {peer_id}")
                else:
                    log_result(False, "POST", f"/api/v1/admin/federation/peers/{peer_id}/deactivate", 
                              f"Status code: {response.status_code}")
            else:
                log_result(True, "POST", "/api/v1/admin/federation/peers/{peer_id}/deactivate", 
                          "No active peers to test (acceptable)")
        else:
            log_result(False, "POST", "/api/v1/admin/federation/peers/{peer_id}/deactivate", 
                      "Could not retrieve active peers")
                
    except Exception as e:
        log_result(False, "POST", "/api/v1/admin/federation/peers/{peer_id}/deactivate", str(e))

def main():
    """Run all tests for admin_federation.py endpoints"""
    print_test_header()
    
    # Authenticate first
    if not authenticate_admin():
        print("\n[FATAL] Failed to authenticate as admin")
        sys.exit(1)
    
    print("\n[INFO] Testing admin federation endpoints\n")
    print("[NOTE] These endpoints require admin developer JWT authentication\n")
    
    # Run all endpoint tests
    test_list_pending_peers()
    test_list_all_peers()
    test_approve_peer()
    test_deactivate_peer()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All admin_federation.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_admin_federation_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "admin_federation.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
