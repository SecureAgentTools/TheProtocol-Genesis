#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 04: Economic Transaction (Definitive)
=======================================================================
This script executes a full economic transaction. The First Citizen will
commit funds to the marketplace via a pre-transfer, then authorize the
purchase, completing the secure Prepaid Escrow protocol.

Author: Claude, AI Executor
Mission: Forge the Golden Path
Classification: AAA-QUALITY
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
MARKETPLACE_URL = "http://localhost:8020"
TEG_URL = "http://localhost:8100"
MARKETPLACE_DID = "did:cos:fbf7393c-f3c1-ee05-7eb7"

# Files from previous scripts
CREDENTIALS_FILE = "first_citizen_credentials.json"
LISTING_RECORD_FILE = "marketplace_listing.json"
TRANSACTION_RECORD_FILE = "transaction_record.json"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("[SHOP] OPERATION FIRST CITIZEN - PHASE 4: ECONOMIC TRANSACTION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mission: Execute a marketplace transaction with prepaid escrow")
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


def execute_purchase(credentials: dict, listing: dict) -> Optional[dict]:
    """Execute the two-step prepaid escrow purchase with correct auth."""
    print("\n[CONTRACT] INITIATING MARKETPLACE PURCHASE")
    print("-" * 60)
    
    api_key = credentials["api_key"]
    buyer_did = credentials["agent_did"]
    listing_id = listing["id"]
    price = Decimal(listing["price"])
    fee_percent = Decimal("0.025")
    fee = price * fee_percent
    total_cost = price + fee

    # --- Step 1: The Commitment (Pre-transfer funds to Marketplace) ---
    print(f"\n   Step 1: Committing funds. Pre-transferring {total_cost} AVT to marketplace...")
    try:
        # --- THE FIX IS HERE: Use the agent's DID as a Bearer token for TEG ---
        teg_headers = {
            "Authorization": f"Bearer {buyer_did}",
            "Content-Type": "application/json"
        }
        # --------------------------------------------------------------------
        
        transfer_response = requests.post(
            f"{TEG_URL}/api/v1/token/transfer",
            headers=teg_headers,
            json={
                "receiver_agent_id": MARKETPLACE_DID,
                "amount": str(total_cost),
                "message": f"Prepaid escrow for listing {listing_id}"
            },
            timeout=15
        )
        if transfer_response.status_code != 200:
            print(f"[FAIL] Escrow pre-transfer failed: {transfer_response.status_code}")
            print(f"   Response: {transfer_response.text}")
            return None
        
        escrow_tx_id = transfer_response.json()["transaction_id"]
        print(f"   [OK] Escrow funds committed. TX ID: {escrow_tx_id}")

    except Exception as e:
        print(f"[FAIL] Error during escrow pre-transfer: {str(e)}")
        return None

    # --- Step 2: The Authorization (Create purchase order with proof of payment) ---
    print(f"\n   Step 2: Authorizing purchase with proof of payment...")
    try:
        purchase_payload = {
            "listing_id": listing_id,
            "buyer_did": buyer_did,
            "prepaid_escrow": True,
            "escrow_tx_id": escrow_tx_id
        }
        
        # --- Use the agent's API key for the Marketplace ---
        marketplace_headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        # --------------------------------------------------

        endpoint_url = f"{MARKETPLACE_URL}/api/v1/marketplace/purchase"
        print(f"   Sending purchase authorization to: {endpoint_url}")

        response = requests.post(
            endpoint_url,
            headers=marketplace_headers,
            json=purchase_payload,
            timeout=15
        )

        if response.status_code == 200:
            order_data = response.json()
            print("[OK] Purchase authorized and order created successfully!")
            print(f"   Marketplace confirmed order ID: {order_data['order']['id']}")
            return order_data
        else:
            print(f"[FAIL] Failed to authorize purchase: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FAIL] Error authorizing purchase: {str(e)}")
        return None


def main():
    """Main execution flow."""
    print_banner()

    credentials = load_json_file(CREDENTIALS_FILE, "First Citizen credentials")
    if not credentials: sys.exit(1)
    
    listing_info = load_json_file(LISTING_RECORD_FILE, "Marketplace listing record")
    if not listing_info: sys.exit(1)

    order_details = execute_purchase(credentials, listing_info)
    
    if not order_details:
        print("\n[FAIL] ABORT: Could not complete the purchase.")
        sys.exit(1)
        
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, TRANSACTION_RECORD_FILE)
    with open(output_file, "w") as f:
        json.dump(order_details, f, indent=2)
    print(f"\n[SAVE] Transaction record saved to: {output_file}")

    print("\n" + "=" * 80)
    print("[SUCCESS] MARKETPLACE TRANSACTION INITIATED!")
    print("=" * 80)
    print("\nThe First Citizen has successfully purchased a service using the secure two-step protocol.")
    
    print("\n[NEXT] Next Steps:")
    print("   Run: python 05_complete_and_verify_transaction.py")
    
    sys.exit(0)


if __name__ == "__main__":
    main()