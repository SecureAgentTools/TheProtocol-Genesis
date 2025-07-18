#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 03: Federation and Discovery (Corrected)
=========================================================================
This script demonstrates the federated discovery capabilities of the Protocol.
The First Citizen will use its valid API Key to discover agents both within
its own registry and across the federated Registry B.

Author: Claude, AI Executor
Mission: Forge the Golden Path
Classification: AAA-QUALITY
"""

import sys
import os
import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path to import from script 00
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
REGISTRY_B_URL = "http://localhost:8001"

# Files from previous scripts
CREDENTIALS_FILE = "first_citizen_credentials.json"
DISCOVERY_RECORD_FILE = "discovery_results.json"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("[GLOBE] OPERATION FIRST CITIZEN - PHASE 3: FEDERATION & DISCOVERY")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mission: Test federated discovery from the agent's perspective")
    print("=" * 80 + "\n")


def load_credentials() -> Optional[Dict]:
    """Load First Citizen credentials from previous script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    creds_file = os.path.join(script_dir, CREDENTIALS_FILE)
    
    if not os.path.exists(creds_file):
        print("[FAIL] ERROR: First Citizen credentials not found!")
        print(f"   Looking for: {creds_file}")
        print("   Please run 01_onboard_first_citizen.py first")
        return None
    
    with open(creds_file, "r") as f:
        credentials = json.load(f)
    
    print("[OK] First Citizen credentials loaded")
    print(f"   Name: {credentials['agent_name']}")
    print(f"   DID: {credentials['agent_did']}")
    print(f"   Registry: {credentials['registry_url']}")
    print(f"   API Key: {credentials.get('api_key', 'N/A')[:10]}...")
    return credentials


def perform_federated_discovery(registry_url: str, api_key: str) -> Optional[List[Dict]]:
    """
    Perform a federated discovery to find all visible agents.
    
    Args:
        registry_url: The URL of the agent's home registry.
        api_key: The API key of the agent performing the search.
        
    Returns:
        A list of all discovered agents, or None on failure.
    """
    print("\n[TELESCOPE] PERFORMING FEDERATED DISCOVERY")
    print("-" * 60)
    
    try:
        params = {
            "include_federated": "true",
            "limit": 100
        }
        
        headers = {
            "X-API-Key": api_key
        }
        
        print(f"   Querying {registry_url}/api/v1/agent-cards/ with federation enabled...")
        
        response = requests.get(
            f"{registry_url}/api/v1/agent-cards/",
            headers=headers,
            params=params,
            timeout=20
        )
        
        if response.status_code == 200:
            agents = response.json().get("items", [])
            print(f"[OK] Discovery successful. Found {len(agents)} total agents.")
            return agents
        else:
            print(f"[FAIL] Failed to discover agents: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error during federated discovery: {str(e)}")
        return None


def analyze_discovery_results(agents: List[Dict], searcher_did: str) -> Dict:
    """Analyze discovery results and categorize them by origin."""
    local_agents = []
    federated_agents = {}
    
    for agent in agents:
        if agent.get("agentDid") == searcher_did:
            continue
        
        origin = agent.get("origin_registry_name", "Local")
        if origin == "Local":
            local_agents.append(agent)
        else:
            if origin not in federated_agents:
                federated_agents[origin] = []
            federated_agents[origin].append(agent)
            
    return {"local": local_agents, "federated": federated_agents}


def verify_agent_found(agents: List[Dict], target_name: str) -> bool:
    """Verify a specific agent was found by name."""
    for agent in agents:
        if agent.get("name") == target_name:
            print(f"   [OK] VERIFIED: Found '{target_name}' in results.")
            return True
    print(f"   [FAIL] NOT FOUND: Could not find '{target_name}' in results.")
    return False


def save_discovery_results(credentials: Dict, results: Dict):
    """Save discovery results for audit trail."""
    federated_count = sum(len(v) for v in results["federated"].values())
    
    discovery_record = {
        "timestamp": datetime.now().isoformat(),
        "searcher_did": credentials["agent_did"],
        "local_agents_found": len(results["local"]),
        "federated_agents_found": federated_count,
        "results_by_registry": results["federated"],
        "federation_active": federated_count > 0
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, DISCOVERY_RECORD_FILE)
    with open(output_file, "w") as f:
        json.dump(discovery_record, f, indent=2)
    
    print(f"\n[SAVE] Discovery results saved to: {output_file}")


def main():
    """Main execution flow."""
    print_banner()
    
    credentials = load_credentials()
    if not credentials or not credentials.get("api_key"):
        print("[FAIL] ABORT: API Key not found in credentials. Please run 02b_...fix.py")
        sys.exit(1)

    all_discovered_agents = perform_federated_discovery(
        credentials["registry_url"], 
        credentials["api_key"]
    )
    
    if all_discovered_agents is None:
        print("\n[FAIL] ABORT: Federated discovery request failed.")
        sys.exit(1)
        
    discovery = analyze_discovery_results(all_discovered_agents, credentials["agent_did"])
    local_agents = discovery["local"]
    federated_agents = discovery["federated"]
    
    print("\n[ANALYSIS] DISCOVERY BREAKDOWN:")
    print(f"   Local agents found: {len(local_agents)}")
    for registry_name, agents in federated_agents.items():
        print(f"   Agents from {registry_name}: {len(agents)}")
    
    print("\n[CHECKPOINT] VERIFYING DISCOVERY RESULTS")
    print("-" * 60)
    
    # Check for the key local agents needed for the next steps
    dp_found = verify_agent_found(local_agents, "Premium Data Processor")
    marketplace_found = verify_agent_found(local_agents, "Sovereign Marketplace")
    
    # Check if federation is working by seeing if we got results from Registry-B
    federation_successful = "Registry-B" in federated_agents and len(federated_agents["Registry-B"]) > 0
    
    if federation_successful:
        print(f"   [OK] VERIFIED: Federation is working! Discovered {len(federated_agents['Registry-B'])} agents from Registry-B.")
    else:
        print(f"   [FAIL] NOT FOUND: No agents from Registry-B were discovered.")

    save_discovery_results(credentials, discovery)

    print("\n" + "=" * 80)
    if dp_found and marketplace_found and federation_successful:
        print("[SUCCESS] FEDERATION & DISCOVERY COMPLETE!")
    else:
        print("[WARNING] Discovery phase completed with issues.")
    print("=" * 80)
    
    print("\n[STATS] DISCOVERY SUMMARY:")
    print(f"   Data Processor (Local) Found: {'[OK]' if dp_found else '[FAIL]'}")
    print(f"   Marketplace (Local) Found:    {'[OK]' if marketplace_found else '[FAIL]'}")
    print(f"   Federation to Registry B:     {'[OK]' if federation_successful else '[FAIL]'}")
    
    print("\n[NEXT] Next Steps:")
    print("   Run: python 04_execute_marketplace_transaction.py")
    print("   This will execute an economic transaction via the marketplace")
    
    print("\n[GLOBE] The First Citizen has discovered their world!")
    
    sys.exit(0)


if __name__ == "__main__":
    main()