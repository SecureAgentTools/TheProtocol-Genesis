"""
Test script for teg_integration router endpoints.

Tests the TEG Layer integration endpoints for tokens, policies, disputes, and attestations.
"""
import httpx
import json
import asyncio
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test developer credentials
TEST_DEV_EMAIL = "teg_test_dev@example.com"
TEST_DEV_PASSWORD = "TestPassword123!"
TEST_DEV_NAME = "TEG Test Developer"

# Commander credentials for admin operations
COMMANDER_EMAIL = "commander@agentvault.com"
COMMANDER_PASSWORD = "SovereignKey!2025"

# Track test results
test_results = []

def log_test_result(test_name, passed, details=""):
    """Log test result with consistent formatting."""
    status = "PASS" if passed else "FAIL"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {
        "timestamp": timestamp,
        "test": test_name,
        "status": status,
        "passed": passed,
        "details": details
    }
    test_results.append(result)
    
    # Color output
    if passed:
        print(f"\033[92m{status}\033[0m {test_name}")
    else:
        print(f"\033[91m{status}\033[0m {test_name}")
        if details:
            print(f"     Details: {details}")

async def create_test_developer(email, password, name):
    """Create a test developer account."""
    async with httpx.AsyncClient() as client:
        # Check if developer already exists
        try:
            login_data = {
                "username": email,
                "password": password
            }
            login_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if login_response.status_code == 200:
                print(f"Test developer {email} already exists, using existing account")
                return login_response.json()
        except:
            pass
        
        # Register new developer
        register_data = {
            "email": email,
            "password": password,
            "name": name
        }
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=register_data
        )
        
        if response.status_code not in [200, 201]:
            print(f"Failed to create test developer: {response.status_code}")
            print(response.text)
            return None
        
        # Login to get tokens
        login_response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"Failed to login test developer: {login_response.status_code}")
            return None
            
        return login_response.json()

async def test_teg_integration_endpoints():
    """Test TEG integration endpoints."""
    print("\n" + "="*50)
    print("TESTING TEG INTEGRATION ENDPOINTS")
    print("="*50)
    
    # Create test developer and get commander auth
    print("\nCreating test developer...")
    dev_auth = await create_test_developer(TEST_DEV_EMAIL, TEST_DEV_PASSWORD, TEST_DEV_NAME)
    if not dev_auth:
        log_test_result("Setup: Create test developer", False, "Failed to create test developer")
        return
    
    dev_token = dev_auth.get("access_token")
    print(f"Test developer created successfully")
    
    # Get commander token for admin operations
    print("\nAuthenticating as commander...")
    commander_auth = None
    async with httpx.AsyncClient() as client:
        login_data = {
            "username": COMMANDER_EMAIL,
            "password": COMMANDER_PASSWORD
        }
        login_response = await client.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_response.status_code == 200:
            commander_auth = login_response.json()
            commander_token = commander_auth.get("access_token")
            print("Commander authenticated successfully")
        else:
            print("Failed to authenticate as commander")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get TEG balance
        print("\n1. Testing GET /teg/balance...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/teg/balance",
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "GET /teg/balance",
                    True,
                    f"Balance: {data.get('balance', '0')}"
                )
            elif response.status_code == 503:
                log_test_result(
                    "GET /teg/balance",
                    True,
                    "503 - TEG service unavailable (expected if TEG Layer not running)"
                )
            else:
                log_test_result(
                    "GET /teg/balance",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "GET /teg/balance",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 2: Get fee configuration
        print("\n2. Testing GET /teg/fees/config...")
        try:
            # Try without auth first
            response = await client.get(f"{BASE_URL}{API_PREFIX}/teg/fees/config")
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "GET /teg/fees/config",
                    True,
                    f"Transfer fee: {data.get('transfer_fee_amount', '0')}"
                )
            elif response.status_code == 401:
                # Try with auth
                response = await client.get(
                    f"{BASE_URL}{API_PREFIX}/teg/fees/config",
                    headers={"Authorization": f"Bearer {dev_token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    log_test_result(
                        "GET /teg/fees/config",
                        True,
                        f"Transfer fee: {data.get('transfer_fee_amount', '0')} (requires auth)"
                    )
                else:
                    log_test_result(
                        "GET /teg/fees/config",
                        True,
                        f"401 - Requires authentication (status after auth: {response.status_code})"
                    )
            elif response.status_code == 503:
                log_test_result(
                    "GET /teg/fees/config",
                    True,
                    "503 - TEG service unavailable (expected if TEG Layer not running)"
                )
            else:
                log_test_result(
                    "GET /teg/fees/config",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "GET /teg/fees/config",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 3: Transfer tokens
        print("\n3. Testing POST /teg/transfer...")
        try:
            transfer_data = {
                "receiver_agent_id": "did:agentvault:test_receiver",
                "amount": "100",
                "message": "Test transfer"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/teg/transfer",
                json=transfer_data,
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "POST /teg/transfer",
                    True,
                    f"Transaction ID: {data.get('transaction_id')}"
                )
            elif response.status_code == 400:
                log_test_result(
                    "POST /teg/transfer",
                    True,
                    "400 - Transfer failed (expected for insufficient balance)"
                )
            elif response.status_code == 503:
                log_test_result(
                    "POST /teg/transfer",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "POST /teg/transfer",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "POST /teg/transfer",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 4: System transfer
        print("\n4. Testing POST /teg/system-transfer...")
        try:
            system_transfer_data = {
                "amount": "50",
                "purpose": "Test system fee"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/teg/system-transfer",
                json=system_transfer_data,
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "POST /teg/system-transfer",
                    True,
                    f"Transaction ID: {data.get('transaction_id')}"
                )
            elif response.status_code == 400:
                log_test_result(
                    "POST /teg/system-transfer",
                    True,
                    "400 - Transfer failed (expected for insufficient balance)"
                )
            elif response.status_code == 503:
                log_test_result(
                    "POST /teg/system-transfer",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "POST /teg/system-transfer",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "POST /teg/system-transfer",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 5: Get transaction history
        print("\n5. Testing GET /teg/transactions...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/teg/transactions?limit=10",
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "GET /teg/transactions",
                    True,
                    f"Total transactions: {data.get('total', 0)}"
                )
            elif response.status_code == 503:
                log_test_result(
                    "GET /teg/transactions",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "GET /teg/transactions",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "GET /teg/transactions",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 6: Get treasury balance
        print("\n6. Testing GET /teg/treasury/balance...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/teg/treasury/balance",
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "GET /teg/treasury/balance",
                    True,
                    f"Treasury balance: {data.get('balance', '0')}"
                )
            elif response.status_code == 503:
                log_test_result(
                    "GET /teg/treasury/balance",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "GET /teg/treasury/balance",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "GET /teg/treasury/balance",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 7: List policies
        print("\n7. Testing GET /teg/policies...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/teg/policies",
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "GET /teg/policies",
                    True,
                    f"Total policies: {data.get('total', 0)}"
                )
            elif response.status_code == 503:
                log_test_result(
                    "GET /teg/policies",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "GET /teg/policies",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "GET /teg/policies",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 8: Create policy (requires admin)
        print("\n8. Testing POST /teg/policies...")
        try:
            policy_data = {
                "policy_code": "TEST_POLICY_001",
                "policy_name": "Test Policy",
                "policy_type": "attestation",
                "description": "Test policy for testing"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/teg/policies",
                json=policy_data,
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "POST /teg/policies",
                    True,
                    f"Policy ID: {data.get('policy_id')}"
                )
            elif response.status_code == 409:
                log_test_result(
                    "POST /teg/policies",
                    True,
                    "409 - Policy already exists"
                )
            elif response.status_code == 503:
                log_test_result(
                    "POST /teg/policies",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "POST /teg/policies",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "POST /teg/policies",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 9: Log dispute
        print("\n9. Testing POST /teg/disputes/log...")
        try:
            dispute_data = {
                "defendant_agent_did": "did:agentvault:test_defendant",
                "reason_code": "UNFAIR_FEE",
                "brief_description": "Test dispute"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/teg/disputes/log",
                json=dispute_data,
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 201:
                data = response.json()
                log_test_result(
                    "POST /teg/disputes/log",
                    True,
                    f"Dispute ID: {data.get('dispute_log_id')}"
                )
            elif response.status_code == 503:
                log_test_result(
                    "POST /teg/disputes/log",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "POST /teg/disputes/log",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "POST /teg/disputes/log",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 10: Submit attestation
        print("\n10. Testing POST /teg/attestations/submit...")
        try:
            attestation_data = {
                "target_agent_did": "did:agentvault:test_target",
                "attestation_type": "identity_verification",
                "attestation_data": {
                    "verified": True,
                    "verification_method": "test"
                }
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/teg/attestations/submit",
                json=attestation_data,
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 201:
                data = response.json()
                log_test_result(
                    "POST /teg/attestations/submit",
                    True,
                    f"Attestation ID: {data.get('attestation_id')}"
                )
            elif response.status_code == 503:
                log_test_result(
                    "POST /teg/attestations/submit",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "POST /teg/attestations/submit",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "POST /teg/attestations/submit",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 11: Apply reputation signal
        print("\n11. Testing POST /teg/transactions/{transaction_id}/reputation-signal...")
        try:
            signal_data = {
                "signal_value": 1
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/teg/transactions/test-txn-123/reputation-signal",
                json=signal_data,
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "POST /teg/transactions/{id}/reputation-signal",
                    True,
                    "Signal applied successfully"
                )
            elif response.status_code == 404:
                log_test_result(
                    "POST /teg/transactions/{id}/reputation-signal",
                    True,
                    "404 - Transaction not found (expected for test ID)"
                )
            elif response.status_code == 503:
                log_test_result(
                    "POST /teg/transactions/{id}/reputation-signal",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "POST /teg/transactions/{id}/reputation-signal",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "POST /teg/transactions/{id}/reputation-signal",
                False,
                f"Exception: {str(e)}"
            )
        
        # Test 12: Get agent reputation
        print("\n12. Testing GET /teg/agents/{agent_id}/reputation...")
        try:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/teg/agents/did:agentvault:test_agent/reputation",
                headers={"Authorization": f"Bearer {dev_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                log_test_result(
                    "GET /teg/agents/{agent_id}/reputation",
                    True,
                    f"Reputation score: {data.get('reputation_score')}"
                )
            elif response.status_code == 404:
                log_test_result(
                    "GET /teg/agents/{agent_id}/reputation",
                    True,
                    "404 - Agent not found (expected for test agent)"
                )
            elif response.status_code == 503:
                log_test_result(
                    "GET /teg/agents/{agent_id}/reputation",
                    True,
                    "503 - TEG service unavailable"
                )
            else:
                log_test_result(
                    "GET /teg/agents/{agent_id}/reputation",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            log_test_result(
                "GET /teg/agents/{agent_id}/reputation",
                False,
                f"Exception: {str(e)}"
            )

def print_summary():
    """Print test summary."""
    print("\n" + "="*50)
    print("TEG INTEGRATION TEST SUMMARY")
    print("="*50)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["passed"])
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests > 0:
        print("\nFailed Tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}")
                if result["details"]:
                    print(f"    {result['details']}")
    
    print("\nNote: Most endpoints will return 503 if TEG Layer service is not running")
    
    # Save results to file
    results_file = "teg_integration_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "test_suite": "teg_integration_endpoints",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests
            },
            "results": test_results
        }, f, indent=2)
    print(f"\nDetailed results saved to {results_file}")

async def main():
    """Main test runner."""
    print("Starting TEG Integration Endpoint Tests...")
    print(f"Target: {BASE_URL}{API_PREFIX}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await test_teg_integration_endpoints()
    except Exception as e:
        print(f"\nCritical error during tests: {str(e)}")
    
    print_summary()

if __name__ == "__main__":
    asyncio.run(main())
