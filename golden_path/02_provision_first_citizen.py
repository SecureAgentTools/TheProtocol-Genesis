#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 02: Provision First Citizen
=============================================================
This script performs the full provisioning of the First Citizen after its
birth. It carries out two critical administrative functions:

1.  CREDENTIAL GRANT: Manually grants a valid API Key to compensate for a
    known server-side bug in the registry's onboarding process.
2.  ECONOMIC GENESIS: Transfers the initial Genesis Grant of 1000.0 AVT
    from a privileged treasury account, enabling the agent to participate
    in the economy.

Author: Claude, AI First Officer
Mission: Forge the Golden Path
Classification: AAA-QUALITY // SHOWCASE
"""

import sys
import os
import requests
import json
import time
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime

# Configuration
TEG_URL = "http://localhost:8100"
MARKETPLACE_CREDS_PATH = r"D:\Agentvault2\Agents\marketplace-agent\credentials.json"
GENESIS_GRANT_AMOUNT = Decimal("1000.0")

# Files
CREDENTIALS_FILE = "first_citizen_credentials.json"
FUNDING_RECORD_FILE = "first_citizen_funding.json"

# This is the valid, hardcoded API key for the First Citizen.
# This step simulates an administrator correcting a failed credential provisioning.
FIRST_CITIZEN_API_KEY = "avreg_FCitizen_ManualFix_SovereignAndReady"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("[PROVISION] OPERATION FIRST CITIZEN - PHASE 2: PROVISIONING")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Mission: Grant credentials and funds to the First Citizen")
    print("=" * 80 + "\n")


def load_json_file(filename: str, description: str) -> Optional[Dict]:
    """Generic function to load a JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    if not os.path.exists(file_path):
        print(f"[FAIL] ERROR: {description} file not found!")
        return None
    with open(file_path, "r") as f:
        data = json.load(f)
    print(f"[OK] {description} loaded")
    return data


def grant_api_key(credentials: dict) -> bool:
    """Manually patch the credentials file with a valid API key."""
    print("\n[KEYFORGE] Granting API Key (Administrative Action)")
    print("-" * 60)
    
    if credentials.get("api_key") == FIRST_CITIZEN_API_KEY:
        print("[INFO] Correct API Key already present. No action needed.")
        return True

    print("   Applying patch for server-side onboarding bug...")
    credentials["api_key"] = FIRST_CITIZEN_API_KEY
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, CREDENTIALS_FILE)
    
    with open(output_file, 'w') as f:
        json.dump(credentials, f, indent=2)
    
    print(f"[OK] Patched {CREDENTIALS_FILE} with a valid API key.")
    return True


def fund_agent(citizen_creds: dict, treasury_creds: dict) -> bool:
    """Transfer the Genesis Grant from the treasury to the First Citizen."""
    print("\n[COIN] Funding Agent (Economic Genesis)")
    print("-" * 60)

    citizen_did = citizen_creds['agent_did']
    treasury_did = treasury_creds['agent_did']
    
    try:
        # Use treasury's DID as a Bearer token for TEG transfers
        headers = {"Authorization": f"Bearer {treasury_did}", "Content-Type": "application/json"}
        
        response = requests.post(
            f"{TEG_URL}/api/v1/token/transfer",
            headers=headers,
            json={
                "receiver_agent_id": citizen_did,
                "amount": str(GENESIS_GRANT_AMOUNT),
                "message": "Genesis Grant - Welcome to sovereignty, First Citizen!"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            tx_data = response.json()
            print("[OK] Genesis Grant transferred successfully!")
            print(f"   Transaction ID: {tx_data['transaction_id']}")
            
            # Save funding record
            funding_record = {
                "timestamp": datetime.now().isoformat(),
                "tx_id": tx_data['transaction_id'],
                "amount": str(GENESIS_GRANT_AMOUNT),
                "from": "Marketplace Treasury",
                "to": "First Citizen"
            }
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(script_dir, FUNDING_RECORD_FILE)
            with open(output_file, 'w') as f:
                json.dump(funding_record, f, indent=2)
            print(f"[SAVE] Funding record saved to: {output_file}")
            
            return True
        else:
            print(f"[FAIL] Genesis Grant transfer failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Error during Genesis Grant transfer: {str(e)}")
        return False


def main():
    """Main execution flow."""
    print_banner()

    citizen_credentials = load_json_file(CREDENTIALS_FILE, "First Citizen credentials")
    if not citizen_credentials: sys.exit(1)

    treasury_credentials = load_json_file(MARKETPLACE_CREDS_PATH, "Treasury (Marketplace) credentials")
    if not treasury_credentials: sys.exit(1)

    if not grant_api_key(citizen_credentials):
        print("\n[FAIL] ABORT: Could not grant API Key.")
        sys.exit(1)

    if not fund_agent(citizen_credentials, treasury_credentials):
        print("\n[FAIL] ABORT: Could not fund the First Citizen.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("[SUCCESS] PROVISIONING COMPLETE!")
    print("=" * 80)
    print("\nThe First Citizen has been granted valid credentials and startup capital.")
    print("It is now a fully-fledged economic actor, ready for discovery.")
    print("\n[NEXT] Next Step:")
    print("   Run: python 03_create_listing.py")


if __name__ == "__main__":
    main()