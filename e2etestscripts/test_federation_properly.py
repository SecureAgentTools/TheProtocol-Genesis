#!/usr/bin/env python3
"""
Create Second Citizen on Registry B to test federation discovery
"""

import sys
import os
import requests
import json
import time
from typing import Dict, Optional
from datetime import datetime

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
REGISTRY_B_URL = "http://localhost:8001"
TEG_URL = "http://localhost:8100"

# Registry B API Key (from your credentials)
REGISTRY_B_API_KEY = "avreg_d2yxb_VO1L9IieWEr4SF6oogMrOdNu2P7T3K5dKOcHk"

# Second Citizen Configuration (on Registry B)
SECOND_CITIZEN_NAME = "Second Citizen"
SECOND_CITIZEN_ID = "second-citizen-001"
SECOND_CITIZEN_DESCRIPTION = "Test agent on Registry B for federation discovery"


def get_bootstrap_token() -> Optional[str]:
    """Request a bootstrap token from Registry B."""
    print("\n[TICKET] REQUESTING BOOTSTRAP TOKEN FROM REGISTRY B")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{REGISTRY_B_URL}/api/v1/onboard/bootstrap/request-token",
            headers={
                "X-Api-Key": REGISTRY_B_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "agent_type_hint": "test-federation",
                "requested_by": "commander@agentvault.com",
                "description": "Bootstrap token for Second Citizen"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()["bootstrap_token"]
            print(f"[OK] Bootstrap token acquired: {token[:20]}...")
            return token
        else:
            print(f"[FAIL] Failed to get bootstrap token: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error requesting bootstrap token: {str(e)}")
        return None


def create_agent_on_registry_b(bootstrap_token: str) -> Optional[Dict]:
    """Create Second Citizen on Registry B."""
    print("\n[BIRTH] CREATING SECOND CITIZEN ON REGISTRY B")
    print("-" * 60)
    
    agent_card = {
        "schemaVersion": "1.0",
        "agentVersion": "1.0.0",
        "name": SECOND_CITIZEN_NAME,
        "description": SECOND_CITIZEN_DESCRIPTION,
        "humanReadableId": SECOND_CITIZEN_ID,
        "url": "https://agentvault.com/agents/second-citizen",
        "iconUrl": "https://agentvault.com/icons/second-citizen.png",
        "provider": {
            "name": "The Protocol",
            "url": "https://agentvault.com",
            "support_contact": "protocol@agentvault.com"
        },
        "tags": ["test", "federation", "registry-b"],
        "capabilities": {
            "a2aVersion": "1.0",
            "supportsPushNotifications": True,
            "supportedMessageParts": ["text", "data"],
            "teeDetails": None
        },
        "authSchemes": [
            {
                "scheme": "oauth2",
                "description": "OAuth2 client credentials flow"
            }
        ],
        "skills": [
            {
                "id": "federation-test",
                "name": "Federation Tester",
                "description": "Tests federation discovery"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_B_URL}/api/v1/onboard/create_agent",
            headers={
                "Bootstrap-Token": bootstrap_token,
                "Content-Type": "application/json"
            },
            json={
                "agent_did_method": "cos",
                "public_key_jwk": None,
                "proof_of_work_solution": None,
                "agent_card": agent_card
            },
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"[OK] Second Citizen created on Registry B!")
            print(f"   DID: {data['agent_did']}")
            print(f"   Client ID: {data['client_id']}")
            return data
        else:
            print(f"[FAIL] Failed to create agent: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error creating agent: {str(e)}")
        return None


def test_federation_discovery(agent_did: str):
    """Use Second Citizen to discover agents on Registry A through federation."""
    print("\n[TELESCOPE] TESTING FEDERATION DISCOVERY")
    print("-" * 60)
    print("Second Citizen (on Registry B) looking for agents on Registry A...")
    
    try:
        # First, discover local agents on Registry B
        print("\nStep 1: Discovering local agents on Registry B...")
        local_response = requests.get(
            f"{REGISTRY_B_URL}/api/v1/agent-cards/",
            headers={
                "Authorization": f"Bearer {agent_did}"
            },
            timeout=10
        )
        
        if local_response.status_code == 200:
            local_agents = local_response.json().get("items", [])
            print(f"[OK] Found {len(local_agents)} agents on Registry B")
            for agent in local_agents:
                print(f"   - {agent.get('name')} (local)")
        
        # Now discover federated agents from Registry A
        print("\nStep 2: Discovering federated agents from Registry A...")
        fed_response = requests.get(
            f"{REGISTRY_B_URL}/api/v1/federation/discover",
            headers={
                "Authorization": f"Bearer {agent_did}"
            },
            params={
                "registry_url": REGISTRY_A_URL
            },
            timeout=30
        )
        
        if fed_response.status_code == 200:
            fed_agents = fed_response.json().get("agents", [])
            print(f"[OK] Found {len(fed_agents)} agents on Registry A through federation!")
            
            marketplace_found = False
            data_processor_found = False
            
            for agent in fed_agents:
                name = agent.get('name', 'Unknown')
                hrid = agent.get('humanReadableId', 'N/A')
                print(f"   - {name} ({hrid}) [from Registry A]")
                
                if "marketplace" in name.lower():
                    marketplace_found = True
                if "data processor" in name.lower():
                    data_processor_found = True
            
            print("\n[RESULTS]")
            print(f"   Marketplace Agent found: {'YES' if marketplace_found else 'NO'}")
            print(f"   Data Processor found: {'YES' if data_processor_found else 'NO'}")
            
            if marketplace_found and data_processor_found:
                print("\n[SUCCESS] Federation is working perfectly!")
                print("   Agents from Registry A are discoverable from Registry B!")
            
        else:
            print(f"[FAIL] Federation discovery failed: {fed_response.status_code}")
            print(f"   Response: {fed_response.text}")
            
    except Exception as e:
        print(f"[FAIL] Error during discovery: {str(e)}")


def main():
    """Main execution flow."""
    print("\n" + "=" * 80)
    print("[GLOBE] FEDERATION DISCOVERY TEST")
    print("=" * 80)
    print("Creating an agent on Registry B to test federation discovery")
    print("=" * 80 + "\n")
    
    # Step 1: Get bootstrap token from Registry B
    bootstrap_token = get_bootstrap_token()
    if not bootstrap_token:
        print("\n[FAIL] Cannot proceed without bootstrap token")
        sys.exit(1)
    
    # Step 2: Create Second Citizen on Registry B
    agent_data = create_agent_on_registry_b(bootstrap_token)
    if not agent_data:
        print("\n[FAIL] Failed to create Second Citizen")
        sys.exit(1)
    
    # Step 3: Test federation discovery
    time.sleep(2)  # Give registries time to sync
    test_federation_discovery(agent_data["agent_did"])
    
    print("\n" + "=" * 80)
    print("FEDERATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
