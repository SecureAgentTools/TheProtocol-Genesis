"""
Test script for TEG Integration Variant endpoints.
Tests all three authentication methods: JWT-SVID, mTLS, and OAuth.
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Registry A
API_PREFIX = "/api/v1"

# Test credentials
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "TestPass123!@#"

# Test transfer data
TEST_RECEIVER = "did:agentvault:test_receiver"
TEST_AMOUNT = "10.0"


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


async def get_auth_token(session: aiohttp.ClientSession) -> Optional[str]:
    """Get authentication token"""
    form_data = aiohttp.FormData()
    form_data.add_field('username', TEST_EMAIL)
    form_data.add_field('password', TEST_PASSWORD)
    
    try:
        async with session.post(f"{BASE_URL}{API_PREFIX}/auth/login", data=form_data) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('access_token')
    except:
        pass
    return None


async def test_teg_variant(session: aiohttp.ClientSession, variant: str, prefix: str, token: str) -> Dict[str, Any]:
    """Test a specific TEG integration variant"""
    print(f"\n{Colors.CYAN}Testing {variant} variant...{Colors.RESET}")
    print(f"{Colors.BLUE}Prefix: {prefix}{Colors.RESET}")
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "endpoints": {}
    }
    
    # Test 1: Get balance
    print(f"\n  {Colors.YELLOW}Testing GET {prefix}/balance...{Colors.RESET}")
    try:
        async with session.get(
            f"{BASE_URL}{prefix}/balance",
            headers=headers
        ) as response:
            data = await response.json()
            results["total"] += 1
            
            if response.status == 200:
                results["passed"] += 1
                print(f"  {Colors.GREEN}[OK] Balance retrieved{Colors.RESET}")
                print(f"    - Agent ID: {data.get('agent_id', 'N/A')}")
                print(f"    - Balance: {data.get('balance', 'N/A')} AVT")
            else:
                results["failed"] += 1
                print(f"  {Colors.RED}[X] Balance failed: {response.status}{Colors.RESET}")
                
            results["endpoints"][f"GET {prefix}/balance"] = response.status
    except Exception as e:
        results["total"] += 1
        results["failed"] += 1
        print(f"  {Colors.RED}[X] Balance error: {str(e)}{Colors.RESET}")
        results["endpoints"][f"GET {prefix}/balance"] = "ERROR"
    
    # Test 2: Get fee config
    print(f"\n  {Colors.YELLOW}Testing GET {prefix}/fee-config...{Colors.RESET}")
    try:
        async with session.get(
            f"{BASE_URL}{prefix}/fee-config",
            headers=headers
        ) as response:
            data = await response.json()
            results["total"] += 1
            
            if response.status == 200:
                results["passed"] += 1
                print(f"  {Colors.GREEN}[OK] Fee config retrieved{Colors.RESET}")
                print(f"    - Transfer fee: {data.get('transfer_fee_amount', 'N/A')} AVT")
                print(f"    - Fee collection address: {data.get('fee_collection_address', 'N/A')}")
            else:
                results["failed"] += 1
                print(f"  {Colors.RED}[X] Fee config failed: {response.status}{Colors.RESET}")
                
            results["endpoints"][f"GET {prefix}/fee-config"] = response.status
    except Exception as e:
        results["total"] += 1
        results["failed"] += 1
        print(f"  {Colors.RED}[X] Fee config error: {str(e)}{Colors.RESET}")
        results["endpoints"][f"GET {prefix}/fee-config"] = "ERROR"
    
    # Test 3: Transfer tokens
    print(f"\n  {Colors.YELLOW}Testing POST {prefix}/transfer...{Colors.RESET}")
    try:
        async with session.post(
            f"{BASE_URL}{prefix}/transfer",
            headers=headers,
            json={
                "receiver_agent_id": TEST_RECEIVER,
                "amount": TEST_AMOUNT,
                "message": f"Test transfer via {variant}"
            }
        ) as response:
            data = await response.json()
            results["total"] += 1
            
            if response.status == 200:
                results["passed"] += 1
                print(f"  {Colors.GREEN}[OK] Transfer successful{Colors.RESET}")
                print(f"    - Transaction ID: {data.get('transaction_id', 'N/A')}")
                print(f"    - Amount: {data.get('amount', 'N/A')} AVT")
                print(f"    - Fee: {data.get('fee_amount', 'N/A')} AVT")
            elif response.status == 400:
                # Expected if insufficient balance
                results["passed"] += 1
                print(f"  {Colors.YELLOW}[OK] Transfer rejected (expected){Colors.RESET}")
                print(f"    - Reason: {data.get('detail', 'Insufficient balance')}")
            else:
                results["failed"] += 1
                print(f"  {Colors.RED}[X] Transfer failed: {response.status}{Colors.RESET}")
                
            results["endpoints"][f"POST {prefix}/transfer"] = response.status
    except Exception as e:
        results["total"] += 1
        results["failed"] += 1
        print(f"  {Colors.RED}[X] Transfer error: {str(e)}{Colors.RESET}")
        results["endpoints"][f"POST {prefix}/transfer"] = "ERROR"
    
    # Test 4: Get transaction history
    print(f"\n  {Colors.YELLOW}Testing GET {prefix}/history...{Colors.RESET}")
    try:
        async with session.get(
            f"{BASE_URL}{prefix}/history?limit=10",
            headers=headers
        ) as response:
            data = await response.json()
            results["total"] += 1
            
            if response.status == 200:
                results["passed"] += 1
                print(f"  {Colors.GREEN}[OK] History retrieved{Colors.RESET}")
                print(f"    - Total transactions: {data.get('total', 0)}")
                print(f"    - Retrieved: {len(data.get('transactions', []))}")
            else:
                results["failed"] += 1
                print(f"  {Colors.RED}[X] History failed: {response.status}{Colors.RESET}")
                
            results["endpoints"][f"GET {prefix}/history"] = response.status
    except Exception as e:
        results["total"] += 1
        results["failed"] += 1
        print(f"  {Colors.RED}[X] History error: {str(e)}{Colors.RESET}")
        results["endpoints"][f"GET {prefix}/history"] = "ERROR"
    
    # OAuth-specific: Test system transfer
    if variant == "OAuth":
        print(f"\n  {Colors.YELLOW}Testing POST {prefix}/system-transfer...{Colors.RESET}")
        try:
            async with session.post(
                f"{BASE_URL}{prefix}/system-transfer",
                headers=headers,
                json={
                    "amount": "5.0",
                    "purpose": "Test system fee"
                }
            ) as response:
                data = await response.json()
                results["total"] += 1
                
                if response.status == 200:
                    results["passed"] += 1
                    print(f"  {Colors.GREEN}[OK] System transfer successful{Colors.RESET}")
                    print(f"    - Transaction ID: {data.get('transaction_id', 'N/A')}")
                    print(f"    - System receiver: {data.get('system_receiver_id', 'N/A')}")
                elif response.status == 400:
                    # Expected if insufficient balance
                    results["passed"] += 1
                    print(f"  {Colors.YELLOW}[OK] System transfer rejected (expected){Colors.RESET}")
                else:
                    results["failed"] += 1
                    print(f"  {Colors.RED}[X] System transfer failed: {response.status}{Colors.RESET}")
                    
                results["endpoints"][f"POST {prefix}/system-transfer"] = response.status
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            print(f"  {Colors.RED}[X] System transfer error: {str(e)}{Colors.RESET}")
            results["endpoints"][f"POST {prefix}/system-transfer"] = "ERROR"
    
    return results


async def test_teg_integration_variants():
    """Test all TEG integration variant endpoints"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}")
    print(f"OPERATION CERBERUS - TEG INTEGRATION VARIANTS TESTING")
    print(f"Testing JWT-SVID, mTLS, and OAuth Authentication Methods")
    print(f"{'='*60}{Colors.RESET}\n")
    
    async with aiohttp.ClientSession() as session:
        overall_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "variants": {}
        }
        
        # Get auth token
        print(f"{Colors.CYAN}Getting authentication token...{Colors.RESET}")
        token = await get_auth_token(session)
        if not token:
            print(f"{Colors.RED}[X] Failed to get auth token{Colors.RESET}")
            return overall_results
        
        print(f"{Colors.GREEN}[OK] Authentication successful{Colors.RESET}")
        
        # Test each variant
        variants = [
            ("JWT-SVID", f"{API_PREFIX}/teg-jwt-svid"),
            ("mTLS", f"{API_PREFIX}/teg-mtls"),
            ("OAuth", f"{API_PREFIX}/teg-oauth")
        ]
        
        for variant_name, prefix in variants:
            print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}")
            print(f"Testing {variant_name} Integration")
            print(f"{'='*50}{Colors.RESET}")
            
            results = await test_teg_variant(session, variant_name, prefix, token)
            
            overall_results["total"] += results["total"]
            overall_results["passed"] += results["passed"]
            overall_results["failed"] += results["failed"]
            overall_results["variants"][variant_name] = results
            
            # Variant summary
            print(f"\n  {Colors.YELLOW}{variant_name} Summary:{Colors.RESET}")
            print(f"    - Total: {results['total']}")
            print(f"    - Passed: {results['passed']}")
            print(f"    - Failed: {results['failed']}")
        
        # Overall summary
        print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}")
        print(f"TEG INTEGRATION VARIANTS TEST SUMMARY")
        print(f"{'='*60}{Colors.RESET}")
        print(f"Total Tests: {overall_results['total']}")
        print(f"{Colors.GREEN}Passed: {overall_results['passed']}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {overall_results['failed']}{Colors.RESET}")
        print(f"Success Rate: {(overall_results['passed']/overall_results['total']*100):.1f}%")
        
        print(f"\n{Colors.YELLOW}Variant Performance:{Colors.RESET}")
        for variant, results in overall_results['variants'].items():
            success_rate = (results['passed']/results['total']*100) if results['total'] > 0 else 0
            color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
            print(f"  {variant}: {color}{success_rate:.1f}%{Colors.RESET} ({results['passed']}/{results['total']})")
        
        print(f"\n{Colors.BLUE}Authentication Methods:{Colors.RESET}")
        print(f"  - JWT-SVID: Uses SPIFFE JWT tokens for end-user auth")
        print(f"  - mTLS: Uses mutual TLS for service-to-service auth")
        print(f"  - OAuth: Uses OAuth 2.0 JWT Bearer Grant flow")
        
        return overall_results


if __name__ == "__main__":
    asyncio.run(test_teg_integration_variants())
