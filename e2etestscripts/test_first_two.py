#!/usr/bin/env python3
"""Test just script 00 and 01"""

import subprocess
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

print("Testing E2E Scripts...")
print("=" * 60)

# Run script 00
print("\n[1] Running 00_setup_and_verify.py...")
result = subprocess.run(
    [sys.executable, os.path.join(script_dir, "00_setup_and_verify.py")],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
if result.returncode != 0:
    print(f"Script 00 failed with code {result.returncode}")
    sys.exit(1)

# Run script 01
print("\n[2] Running 01_onboard_first_citizen.py...")
result = subprocess.run(
    [sys.executable, os.path.join(script_dir, "01_onboard_first_citizen.py")],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
if result.returncode != 0:
    print(f"Script 01 failed with code {result.returncode}")
    sys.exit(1)

print("\n[SUCCESS] First two scripts completed!")
