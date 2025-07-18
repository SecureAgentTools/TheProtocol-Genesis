#!/usr/bin/env python3
"""Quick test of the correct API key"""

import requests

# Test with the NEW correct API key
REGISTRY_A_URL = "http://localhost:8000"
REGISTRY_A_API_KEY = "avreg_eJx7JyZWspw29zO8A_EcsMPsA6_lrO7O6eFwzGaIG2I"  # New key

print("Testing NEW Registry A API key...")
print(f"Key: {REGISTRY_A_API_KEY}")

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
        
        # Try with OLD key
        print("\nTrying with OLD API key...")
        OLD_KEY = "avreg_eJx7JyZWspw29zO8A_EcsMDsA6_lrL7O6eFwzGaIG2I"
        response2 = requests.post(
            f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
            headers={
                "X-Api-Key": OLD_KEY,
                "Content-Type": "application/json"
            },
            json={
                "agent_type_hint": "sovereign-citizen",
                "requested_by": "commander@agentvault.com",
                "description": "Test bootstrap token"
            },
            timeout=10
        )
        print(f"Old key status: {response2.status_code}")
        if response2.status_code == 200:
            print("OLD KEY WORKS!")
            
except Exception as e:
    print(f"ERROR: {str(e)}")
