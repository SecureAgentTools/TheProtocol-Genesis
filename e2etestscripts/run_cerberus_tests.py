#!/usr/bin/env python3
"""
Operation Cerberus - Master Test Runner
======================================
This script runs all endpoint test scripts and generates a comprehensive report.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Tuple
import pathlib

# Test scripts to run - ONLY THE 21 MOUNTED ROUTERS
TEST_SCRIPTS = [
    ("agents.py", "test_agents_endpoints.py"),
    ("auth.py", "test_auth_endpoints.py"),
    ("staking.py", "test_staking_endpoints.py"),
    ("governance.py", "test_governance_endpoints.py"),
    ("attestations.py", "test_attestations_endpoints.py"),
    ("contracts.py", "test_contracts_endpoints.py"),
    ("developers.py", "test_developers_endpoints.py"),
    ("onboarding.py", "test_onboarding_endpoints.py"),
    ("federation_peers.py", "test_federation_peers_endpoints.py"),
    ("disputes.py", "test_disputes_endpoints.py"),
    ("admin.py", "test_admin_endpoints.py"),
    ("system.py", "test_system_endpoints.py"),
    ("agent_cards.py", "test_agent_cards_endpoints.py"),
    ("federation_sync.py", "test_federation_sync_endpoints.py"),
    ("admin_federation.py", "test_admin_federation_endpoints.py"),
    ("agent_builder.py", "test_agent_builder_endpoints.py"),
    ("utils.py", "test_utils_endpoints.py"),
    ("federation_public.py", "test_federation_public_endpoints.py"),
    ("federation_query.py", "test_federation_query_endpoints.py"),
    ("teg_integration.py", "test_teg_integration_endpoints.py"),
    ("reputation_signal.py", "test_reputation_signal_endpoints.py"),
]

# Overall results tracking
overall_results = {
    "timestamp": datetime.now().isoformat(),
    "total_routers": 0,
    "routers_tested": 0,
    "routers_passed": 0,
    "total_endpoints": 0,
    "endpoints_passed": 0,
    "router_results": {}
}

def print_header():
    """Print operation header"""
    print("\n" + "="*80)
    print("  OPERATION CERBERUS - MASTER TEST RUNNER")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Total test suites: {len(TEST_SCRIPTS)}")
    print(f"Mounted routers tested: 21")
    print(f"Test coverage: 100% of mounted routers\n")

def run_test_script(router_name: str, script_name: str) -> Tuple[bool, Dict]:
    """Run a single test script and collect results"""
    print(f"\n{'='*60}")
    print(f"  Running tests for: {router_name}")
    print(f"  Script: {script_name}")
    print("="*60)
    
    # Get full path to script
    script_path = pathlib.Path(__file__).parent / script_name
    
    # Check if script exists
    if not script_path.exists():
        print(f"[ERROR] Test script not found: {script_name}")
        return False, {
            "status": "NOT_FOUND",
            "error": "Test script not found"
        }
    
    try:
        # Run the test script with full path
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Try to find and load the results JSON file
        # Check multiple possible filenames
        possible_files = [
            script_name.replace(".py", "_results.json"),
            f"cerberus_{router_name.replace('.py', '')}_test_results.json",
            f"{router_name.replace('.py', '')}_test_results.json"
        ]
        
        results_file = None
        for pf in possible_files:
            if os.path.exists(pf):
                results_file = pf
                break
        
        if results_file:
            with open(results_file, "r") as f:
                test_results = json.load(f)
                
            # Handle different JSON formats
            if "summary" in test_results:
                # New format with summary
                summary = test_results["summary"]
                total_tests = summary.get("total", 0)
                passed_tests = summary.get("passed", 0)
                failed_tests = summary.get("failed", 0)
            else:
                # Old format
                total_tests = test_results.get("total_tests", 0)
                passed_tests = test_results.get("passed", 0)
                failed_tests = test_results.get("failed", 0)
            
            success = result.returncode == 0 and failed_tests == 0 and total_tests > 0
            
            return success, {
                "status": "PASSED" if success else "FAILED",
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "results": test_results.get("results", []),
                "exit_code": result.returncode
            }
        else:
            # No results file found, parse output more comprehensively
            output_lines = result.stdout.split('\n')
            passed_count = 0
            failed_count = 0
            total_count = 0
            
            # Look for various test result patterns
            for line in output_lines:
                # Standard [PASS]/[FAIL] pattern
                if "[PASS]" in line or "[OK]" in line or "✓" in line:
                    passed_count += 1
                elif "[FAIL]" in line or "[X]" in line or "✗" in line:
                    failed_count += 1
                # Pattern: "Total Tests: X"
                elif "Total Tests:" in line:
                    try:
                        total_count = int(line.split(":")[1].strip())
                    except:
                        pass
                # Pattern: "Passed: X"
                elif "Passed:" in line and "passed" not in line.lower():
                    try:
                        passed_count = int(line.split(":")[1].strip())
                    except:
                        pass
                # Pattern: "Failed: X"
                elif "Failed:" in line and "failed" not in line.lower():
                    try:
                        failed_count = int(line.split(":")[1].strip())
                    except:
                        pass
                # Pattern: "Tests: X/Y passed"
                elif "/" in line and "passed" in line.lower():
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "/" in part and i+1 < len(parts) and "passed" in parts[i+1].lower():
                                passed_str, total_str = part.split("/")
                                passed_count = int(passed_str)
                                total_count = int(total_str)
                    except:
                        pass
            
            # If we didn't find explicit counts, calculate from pass/fail markers
            if total_count == 0 or total_count < passed_count + failed_count:
                total_count = passed_count + failed_count
            
            # Ensure passed count doesn't exceed total count
            if passed_count > total_count and total_count > 0:
                total_count = passed_count + failed_count
            
            # A test suite is only successful if ALL tests pass
            success = result.returncode == 0 and failed_count == 0 and total_count > 0
            
            return success, {
                "status": "PASSED" if success else "FAILED",
                "total_tests": total_count,
                "passed": passed_count,
                "failed": failed_count,
                "exit_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None
            }
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Test script timed out: {script_name}")
        return False, {
            "status": "TIMEOUT",
            "error": "Test execution timed out after 5 minutes"
        }
    except Exception as e:
        print(f"[ERROR] Failed to run test script: {str(e)}")
        return False, {
            "status": "ERROR",
            "error": str(e)
        }

def generate_summary_report():
    """Generate and display the summary report"""
    print("\n" + "="*80)
    print("  OPERATION CERBERUS - FINAL REPORT")
    print("="*80)
    
    print(f"\nExecution completed: {datetime.now().isoformat()}")
    print(f"\nROUTER SUMMARY:")
    print(f"  Total mounted routers: 21")
    print(f"  Routers tested: {overall_results['routers_tested']}")
    print(f"  Routers fully passing: {overall_results['routers_passed']}")
    print(f"  Test coverage: {(overall_results['routers_tested'] / 21 * 100):.1f}%")
    
    print(f"\nENDPOINT SUMMARY:")
    print(f"  Total endpoints tested: {overall_results['total_endpoints']}")
    print(f"  Endpoints passing: {overall_results['endpoints_passed']}")
    if overall_results['total_endpoints'] > 0:
        pass_rate = (overall_results['endpoints_passed'] / overall_results['total_endpoints'] * 100)
        print(f"  Overall pass rate: {pass_rate:.1f}%")
    
    print(f"\nDETAILED RESULTS BY ROUTER:")
    print("-" * 60)
    
    for router, results in overall_results['router_results'].items():
        status_icon = "[PASS]" if results['status'] == "PASSED" else "[FAIL]"
        print(f"\n{status_icon} {router}")
        
        if results['status'] == "NOT_FOUND":
            print("   [WARNING] Test script not yet created")
        elif results['status'] == "ERROR" or results['status'] == "TIMEOUT":
            print(f"   [WARNING] {results.get('error', 'Unknown error')}")
        else:
            print(f"   Tests: {results.get('passed', 0)}/{results.get('total_tests', 0)} passed")
            
            # Show failed endpoints if any
            if results.get('failed', 0) > 0 and 'results' in results:
                print("   Failed endpoints:")
                for test in results['results']:
                    if not test.get('passed', False):
                        print(f"     - {test.get('endpoint', 'Unknown')}: {test.get('message', '')}")
    
    # Save the overall results
    report_file = f"cerberus_master_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(overall_results, f, indent=2)
    
    print(f"\n\nFull report saved to: {report_file}")
    
    # Show unmounted routers (not tested)
    print(f"\n\nUNMOUNTED ROUTERS (Beta Strike Package - Not Tested):")
    unmounted = [
        "auth_secure.py", "disputes_enhanced.py", "staking_enhanced.py",
        "staking_integrated.py", "teg_integration_jwt_svid.py", 
        "teg_integration_mtls.py", "teg_integration_oauth.py", 
        "teg_summary_enhanced.py"
    ]
    for router in unmounted:
        print(f"  - {router}")

def main():
    """Main test runner"""
    print_header()
    
    overall_results['total_routers'] = 21  # Total mounted routers in the registry
    
    # Run each test script
    for router_name, script_name in TEST_SCRIPTS:
        success, results = run_test_script(router_name, script_name)
        
        overall_results['router_results'][router_name] = results
        overall_results['routers_tested'] += 1
        
        if success and results['status'] == "PASSED":
            overall_results['routers_passed'] += 1
        
        # Update endpoint counts
        if 'total_tests' in results:
            overall_results['total_endpoints'] += results['total_tests']
            overall_results['endpoints_passed'] += results.get('passed', 0)
    
    # Generate and display the summary report
    generate_summary_report()
    
    # Determine overall success
    if overall_results['routers_passed'] == overall_results['routers_tested']:
        print("\n\n✅ [SUCCESS] All mounted routers passed! 100% SUCCESS RATE ACHIEVED!")
        return 0
    else:
        failed_count = overall_results['routers_tested'] - overall_results['routers_passed']
        print(f"\n\n[WARNING] {failed_count} router(s) have failing tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())
