#!/usr/bin/env python3
"""Test which API key works"""

import requests

REGISTRY_A_URL = "http://localhost:8000"

# Test both keys
OLD_KEY = "avreg_COs8OL3A7ENKZflsNyBvAsRv3v2jD4BUfrwE4uPmbeQ"  # From existing scripts
NEW_KEY = "avreg_eSVyrsDw2RpxYDSYpcTF-gO6fBc1YT6r9ZkdMnLZeoU"  # From user

print("Testing API keys...")
print("=" * 60)

# Test OLD key
print("\n1. Testing OLD key (from existing scripts):")
print(f"   Key: ...{OLD_KEY[-20:]}")
try:
    response = requests.post(
        f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
        headers={
            "X-Api-Key": OLD_KEY,
            "Content-Type": "application/json"
        },
        json={
            "agent_type_hint": "test",
            "requested_by": "commander@agentvault.com"
        },
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [SUCCESS] OLD KEY WORKS!")
    else:
        print(f"   [FAIL] {response.text}")
except Exception as e:
    print(f"   [ERROR] {str(e)}")

# Test NEW key
print("\n2. Testing NEW key (from user):")
print(f"   Key: ...{NEW_KEY[-20:]}")
try:
    response = requests.post(
        f"{REGISTRY_A_URL}/api/v1/onboard/bootstrap/request-token",
        headers={
            "X-Api-Key": NEW_KEY,
            "Content-Type": "application/json"
        },
        json={
            "agent_type_hint": "test",
            "requested_by": "commander@agentvault.com"
        },
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [SUCCESS] NEW KEY WORKS!")
    else:
        print(f"   [FAIL] {response.text}")
except Exception as e:
    print(f"   [ERROR] {str(e)}")

print("\n" + "=" * 60)
print("CONCLUSION:")
if response.status_code == 200:
    print("USE THE NEW KEY!")
else:
    print("Check which key got 200 status above")
