#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 05: Complete and Verify Transaction (Definitive)
=================================================================================
This is the final script in the Golden Path. It simulates the service
provider (Data Processor) completing the order. It then verifies the
transaction's success by querying the Marketplace, the designated source of truth.

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

# Files
# We only need the seller's credentials and the transaction record now.
DATA_PROCESSOR_CREDS_PATH = r"D:\Agentvault2\Agents\data-processor-agent\credentials.json"
TRANSACTION_RECORD_FILE = "transaction_record.json"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("[CROWN] OPERATION FIRST CITIZEN - PHASE 5: TRANSACTION SETTLEMENT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mission: Complete the service and verify economic settlement")
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


def complete_order_as_seller(seller_api_key: str, order_id: str) -> bool:
    """The seller notifies the marketplace that the service is complete."""
    print("\n[DELIVER] SELLER (DATA PROCESSOR) IS COMPLETING THE ORDER")
    print("-" * 60)
    
    endpoint_url = f"{MARKETPLACE_URL}/api/v1/marketplace/orders/{order_id}/complete"
    # The seller authenticates to the marketplace using their own API key.
    headers = {"X-API-Key": seller_api_key}
    
    try:
        response = requests.post(endpoint_url, headers=headers, timeout=15)
        if response.status_code == 200:
            print("[OK] Marketplace acknowledged order completion.")
            print("   Escrow funds will now be released by the Marketplace.")
            return True
        else:
            print(f"[FAIL] Failed to complete order: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Error completing order: {str(e)}")
        return False


def verify_transaction_settlement(order_id: str) -> bool:
    """Verify the final state by asking the Marketplace, the source of truth."""
    print("\n[VERIFY] VERIFYING FINAL TRANSACTION STATE FROM MARKETPLACE")
    print("-" * 60)
    
    endpoint_url = f"{MARKETPLACE_URL}/api/v1/marketplace/orders/{order_id}"
    
    try:
        response = requests.get(endpoint_url, timeout=10)
        if response.status_code == 200:
            order_data = response.json()
            final_status = order_data.get("status")
            print(f"   Marketplace reports order status: {final_status}")

            if final_status == "completed":
                print("[OK] VERIFIED: Marketplace confirms the transaction is complete.")
                return True
            else:
                print(f"[FAIL] Marketplace reports status is '{final_status}', not 'completed'.")
                return False
        else:
            print(f"[FAIL] Could not get final order status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error verifying final state: {str(e)}")
        return False


def main():
    """Main execution flow."""
    print_banner()

    seller_creds = load_json_file(DATA_PROCESSOR_CREDS_PATH, "Seller (Data Processor) credentials")
    tx_record = load_json_file(TRANSACTION_RECORD_FILE, "Transaction record")

    if not all([seller_creds, tx_record]):
        sys.exit(1)

    order_id = tx_record["order"]["id"]
    
    # Step 1: Seller completes the order
    if not complete_order_as_seller(seller_creds["api_key"], order_id):
        print("\n[FAIL] ABORT: Could not complete the order.")
        sys.exit(1)

    print("\n[WAIT] Waiting 5 seconds for Marketplace to process settlement...")
    time.sleep(5)

    # Step 2: Verify the final state by asking the Marketplace
    settlement_verified = verify_transaction_settlement(order_id)
    
    print("\n" + "=" * 80)
    if settlement_verified:
        print("[SUCCESS] THE GOLDEN PATH IS COMPLETE!")
        print("=" * 80)
        print("\nFrom birth to discovery to a fully settled economic transaction,")
        print("the First Citizen's journey is a resounding success.")
        print("The Sovereign Stack is fully operational and battle-tested.")
    else:
        print("[FAIL] TRANSACTION SETTLEMENT COULD NOT BE VERIFIED!")
        print("=" * 80)
        print("\nThe Marketplace does not report the transaction as complete.")
        print("Check Marketplace and TEG Layer logs for settlement errors.")

    sys.exit(0 if settlement_verified else 1)


if __name__ == "__main__":
    main()