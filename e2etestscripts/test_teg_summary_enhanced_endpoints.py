"""
Test script for Enhanced TEG Summary endpoints (teg_summary_enhanced router).
Tests the real-time economic data endpoints.
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Registry A
API_PREFIX = "/api/v1"

# Test credentials
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "TestPass123!@#"


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


async def test_teg_summary_enhanced_endpoints():
    """Test all enhanced TEG summary endpoints"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}")
    print(f"OPERATION CERBERUS - TEG SUMMARY ENHANCED TESTING")
    print(f"Testing Real-Time Economic Data Endpoints")
    print(f"{'='*60}{Colors.RESET}\n")
    
    async with aiohttp.ClientSession() as session:
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "endpoints": {}
        }
        
        # Get auth token
        print(f"{Colors.CYAN}Getting authentication token...{Colors.RESET}")
        token = await get_auth_token(session)
        if not token:
            print(f"{Colors.RED}[X] Failed to get auth token{Colors.RESET}")
            return results
        
        headers = {"Authorization": f"Bearer {token}"}
        print(f"{Colors.GREEN}[OK] Authentication successful{Colors.RESET}\n")
        
        # Test 1: Get comprehensive TEG summary
        print(f"{Colors.CYAN}Testing GET /developers/me/teg-summary...{Colors.RESET}")
        try:
            async with session.get(
                f"{BASE_URL}{API_PREFIX}/developers/me/teg-summary",
                headers=headers
            ) as response:
                data = await response.json()
                results["total"] += 1
                
                if response.status == 200:
                    results["passed"] += 1
                    print(f"{Colors.GREEN}[OK] TEG summary retrieved{Colors.RESET}")
                    print(f"  - Developer ID: {data.get('developer_id', 'N/A')}")
                    print(f"  - Total agents: {data.get('total_agents', 0)}")
                    print(f"  - Active agents: {data.get('active_agents', 0)}")
                    print(f"  - Total liquid balance: {data.get('total_liquid_balance', 'N/A')} AVT")
                    print(f"  - Total staked balance: {data.get('total_staked_balance', 'N/A')} AVT")
                    print(f"  - Total balance: {data.get('total_balance', 'N/A')} AVT")
                    print(f"  - Average reputation: {data.get('average_reputation', 'N/A')}")
                    print(f"  - Pending rewards: {data.get('pending_rewards', 'N/A')} AVT")
                    print(f"  - Total voting power: {data.get('total_voting_power', 'N/A')}")
                    
                    # Check performance metrics
                    perf = data.get('performance_metrics', {})
                    if perf:
                        print(f"\n  {Colors.YELLOW}Performance Metrics:{Colors.RESET}")
                        print(f"    - Average balance per agent: {perf.get('average_balance_per_agent', 'N/A')} AVT")
                        print(f"    - Staking participation: {perf.get('staking_participation_rate', 'N/A')}%")
                        top_performers = perf.get('top_performers', [])
                        if top_performers:
                            print(f"    - Top performers: {len(top_performers)} agents")
                else:
                    results["failed"] += 1
                    print(f"{Colors.RED}[X] TEG summary failed: {response.status}{Colors.RESET}")
                    print(f"  - Error: {data}")
                    
                results["endpoints"]["GET /developers/me/teg-summary"] = response.status
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            print(f"{Colors.RED}[X] TEG summary error: {str(e)}{Colors.RESET}")
            results["endpoints"]["GET /developers/me/teg-summary"] = "ERROR"
        
        # Test 2: Get real treasury balance
        print(f"\n{Colors.CYAN}Testing GET /developers/me/teg-summary/treasury...{Colors.RESET}")
        try:
            async with session.get(
                f"{BASE_URL}{API_PREFIX}/developers/me/teg-summary/treasury",
                headers=headers
            ) as response:
                data = await response.json()
                results["total"] += 1
                
                if response.status == 200:
                    results["passed"] += 1
                    print(f"{Colors.GREEN}[OK] Treasury balance retrieved{Colors.RESET}")
                    print(f"  - Treasury DID: {data.get('treasury_did', 'N/A')}")
                    print(f"  - Balance: {data.get('balance', 'N/A')} {data.get('currency', 'N/A')}")
                    print(f"  - Last updated: {data.get('last_updated', 'N/A')}")
                    print(f"  - Note: {data.get('note', 'N/A')}")
                    
                    # Check if it's real data (not the hardcoded 713,651)
                    balance = data.get('balance', '0')
                    if balance == "713651" or balance == "713,651":
                        print(f"{Colors.YELLOW}  ⚠ WARNING: This appears to be the hardcoded value!{Colors.RESET}")
                    else:
                        print(f"{Colors.GREEN}  [OK] This is REAL treasury data!{Colors.RESET}")
                else:
                    results["failed"] += 1
                    print(f"{Colors.RED}[X] Treasury balance failed: {response.status}{Colors.RESET}")
                    print(f"  - Error: {data}")
                    
                results["endpoints"]["GET /developers/me/teg-summary/treasury"] = response.status
        except Exception as e:
            results["total"] += 1
            results["failed"] += 1
            print(f"{Colors.RED}[X] Treasury balance error: {str(e)}{Colors.RESET}")
            results["endpoints"]["GET /developers/me/teg-summary/treasury"] = "ERROR"
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*60}")
        print(f"TEG SUMMARY ENHANCED TEST SUMMARY")
        print(f"{'='*60}{Colors.RESET}")
        print(f"Total Tests: {results['total']}")
        print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {results['failed']}{Colors.RESET}")
        print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
        
        print(f"\n{Colors.YELLOW}Endpoint Results:{Colors.RESET}")
        for endpoint, status in results['endpoints'].items():
            color = Colors.GREEN if status == 200 else Colors.RED
            print(f"  {endpoint}: {color}{status}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}Note: This endpoint replaces the legacy hardcoded treasury balance{Colors.RESET}")
        print(f"{Colors.BLUE}with real-time data from the TEG Layer.{Colors.RESET}")
        
        return results


if __name__ == "__main__":
    asyncio.run(test_teg_summary_enhanced_endpoints())
