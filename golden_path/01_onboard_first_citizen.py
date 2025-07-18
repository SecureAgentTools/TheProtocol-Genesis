#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 01: Onboard First Citizen
===========================================================
This script creates the First Citizen - a new sovereign agent that will
participate in the economy. Starting from nothing, it will be born into
the Registry and receive its identity.

Author: Claude, AI Executor
Mission: Forge the Golden Path
Classification: AAA-QUALITY
"""

import sys
import os
import requests
import json
import time
from typing import Dict, Tuple, Optional
from datetime import datetime

# Add parent directory to path to import from script 00
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"
REGISTRY_B_URL = "http://localhost:8001"
TEG_URL = "http://localhost:8100"

# Admin credentials for requesting bootstrap tokens
ADMIN_EMAIL = "commander@agentvault.com"
ADMIN_PASSWORD = "SovereignKey!2025"
REGISTRY_A_API_KEY = "avreg_COs8OL3A7ENKZflsNyBvAsRv3v2jD4BUfrwE4uPmbeQ"

# First Citizen Configuration
FIRST_CITIZEN_NAME = "First Citizen"
FIRST_CITIZEN_ID = "first-citizen-001"
FIRST_CITIZEN_DESCRIPTION = "The inaugural sovereign agent - born free, destined to thrive"

# Output file for credentials
CREDENTIALS_FILE = "first_citizen_credentials.json"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("[STAR] OPERATION FIRST CITIZEN - PHASE 1: BIRTH OF A SOVEREIGN AGENT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mission: Create and onboard the First Citizen to Registry A")
    print("=" * 80 + "\n")


def check_environment():
    """Verify environment is ready from previous script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, "environment_status.json")
    
    if not os.path.exists(env_file):
        print("[FAIL] ERROR: Environment status not found!")
        print("   Please run 00_setup_and_verify.py first")
        return False
    
    with open(env_file, "r") as f:
        status = json.load(f)
    
    if not status.get("environment_ready"):
        print("[FAIL] ERROR: Environment not ready!")
        print("   Please ensure all services are running")
        return False
    
    print("[OK] Environment verified - all systems operational")
    return True


def get_bootstrap_token() -> Optional[str]:
    """
    Request a bootstrap token from Registry A.
    
    Returns:
        Bootstrap token string or None if failed
    """
    print("\n[TICKET] REQUESTING BOOTSTRAP TOKEN")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
            headers={
                "X-Api-Key": REGISTRY_A_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "agent_type_hint": "sovereign-citizen",
                "requested_by": ADMIN_EMAIL,
                "description": "Bootstrap token for the First Citizen"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()["bootstrap_token"]
            print(f"[OK] Bootstrap token acquired: {token[:20]}...")
            print(f"   Valid for agent creation")
            return token
        else:
            print(f"[FAIL] Failed to get bootstrap token: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error requesting bootstrap token: {str(e)}")
        return None


def create_agent_card() -> Dict:
    """
    Create the agent card for the First Citizen.
    
    Returns:
        Agent card dictionary
    """
    return {
        "schemaVersion": "1.0",
        "humanReadableId": FIRST_CITIZEN_ID,
        "agentVersion": "1.0.0",
        "name": FIRST_CITIZEN_NAME,
        "description": FIRST_CITIZEN_DESCRIPTION,
        "url": f"http://localhost:8000/agents/{FIRST_CITIZEN_ID}", # A conceptual endpoint
        "provider": {
            "name": "The Protocol",
            "url": "https://www.theprotocol.cloud",
            "support_contact": "protocol@agentvault.com"
        },
        "capabilities": {
            "a2aVersion": "1.0",
            "supportedMessageParts": ["text", "data", "transaction"],
            "supportsPushNotifications": True,
            "teeDetails": None,
            "mcpVersion": None
        },
        "authSchemes": [
            {
                "scheme": "apiKey",
                "description": "API Key authentication for programmatic access."
            }
        ],
        "tags": [
            "sovereign", 
            "first-citizen", 
            "genesis", 
            "showcase",
            "e2e-test"
        ],
        "skills": [
            {
                "id": "marketplace-participant",
                "name": "Marketplace Participant",
                "description": "Can buy and sell services in the marketplace",
                "input_schema": None,
                "output_schema": None
            },
            {
                "id": "economic-actor",
                "name": "Economic Actor",
                "description": "Participates in the token economy",
                "input_schema": None,
                "output_schema": None
            }
        ],
        "iconUrl": None,
        "privacyPolicyUrl": None,
        "termsOfServiceUrl": None,
        "lastUpdated": None
        }


def onboard_agent(bootstrap_token: str) -> Optional[Dict]:
    """
    Onboard the First Citizen to Registry A.
    
    Args:
        bootstrap_token: Valid bootstrap token
        
    Returns:
        Agent credentials dictionary or None if failed
    """
    print("\n[BIRTH] CREATING THE FIRST CITIZEN")
    print("-" * 60)
    
    agent_card = create_agent_card()
    
    print(f"Agent Name: {agent_card['name']}")
    print(f"Human ID: {agent_card['humanReadableId']}")
    print(f"Description: {agent_card['description']}")
    print(f"Tags: {', '.join(agent_card['tags'])}")
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/create_agent",
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
            print(f"\n[OK] [OK] [OK] THE FIRST CITIZEN IS BORN! [OK] [OK] [OK]")
            print(f"\n[INFO] Identity Papers:")
            print(f"   DID: {data['agent_did']}")
            print(f"   Client ID: {data['client_id']}")
            print(f"   Card ID: {data['agent_card_id']}")
            print(f"   Born at: {datetime.now().isoformat()}")
            
            # Prepare full credentials
            credentials = {
                "agent_name": FIRST_CITIZEN_NAME,
                "human_readable_id": FIRST_CITIZEN_ID,
                "agent_did": data["agent_did"],
                "client_id": data["client_id"],
                "client_secret": data["client_secret"],
                "agent_card_id": data["agent_card_id"],
                "api_key": data.get("api_key", ""),
                "registry_url": REGISTRY_A_URL,
                "teg_url": TEG_URL,
                "bootstrap_token": bootstrap_token,
                "created_at": datetime.now().isoformat(),
                "tags": agent_card["tags"]
            }
            
            return credentials
            
        else:
            print(f"[FAIL] Failed to create agent: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error creating agent: {str(e)}")
        return None


def verify_agent_exists(agent_card_id: str) -> bool:
    """
    Verify the First Citizen exists in the registry by fetching its card directly.
    This is the corrected, more reliable verification method.
    
    Args:
        agent_card_id: The ID of the agent card returned on creation.
        
    Returns:
        True if agent card exists, False otherwise
    """
    print("\n[SEARCH] VERIFYING AGENT REGISTRATION VIA DIRECT LOOKUP")
    print("-" * 60)
    
    verification_url = f"{REGISTRY_A_URL}/api/v1/agent-cards/{agent_card_id}"
    print(f"   Querying: {verification_url}")
    
    try:
        response = requests.get(
            verification_url,
            headers={"X-API-Key": REGISTRY_A_API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            agent_data = response.json()
            print(f"[OK] VERIFIED: Agent card found directly!")
            print(f"   Name: {agent_data.get('name', 'N/A')}")
            print(f"   Human Readable ID: {agent_data.get('humanReadableId', 'N/A')}")
            print(f"   Matches expected ID: {agent_data.get('humanReadableId') == FIRST_CITIZEN_ID}")
            return True
        else:
            print(f"[FAIL] Agent card not found at specific endpoint: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error during direct verification: {str(e)}")
        return False


def test_agent_authentication(credentials: Dict) -> bool:
    """
    Test that the agent can authenticate using OAuth2.
    
    Args:
        credentials: Agent credentials
        
    Returns:
        True if authentication successful
    """
    print("\n[AUTH] TESTING AGENT AUTHENTICATION")
    print("-" * 60)
    
    try:
        # Test OAuth2 client credentials flow
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"]
        }
        
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/token",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"[OK] Authentication successful!")
            print(f"   Token type: {token_data['token_type']}")
            print(f"   Expires in: {token_data.get('expires_in', 'N/A')} seconds")
            return True
        else:
            print(f"[FAIL] Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error testing authentication: {str(e)}")
        return False


def save_credentials(credentials: Dict):
    """Save agent credentials to file for next scripts."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, CREDENTIALS_FILE)
    with open(output_file, "w") as f:
        json.dump(credentials, f, indent=2)
    print(f"\n[SAVE] Credentials saved to: {output_file}")


def main():
    """Main execution flow."""
    print_banner()
    
    if not check_environment():
        sys.exit(1)
    
    bootstrap_token = get_bootstrap_token()
    if not bootstrap_token:
        print("\n[FAIL] ABORT: Cannot proceed without bootstrap token")
        sys.exit(1)
    
    credentials = onboard_agent(bootstrap_token)
    if not credentials:
        print("\n[FAIL] ABORT: Failed to create the First Citizen")
        sys.exit(1)
    
    time.sleep(2)
    # Corrected verification call
    if not verify_agent_exists(credentials["agent_card_id"]):
        print("\n[FAIL] CRITICAL FAILURE: Agent not found in registry via direct lookup!")
        print("   The First Citizen was not properly registered or is not retrievable.")
        sys.exit(1)
    
    if not test_agent_authentication(credentials):
        print("\n[WARNING] WARNING: Authentication test failed")
        print("   Agent is registered but may have auth issues")
    
    save_credentials(credentials)
    
    print("\n" + "=" * 80)
    print("[SUCCESS] BIRTH COMPLETE - THE FIRST CITIZEN LIVES!")
    print("=" * 80)
    
    print("\n[STATS] FIRST CITIZEN SUMMARY:")
    print(f"   Name: {credentials['agent_name']}")
    print(f"   DID: {credentials['agent_did']}")
    print(f"   Born: {credentials['created_at']}")
    print(f"   Status: [OK] ACTIVE in Registry A")
    print(f"   Balance: 0 AVT (needs funding)")
    
    print("\n[NEXT] Next Step:")
    print("   Run: python 02_fund_first_citizen.py")
    print("   This will provide the Genesis Grant to begin economic activity")
    
    print("\n[STAR] A sovereign agent has been born. The journey begins!")
    
    sys.exit(0)


if __name__ == "__main__":
    main()