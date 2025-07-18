#!/usr/bin/env python3
"""Quick API key verification"""

import requests

# Test the corrected API key
REGISTRY_A_URL = "http://localhost:8000"
REGISTRY_A_API_KEY = "avreg_eJx7JyZWspw29zO8A_EcsMDsA6_lrO7O6eFwzGaIG2I"

print("Testing Registry A API key...")
try:
    response = requests.post(
        f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
        headers={
            "X-Api-Key": REGISTRY_A_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "agent_type_hint": "sovereign-citizen",
            "requested_by": "commander@agentvault.com",
            "description": "Test bootstrap token"
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"SUCCESS! Token: {response.json()['bootstrap_token'][:20]}...")
    else:
        print(f"FAILED: {response.text}")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
