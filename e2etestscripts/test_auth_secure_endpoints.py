"""
Test script for Enhanced Authentication endpoints (auth_secure router).
Tests the Beta Strike enhanced authentication features.
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Registry A
API_PREFIX = "/api/v1"

# Test data
TEST_DEVELOPER = {
    "email": f"test_secure_{datetime.now().timestamp()}@example.com",
    "password": "SuperSecure123!@#",
    "username": f"test_secure_user_{int(datetime.now().timestamp())}"
}


class Colors:
    """ANSI color codes for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


async def test_auth_secure_endpoints():
    """Test all enhanced authentication endpoints"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}")
    print(f"OPERATION CERBERUS - AUTH SECURE TESTING")
    print(f"Testing Enhanced Authentication Endpoints")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Track results for saving
    test_results = []
    
    async with aiohttp.ClientSession() as session:
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "endpoints": {}
        }
        
        # Store tokens for later tests
        tokens = {}
        
        # Test 1: Register new developer
        print(f"{Colors.CYAN}Testing POST /auth/register (Enhanced)...{Colors.RESET}")
        try:
            async with session.post(
                f"{BASE_URL}{API_PREFIX}/auth/register",
                json=TEST_DEVELOPER
            ) as response:
                data = await response.json()
                results["total"] += 1
                
                if response.status == 201:
                    results["passed"] += 1
                    print(f"{Colors.GREEN}[OK] Registration successful{Colors.RESET}")
                    print(f"  - Message: {data.get('message', 'N/A')}")
                    print(f"  - Recovery keys: {len(data.get('recovery_keys', []))}")
                    tokens['recovery_key'] = data.get('recovery_keys', [])[0] if data.get('recovery_keys') else None
                    test_results.append({
                        "endpoint": "POST /auth/register",
                        "passed": True,
                        "message": ""
                    })
                else:
                    results["failed"] += 1
                    print(f"{Colors.RED}[X] Registration failed: {response.status}{Colors.RESET}")
                    print(f"  - Error: {data}")
                    test_results.append({
                        "endpoint": "POST /auth/register",
                        "passed": False,
                        "message": f"Status code: {response.status}"
                    })
                    
                results["endpoints"]["POST /auth/register"] = response.status
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            print(f"{Colors.RED}[X] Registration error: {str(e)}{Colors.RESET}")
            results["endpoints"]["POST /auth/register"] = "ERROR"
            test_results.append({
                "endpoint": "POST /auth/register",
                "passed": False,
                "message": str(e)
            })
        
        # Test 2: Login
        print(f"\n{Colors.CYAN}Testing POST /auth/login (Enhanced)...{Colors.RESET}")
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('username', TEST_DEVELOPER['email'])
            form_data.add_field('password', TEST_DEVELOPER['password'])
            
            async with session.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                data=form_data
            ) as response:
                data = await response.json()
                results["total"] += 1
                
                if response.status == 200:
                    results["passed"] += 1
                    print(f"{Colors.GREEN}[OK] Login successful{Colors.RESET}")
                    print(f"  - Token type: {data.get('token_type', 'N/A')}")
                    print(f"  - Has access token: {'access_token' in data}")
                    tokens['access_token'] = data.get('access_token')
                    test_results.append({
                        "endpoint": "POST /auth/login",
                        "passed": True,
                        "message": ""
                    })
                else:
                    results["failed"] += 1
                    print(f"{Colors.RED}[X] Login failed: {response.status}{Colors.RESET}")
                    print(f"  - Error: {data}")
                    test_results.append({
                        "endpoint": "POST /auth/login",
                        "passed": False,
                        "message": f"Status code: {response.status}"
                    })
                    
                results["endpoints"]["POST /auth/login"] = response.status
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            print(f"{Colors.RED}[X] Login error: {str(e)}{Colors.RESET}")
            results["endpoints"]["POST /auth/login"] = "ERROR"
            test_results.append({
                "endpoint": "POST /auth/login",
                "passed": False,
                "message": str(e)
            })
        
        # Test 3: Refresh token
        if tokens.get('access_token'):
            print(f"\n{Colors.CYAN}Testing POST /auth/refresh...{Colors.RESET}")
            try:
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                async with session.post(
                    f"{BASE_URL}{API_PREFIX}/auth/refresh",
                    headers=headers
                ) as response:
                    data = await response.json()
                    results["total"] += 1
                    
                    if response.status == 200:
                        results["passed"] += 1
                        print(f"{Colors.GREEN}[OK] Token refresh successful{Colors.RESET}")
                        print(f"  - New token received: {'access_token' in data}")
                        test_results.append({
                            "endpoint": "POST /auth/refresh",
                            "passed": True,
                            "message": ""
                        })
                    else:
                        results["failed"] += 1
                        print(f"{Colors.RED}[X] Token refresh failed: {response.status}{Colors.RESET}")
                        test_results.append({
                            "endpoint": "POST /auth/refresh",
                            "passed": False,
                            "message": f"Status code: {response.status}"
                        })
                        
                    results["endpoints"]["POST /auth/refresh"] = response.status
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                print(f"{Colors.RED}[X] Token refresh error: {str(e)}{Colors.RESET}")
                results["endpoints"]["POST /auth/refresh"] = "ERROR"
                test_results.append({
                    "endpoint": "POST /auth/refresh",
                    "passed": False,
                    "message": str(e)
                })
        
        # Test 4: API Key Management
        if tokens.get('access_token'):
            print(f"\n{Colors.CYAN}Testing POST /auth/api-keys...{Colors.RESET}")
            try:
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                async with session.post(
                    f"{BASE_URL}{API_PREFIX}/auth/api-keys",
                    headers=headers,
                    json={"key_name": "Test API Key"}
                ) as response:
                    data = await response.json()
                    results["total"] += 1
                    
                    if response.status == 200:
                        results["passed"] += 1
                        print(f"{Colors.GREEN}[OK] API key created{Colors.RESET}")
                        print(f"  - Key prefix: {data.get('api_key_info', {}).get('key_prefix', 'N/A')}")
                        api_key_id = data.get('api_key_info', {}).get('id')
                        test_results.append({
                            "endpoint": "POST /auth/api-keys",
                            "passed": True,
                            "message": ""
                        })
                    else:
                        results["failed"] += 1
                        print(f"{Colors.RED}[X] API key creation failed: {response.status}{Colors.RESET}")
                        test_results.append({
                            "endpoint": "POST /auth/api-keys",
                            "passed": False,
                            "message": f"Status code: {response.status}"
                        })
                        
                    results["endpoints"]["POST /auth/api-keys"] = response.status
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                print(f"{Colors.RED}[X] API key creation error: {str(e)}{Colors.RESET}")
                results["endpoints"]["POST /auth/api-keys"] = "ERROR"
                test_results.append({
                    "endpoint": "POST /auth/api-keys",
                    "passed": False,
                    "message": str(e)
                })
            
            # Test 5: List API keys
            print(f"\n{Colors.CYAN}Testing GET /auth/api-keys...{Colors.RESET}")
            try:
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                async with session.get(
                    f"{BASE_URL}{API_PREFIX}/auth/api-keys",
                    headers=headers
                ) as response:
                    data = await response.json()
                    results["total"] += 1
                    
                    if response.status == 200:
                        results["passed"] += 1
                        print(f"{Colors.GREEN}[OK] API keys listed{Colors.RESET}")
                        print(f"  - Number of keys: {len(data)}")
                        test_results.append({
                            "endpoint": "GET /auth/api-keys",
                            "passed": True,
                            "message": ""
                        })
                    else:
                        results["failed"] += 1
                        print(f"{Colors.RED}[X] API key listing failed: {response.status}{Colors.RESET}")
                        test_results.append({
                            "endpoint": "GET /auth/api-keys",
                            "passed": False,
                            "message": f"Status code: {response.status}"
                        })
                        
                    results["endpoints"]["GET /auth/api-keys"] = response.status
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                print(f"{Colors.RED}[X] API key listing error: {str(e)}{Colors.RESET}")
                results["endpoints"]["GET /auth/api-keys"] = "ERROR"
                test_results.append({
                    "endpoint": "GET /auth/api-keys",
                    "passed": False,
                    "message": str(e)
                })
        
        # Test 6: Account recovery
        if tokens.get('recovery_key'):
            print(f"\n{Colors.CYAN}Testing POST /auth/recover-account...{Colors.RESET}")
            try:
                async with session.post(
                    f"{BASE_URL}{API_PREFIX}/auth/recover-account",
                    json={
                        "email": TEST_DEVELOPER['email'],
                        "recovery_key": tokens['recovery_key']
                    }
                ) as response:
                    data = await response.json()
                    results["total"] += 1
                    
                    if response.status == 200:
                        results["passed"] += 1
                        print(f"{Colors.GREEN}[OK] Account recovery initiated{Colors.RESET}")
                        print(f"  - Temp token received: {'access_token' in data}")
                        test_results.append({
                            "endpoint": "POST /auth/recover-account",
                            "passed": True,
                            "message": ""
                        })
                    else:
                        results["failed"] += 1
                        print(f"{Colors.RED}[X] Account recovery failed: {response.status}{Colors.RESET}")
                        test_results.append({
                            "endpoint": "POST /auth/recover-account",
                            "passed": False,
                            "message": f"Status code: {response.status}"
                        })
                        
                    results["endpoints"]["POST /auth/recover-account"] = response.status
            except Exception as e:
                results["total"] += 1
                results["failed"] += 1
                print(f"{Colors.RED}[X] Account recovery error: {str(e)}{Colors.RESET}")
                results["endpoints"]["POST /auth/recover-account"] = "ERROR"
                test_results.append({
                    "endpoint": "POST /auth/recover-account",
                    "passed": False,
                    "message": str(e)
                })
        
        # Test 7: Logout
        print(f"\n{Colors.CYAN}Testing POST /auth/logout...{Colors.RESET}")
        try:
            async with session.post(f"{BASE_URL}{API_PREFIX}/auth/logout") as response:
                data = await response.json()
                results["total"] += 1
                
                if response.status == 200:
                    results["passed"] += 1
                    print(f"{Colors.GREEN}[OK] Logout successful{Colors.RESET}")
                    print(f"  - Message: {data.get('message', 'N/A')}")
                    test_results.append({
                        "endpoint": "POST /auth/logout",
                        "passed": True,
                        "message": ""
                    })
                else:
                    results["failed"] += 1
                    print(f"{Colors.RED}[X] Logout failed: {response.status}{Colors.RESET}")
                    test_results.append({
                        "endpoint": "POST /auth/logout",
                        "passed": False,
                        "message": f"Status code: {response.status}"
                    })
                    
                results["endpoints"]["POST /auth/logout"] = response.status
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            print(f"{Colors.RED}[X] Logout error: {str(e)}{Colors.RESET}")
            results["endpoints"]["POST /auth/logout"] = "ERROR"
            test_results.append({
                "endpoint": "POST /auth/logout",
                "passed": False,
                "message": str(e)
            })
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}")
        print(f"AUTH SECURE TEST SUMMARY")
        print(f"{'='*60}{Colors.RESET}")
        print(f"Total Tests: {results['total']}")
        print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {results['failed']}{Colors.RESET}")
        print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
        
        print(f"\n{Colors.YELLOW}Endpoint Results:{Colors.RESET}")
        for endpoint, status in results['endpoints'].items():
            color = Colors.GREEN if status == 200 or status == 201 else Colors.RED
            print(f"  {endpoint}: {color}{status}{Colors.RESET}")
        
        # Save results to JSON file
        results_file = "cerberus_auth_secure_test_results.json"
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "router": "auth_secure.py",
                "total_tests": results["total"],
                "passed": results["passed"],
                "failed": results["failed"],
                "results": test_results
            }, f, indent=2)
        
        print(f"\nResults saved to {results_file}")
        
        return results


if __name__ == "__main__":
    asyncio.run(test_auth_secure_endpoints())
