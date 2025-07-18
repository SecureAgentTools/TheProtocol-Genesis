"""
OPERATION CERBERUS - BETA STRIKE MASTER TEST CAMPAIGN
Comprehensive test suite for all 7 integrated routers.
"""
import asyncio
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple


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


def print_banner():
    """Print the Operation Cerberus banner"""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*80}")
    print(f"      OPERATION CERBERUS - BETA STRIKE TEST CAMPAIGN")
    print(f"         Testing 7 Enhanced Routers - 40+ New Endpoints")
    print(f"{'='*80}{Colors.RESET}\n")
    
    print(f"{Colors.CYAN}Mission Objectives:{Colors.RESET}")
    print(f"  1. {Colors.YELLOW}auth_secure{Colors.RESET}         - Enhanced authentication with recovery keys")
    print(f"  2. {Colors.YELLOW}disputes_enhanced{Colors.RESET}   - Beta Strike dispute resolution system")
    print(f"  3. {Colors.YELLOW}staking_enhanced{Colors.RESET}    - Economic Engine with idempotency")
    print(f"  4. {Colors.YELLOW}teg_summary_enhanced{Colors.RESET} - Real-time economic data")
    print(f"  5. {Colors.YELLOW}teg_jwt_svid{Colors.RESET}       - TEG with JWT-SVID authentication")
    print(f"  6. {Colors.YELLOW}teg_mtls{Colors.RESET}           - TEG with mTLS authentication")
    print(f"  7. {Colors.YELLOW}teg_oauth{Colors.RESET}          - TEG with OAuth 2.0 authentication\n")


async def run_test_script(script_name: str) -> Tuple[bool, Dict]:
    """Run a single test script and capture results"""
    print(f"{Colors.CYAN}Executing: {script_name}...{Colors.RESET}")
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if successful
        success = result.returncode == 0
        
        # Parse output for summary (looking for pass/fail counts)
        output = result.stdout
        
        # Extract test counts from output
        total = 0
        passed = 0
        failed = 0
        
        for line in output.split('\n'):
            if 'Total Tests:' in line:
                try:
                    total = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Passed:' in line and '\033[92m' in line:  # Look for green color code
                try:
                    passed = int(line.split('Passed:')[1].split('\033')[0].strip())
                except:
                    pass
            elif 'Failed:' in line and '\033[91m' in line:  # Look for red color code
                try:
                    failed = int(line.split('Failed:')[1].split('\033')[0].strip())
                except:
                    pass
        
        return success, {
            'total': total,
            'passed': passed,
            'failed': failed,
            'output': output,
            'error': result.stderr
        }
        
    except Exception as e:
        return False, {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'output': '',
            'error': str(e)
        }


async def main():
    """Run all test scripts and provide summary"""
    print_banner()
    
    # Define test scripts
    test_scripts = [
        ("test_auth_secure_endpoints.py", "Enhanced Authentication"),
        ("test_disputes_enhanced_endpoints.py", "Enhanced Disputes"),
        ("test_staking_enhanced_endpoints.py", "Enhanced Staking"),
        ("test_teg_summary_enhanced_endpoints.py", "Enhanced TEG Summary"),
        ("test_teg_integration_variants_endpoints.py", "TEG Integration Variants")
    ]
    
    # Overall results
    overall_results = {
        'total_tests': 0,
        'total_passed': 0,
        'total_failed': 0,
        'scripts_passed': 0,
        'scripts_failed': 0,
        'details': {}
    }
    
    # Run each test
    print(f"{Colors.BOLD}Starting test campaign...{Colors.RESET}\n")
    
    for script_name, description in test_scripts:
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
        print(f"Testing: {description}")
        print(f"Script: {script_name}")
        print(f"{'='*60}{Colors.RESET}\n")
        
        success, results = await run_test_script(script_name)
        
        if success and results['total'] > 0:
            overall_results['scripts_passed'] += 1
            print(f"\n{Colors.GREEN}[OK] {description} - PASSED{Colors.RESET}")
        else:
            overall_results['scripts_failed'] += 1
            print(f"\n{Colors.RED}[X] {description} - FAILED{Colors.RESET}")
            if results['error']:
                print(f"{Colors.RED}Error: {results['error'][:200]}...{Colors.RESET}")
        
        # Update totals
        overall_results['total_tests'] += results['total']
        overall_results['total_passed'] += results['passed']
        overall_results['total_failed'] += results['failed']
        overall_results['details'][script_name] = results
        
        # Show mini summary
        if results['total'] > 0:
            success_rate = (results['passed'] / results['total']) * 100
            color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
            print(f"Results: {results['passed']}/{results['total']} passed ({color}{success_rate:.1f}%{Colors.RESET})")
    
    # Final summary
    print(f"\n\n{Colors.BOLD}{Colors.PURPLE}{'='*80}")
    print(f"OPERATION CERBERUS - FINAL REPORT")
    print(f"{'='*80}{Colors.RESET}\n")
    
    print(f"{Colors.CYAN}Campaign Statistics:{Colors.RESET}")
    print(f"  Test Scripts Run: {len(test_scripts)}")
    print(f"  Scripts Passed: {Colors.GREEN}{overall_results['scripts_passed']}{Colors.RESET}")
    print(f"  Scripts Failed: {Colors.RED}{overall_results['scripts_failed']}{Colors.RESET}")
    
    print(f"\n{Colors.CYAN}Endpoint Test Results:{Colors.RESET}")
    print(f"  Total Tests: {overall_results['total_tests']}")
    print(f"  Tests Passed: {Colors.GREEN}{overall_results['total_passed']}{Colors.RESET}")
    print(f"  Tests Failed: {Colors.RED}{overall_results['total_failed']}{Colors.RESET}")
    
    if overall_results['total_tests'] > 0:
        overall_success_rate = (overall_results['total_passed'] / overall_results['total_tests']) * 100
        color = Colors.GREEN if overall_success_rate >= 80 else Colors.YELLOW if overall_success_rate >= 50 else Colors.RED
        print(f"  Success Rate: {color}{overall_success_rate:.1f}%{Colors.RESET}")
    
    print(f"\n{Colors.CYAN}Detailed Results:{Colors.RESET}")
    for script_name, description in test_scripts:
        results = overall_results['details'].get(script_name, {})
        if results['total'] > 0:
            success_rate = (results['passed'] / results['total']) * 100
            color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
            print(f"  {description}: {color}{results['passed']}/{results['total']} ({success_rate:.1f}%){Colors.RESET}")
        else:
            print(f"  {description}: {Colors.RED}No tests run{Colors.RESET}")
    
    # Mission status
    print(f"\n{Colors.BOLD}{Colors.PURPLE}{'='*80}")
    if overall_results['scripts_failed'] == 0 and overall_results['total_failed'] == 0:
        print(f"{Colors.GREEN}MISSION STATUS: COMPLETE SUCCESS{Colors.RESET}")
        print(f"{Colors.GREEN}All Beta Strike endpoints integrated and operational!{Colors.RESET}")
    elif overall_results['total_passed'] > overall_results['total_failed']:
        print(f"{Colors.YELLOW}MISSION STATUS: PARTIAL SUCCESS{Colors.RESET}")
        print(f"{Colors.YELLOW}Most endpoints operational, some issues detected.{Colors.RESET}")
    else:
        print(f"{Colors.RED}MISSION STATUS: CRITICAL ISSUES{Colors.RESET}")
        print(f"{Colors.RED}Multiple endpoint failures detected.{Colors.RESET}")
    print(f"{'='*80}{Colors.RESET}\n")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cerberus_beta_strike_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("OPERATION CERBERUS - BETA STRIKE TEST REPORT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("="*60 + "\n\n")
        f.write(f"Total Tests: {overall_results['total_tests']}\n")
        f.write(f"Passed: {overall_results['total_passed']}\n")
        f.write(f"Failed: {overall_results['total_failed']}\n")
        f.write(f"Success Rate: {overall_success_rate:.1f}%\n")
    
    print(f"{Colors.CYAN}Report saved to: {report_file}{Colors.RESET}")
    
    return overall_results


if __name__ == "__main__":
    asyncio.run(main())
