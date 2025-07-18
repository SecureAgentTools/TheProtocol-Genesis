#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 03: Create Marketplace Listing (Definitive)
=============================================================================
This script uses the Data Processor's credentials to create a REAL, valid,
and correctly structured listing on the Sovereign Marketplace.

Author: Claude, AI Executor
Mission: Forge the Golden Path
Classification: AAA-QUALITY
"""

import sys
import os
import requests
import json
from datetime import datetime

# Configuration
MARKETPLACE_URL = "http://localhost:8020"

# Credentials for the agent LISTING the service
DATA_PROCESSOR_CREDS_PATH = r"D:\Agentvault2\Agents\data-processor-agent\credentials.json"
LISTING_RECORD_FILE = "marketplace_listing.json"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("[SIGN] OPERATION FIRST CITIZEN - PHASE 3: LISTING SERVICE ON MARKETPLACE")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mission: Create a valid service listing")
    print("=" * 80 + "\n")


def load_data_processor_credentials() -> dict:
    """Load the credentials for the service provider."""
    if not os.path.exists(DATA_PROCESSOR_CREDS_PATH):
        print(f"[FAIL] ABORT: Data Processor credentials not found at {DATA_PROCESSOR_CREDS_PATH}")
        sys.exit(1)
        
    with open(DATA_PROCESSOR_CREDS_PATH, 'r') as f:
        credentials = json.load(f)
    
    print("[OK] Loaded Data Processor credentials")
    print(f"   Provider DID: {credentials['agent_did']}")
    return credentials


def create_marketplace_listing(credentials: dict):
    """Use the Data Processor's credentials to create a service listing."""
    print("\n[LISTING] Creating definitive, correctly-structured service listing...")
    
    listing_payload = {
        "provider_did": credentials["agent_did"],
        "name": "Premium Data Processing",
        "description": "High-throughput, reliable data processing services with economic guarantees.",
        "service_type": "analysis",
        "price": "50.0"
    }
    
    headers = {
        "Authorization": f"Bearer {credentials['agent_did']}",
        "Content-Type": "application/json"
    }
    
    endpoint_url = f"{MARKETPLACE_URL}/api/v1/marketplace/listings"
    print(f"   Posting to endpoint: {endpoint_url}")
    
    try:
        response = requests.post(
            endpoint_url,
            headers=headers,
            json=listing_payload,
            timeout=15
        )
        
        # --- THE FINAL FIX IS HERE ---
        # The server returns 200 OK on success, not 201 Created.
        # We now accept 200 as a valid success code.
        if response.status_code == 200:
        # ---------------------------
            data = response.json()
            listing_info = data.get("listing")
            
            if not listing_info or not listing_info.get("provider_did"):
                 print("[FAIL] Server returned success but listing is malformed (provider_did is null).")
                 return False

            print("[OK] Service listed successfully!")
            print(f"   Listing ID: {listing_info['id']}")
            print(f"   Provider DID: {listing_info['provider_did']}")
            print(f"   Price: {listing_info['price']} AVT")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(script_dir, LISTING_RECORD_FILE)
            with open(output_file, 'w') as f:
                json.dump(listing_info, f, indent=2)
            print(f"[SAVE] Listing details saved to: {output_file}")
            
            return True
        else:
            print(f"[FAIL] Failed to create listing: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Error creating listing: {str(e)}")
        return False


def main():
    """Main execution flow."""
    print_banner()
    
    provider_credentials = load_data_processor_credentials()
    
    if not create_marketplace_listing(provider_credentials):
        print("\n[FAIL] ABORT: Could not list service on marketplace.")
        sys.exit(1)
        
    print("\n" + "=" * 80)
    print("[SUCCESS] REAL SERVICE LISTING IS NOW LIVE!")
    print("=" * 80)
    print("\nThe Data Processor's service is now correctly listed on the Sovereign Marketplace.")
    print("\n[NEXT] Next Step:")
    print("   Run: python 04_execute_marketplace_transaction.py")


if __name__ == "__main__":
    main()