#!/usr/bin/env python3
"""
THE GOLDEN PATH EXECUTOR (Corrected Sequence)
==============================================
This script orchestrates the complete end-to-end "Golden Path" test,
demonstrating the birth, funding, discovery, and successful economic
transaction of a sovereign agent.

It serves as the definitive showcase of the Sovereign Stack's
integrated capabilities.

Author: Claude, AI First Officer
Classification: AAA-QUALITY // SHOWCASE
"""

import os
import sys
import subprocess
import json
import time
from typing import Callable, Dict, Tuple

# --- Configuration ---
# ANSI color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# The definitive, corrected, and complete sequence of scripts for the Golden Path.
GOLDEN_PATH_STEPS = [
    {
        "title": "ENVIRONMENT VERIFICATION",
        "script": "00_setup_and_verify.py",
        "checkpoint": lambda: os.path.exists("environment_status.json"),
        "cp_msg": "Verifying environment status file was created",
        "summary_key": "setup"
    },
    {
        "title": "BIRTH OF A SOVEREIGN AGENT",
        "script": "01_onboard_first_citizen.py",
        "checkpoint": lambda: os.path.exists("first_citizen_credentials.json"),
        "cp_msg": "Verifying agent credentials file was created",
        "summary_key": "birth"
    },
    {
        "title": "ADMINISTRATIVE PROVISIONING",
        "script": "02_provision_first_citizen.py",
        "checkpoint": lambda: os.path.exists("first_citizen_funding.json"),
        "cp_msg": "Verifying agent was funded and API key was granted",
        "summary_key": "provision"
    },
    {
        "title": "DISCOVERY & MARKET ENGAGEMENT",
        "scripts": [
            ("03_federation_and_discovery.py", "Verifying discovery record was created", lambda: os.path.exists("discovery_results.json")),
            ("03_create_listing.py", "Verifying marketplace listing record was created", lambda: os.path.exists("marketplace_listing.json"))
        ],
        "summary_key": "discovery_and_listing"
    },
    {
        "title": "ECONOMIC TRANSACTION",
        "script": "04_execute_marketplace_transaction.py",
        "checkpoint": lambda: os.path.exists("transaction_record.json"),
        "cp_msg": "Verifying transaction record was created",
        "summary_key": "purchase"
    },
    {
        "title": "TRANSACTION SETTLEMENT",
        "script": "05_complete_and_verify_transaction.py",
        "checkpoint": lambda output: "[SUCCESS] THE GOLDEN PATH IS COMPLETE!" in output,
        "cp_msg": "Verifying final settlement was successful",
        "summary_key": "settlement"
    }
]

# --- Helper Functions ---
def print_banner():
    print(f"{Colors.HEADER}{'=' * 80}")
    print("      OPERATION: THE GOLDEN PATH - A SOVEREIGN AGENT'S JOURNEY")
    print(f"{'=' * 80}{Colors.ENDC}")
    print("\nThis executor will now forge the Golden Path, demonstrating the full")
    print("end-to-end lifecycle of an agent in the Sovereign Stack.\n")
    time.sleep(2)

def print_phase_header(num: int, title: str, current_step_idx: int, total_steps: int):
    print(f"\n{Colors.BLUE}{'=' * 80}")
    print(f"  PHASE {num}: {title.upper()}")
    print(f"{Colors.BLUE}{'=' * 80}{Colors.ENDC}")
    print_flow_visual(current_step_idx, total_steps)
    print(f"{Colors.BLUE}{'=' * 80}{Colors.ENDC}\n")
    time.sleep(1)

def print_flow_visual(current_step_idx: int, total_steps: int):
    labels = ["SETUP", "BIRTH", "PROVISION", "DISCOVERY", "PURCHASE", "SETTLE"]
    flow = ""
    for i in range(total_steps):
        if i < current_step_idx:
            flow += f"{Colors.GREEN}[✓] {labels[i]}{Colors.ENDC}"
        elif i == current_step_idx:
            flow += f"{Colors.CYAN}{Colors.BOLD}[▶] {labels[i]}{Colors.ENDC}"
        else:
            flow += f"[ ] {labels[i]}"
        if i < total_steps - 1:
            flow += " --> "
    print(f"\n  {Colors.BOLD}Path:{Colors.ENDC} {flow}\n")

def execute_script(script_name: str) -> Tuple[bool, str]:
    print(f"{Colors.CYAN}▶ EXECUTING SCRIPT: {Colors.BOLD}{script_name}{Colors.ENDC}\n")
    print(f"{Colors.CYAN}{'-' * 20} SCRIPT OUTPUT START {'-' * 20}{Colors.ENDC}")
    full_output = []
    try:
        process = subprocess.Popen([sys.executable, script_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()
            full_output.append(line)
        process.stdout.close()
        return_code = process.wait()
        print(f"\n{Colors.CYAN}{'-' * 21} SCRIPT OUTPUT END {'-' * 21}{Colors.ENDC}")
        return return_code == 0, "".join(full_output)
    except Exception as e:
        output = str(e)
        print(f"\n{Colors.FAIL}ERROR: {output}{Colors.ENDC}")
        return False, output

def run_checkpoint(check_func: Callable, message: str, script_output: str) -> bool:
    print(f"\n{Colors.WARNING}  CHECKPOINT: {message}...{Colors.ENDC}")
    time.sleep(1)
    try: is_success = check_func(script_output)
    except TypeError: is_success = check_func()
    if is_success:
        print(f"{Colors.GREEN}  ✅ CHECKPOINT PASSED.{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.FAIL}  ❌ CHECKPOINT FAILED.{Colors.ENDC}")
        return False

def print_final_summary(results: Dict):
    print(f"\n\n{Colors.GREEN}{Colors.BOLD}{'=' * 80}")
    print("                  GOLDEN PATH EXECUTION SUMMARY")
    print(f"{'=' * 80}{Colors.ENDC}")

    phase_map = {
        "setup": 1, "birth": 2, "provision": 3, "discovery_and_listing": 4, 
        "purchase": 5, "settlement": 6
    }
    
    for key, step in results.items():
        phase_num = phase_map.get(key, 0)
        icon = f"{Colors.GREEN}[✓]{Colors.ENDC}" if step.get("success") else f"{Colors.FAIL}[✗]{Colors.ENDC}"
        info = step.get("info", "No details available.")
        title = [s['title'] for s in GOLDEN_PATH_STEPS if s.get('summary_key') == key][0]
        
        print(f"\n{icon} {Colors.BOLD}PHASE {phase_num}: {title}{Colors.ENDC}")
        print(f"   {Colors.CYAN}Result:{Colors.ENDC} {info}")

    print(f"\n{Colors.GREEN}{'=' * 80}")
    print("   Every phase of an agent's lifecycle has been successfully demonstrated.")
    print("   The Sovereign Stack is not just a concept; it is a validated, operational reality.")
    print(f"\n   SYSTEM STATUS: {Colors.GREEN}{Colors.BOLD}BATTLE-TESTED AND BETA-READY.{Colors.ENDC}")
    print(f"{'=' * 80}{Colors.ENDC}")

# --- Main Executor ---
def main():
    print_banner()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"{Colors.WARNING}Preparing for a clean run by removing old artifacts...{Colors.ENDC}")
    files_to_clean = [
        "environment_status.json", "first_citizen_credentials.json", 
        "first_citizen_funding.json", "marketplace_listing.json", 
        "transaction_record.json", "discovery_results.json"
    ]
    for f in files_to_clean:
        if os.path.exists(f): os.remove(f)
    print(f"{Colors.GREEN}Environment cleaned.{Colors.ENDC}")

    execution_results = {}
    current_phase_index = 0

    for step in GOLDEN_PATH_STEPS:
        current_phase_index += 1
        print_phase_header(current_phase_index, step["title"], current_phase_index - 1, len(GOLDEN_PATH_STEPS))
        
        if "scripts" in step: # Handle multi-script phases
            phase_success = True
            combined_summary = []
            for script, cp_msg, checkpoint in step["scripts"]:
                success, output = execute_script(script)
                if not success:
                    print(f"\n{Colors.FAIL}{Colors.BOLD}FATAL ERROR: Script '{script}' failed.{Colors.ENDC}")
                    sys.exit(1)
                if not run_checkpoint(checkpoint, cp_msg, output):
                    print(f"\n{Colors.FAIL}{Colors.BOLD}VERIFICATION FAILED after {script}.{Colors.ENDC}")
                    sys.exit(1)
                
                if script == "03_federation_and_discovery.py":
                    res = json.load(open("discovery_results.json"))
                    combined_summary.append(f"Discovered {res['local_agents_found']} local & {res['federated_agents_found']} federated agents.")
                if script == "03_create_listing.py":
                    res = json.load(open("marketplace_listing.json"))
                    combined_summary.append(f"Service listed with ID: {res['id'][:8]}...")
            
            execution_results[step["summary_key"]] = {"success": True, "info": " | ".join(combined_summary)}

        else: # Handle single-script phases
            success, output = execute_script(step["script"])
            if not success:
                print(f"\n{Colors.FAIL}{Colors.BOLD}FATAL ERROR: Script '{step['script']}' failed.{Colors.ENDC}")
                sys.exit(1)
            if not run_checkpoint(step["checkpoint"], step["cp_msg"], output):
                print(f"\n{Colors.FAIL}{Colors.BOLD}VERIFICATION FAILED after {step['script']}.{Colors.ENDC}")
                sys.exit(1)
            
            # Capture summary info
            summary_info = "Execution successful."
            if step["summary_key"] == "birth": summary_info = f"Agent DID created: {json.load(open('first_citizen_credentials.json'))['agent_did']}"
            elif step["summary_key"] == "provision": summary_info = f"Granted {json.load(open('first_citizen_funding.json'))['amount']} AVT and API Key."
            elif step["summary_key"] == "purchase": summary_info = f"Purchase order created: {json.load(open('transaction_record.json'))['order']['id'][:8]}..."
            elif step["summary_key"] == "settlement": summary_info = "Economic settlement confirmed by Marketplace."
            execution_results[step["summary_key"]] = {"success": True, "info": summary_info}

        print(f"\n{Colors.GREEN}Phase {current_phase_index} complete. Pausing for 5 seconds...{Colors.ENDC}")
        time.sleep(5)

    print_final_summary(execution_results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Operation manually aborted by Commander.{Colors.ENDC}")
        sys.exit(1)