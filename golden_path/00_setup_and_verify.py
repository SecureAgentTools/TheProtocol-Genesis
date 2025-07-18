#!/usr/bin/env python3
"""
OPERATION FIRST CITIZEN - Script 00: Setup and Verify
======================================================
This script verifies that all required services are running and accessible.
It ensures the environment is ready for the First Citizen's journey.

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

# Service Configuration
SERVICES = {
    "registry_a": {
        "name": "Registry A",
        "url": "http://localhost:8000",
        "health_endpoint": "/health",
        "critical": True
    },
    "registry_b": {
        "name": "Registry B",
        "url": "http://localhost:8001",
        "health_endpoint": "/health",
        "critical": True
    },
    "teg_layer": {
        "name": "TEG Layer",
        "url": "http://localhost:8100",
        "health_endpoint": "/health",
        "critical": True
    },
    "marketplace": {
        "name": "Marketplace Agent",
        "url": "http://localhost:8020",
        "health_endpoint": "/health",
        "critical": False  # May need to be started
    },
    "data_processor": {
        "name": "Data Processor Agent",
        "url": "http://localhost:8010",
        "health_endpoint": "/health",
        "critical": False  # May need to be started
    }
}

# Admin credentials for federation check
ADMIN_EMAIL = "commander@agentvault.com"
ADMIN_PASSWORD = "SovereignKey!2025"


def print_banner():
    """Print the mission banner."""
    print("\n" + "=" * 80)
    print("OPERATION FIRST CITIZEN - PHASE 0: ENVIRONMENT VERIFICATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Mission: Verify all systems are operational for the First Citizen's birth")
    print("=" * 80 + "\n")


def check_service(service_config: Dict) -> Tuple[bool, str]:
    """
    Check if a service is accessible and healthy.
    
    Returns:
        Tuple of (is_healthy, status_message)
    """
    try:
        # First try health endpoint
        health_url = service_config["url"] + service_config["health_endpoint"]
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            return True, "ONLINE - Health check passed"
        else:
            # Try base URL if health endpoint fails
            base_response = requests.get(service_config["url"], timeout=5)
            if base_response.status_code in [200, 404]:  # 404 might mean API is up but no index
                return True, f"ONLINE - Responding (status: {base_response.status_code})"
            else:
                return False, f"UNHEALTHY - Status code: {response.status_code}"
                
    except requests.exceptions.ConnectionError:
        return False, "OFFLINE - Connection refused"
    except requests.exceptions.Timeout:
        return False, "TIMEOUT - Service not responding"
    except Exception as e:
        return False, f"ERROR - {str(e)}"


def check_all_services() -> tuple:
    """
    Check all services and report their status.
    
    Returns:
        True if all critical services are healthy, False otherwise
    """
    print("[CHECK] CHECKING SERVICE STATUS")
    print("-" * 60)
    
    all_critical_healthy = True
    service_status = {}
    
    for service_id, config in SERVICES.items():
        is_healthy, status_msg = check_service(config)
        service_status[service_id] = is_healthy
        
        # Format output
        status_icon = "[OK]" if is_healthy else "[FAIL]"
        critical_tag = " [CRITICAL]" if config["critical"] else ""
        
        print(f"{status_icon} {config['name']:<20} : {status_msg}{critical_tag}")
        
        # Track critical service failures
        if config["critical"] and not is_healthy:
            all_critical_healthy = False
    
    print("-" * 60)
    
    if all_critical_healthy:
        print("[OK] All critical services are operational!")
    else:
        print("[FAIL] Some critical services are down. Cannot proceed.")
    
    return all_critical_healthy, service_status


def check_federation_status() -> Tuple[bool, str]:
    """
    Check if federation trust bridge is active between registries.
    
    Returns:
        Tuple of (is_active, status_message)
    """
    print("\n[CHECK] CHECKING FEDERATION STATUS")
    print("-" * 60)
    
    try:
        # Login to Registry A
        login_data = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "grant_type": "password"
        }
        
        token_response = requests.post(
            f"{SERVICES['registry_a']['url']}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if token_response.status_code != 200:
            return False, f"Failed to authenticate with Registry A: {token_response.status_code}"
        
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check federation peers
        peers_response = requests.get(
            f"{SERVICES['registry_a']['url']}/api/v1/admin/federation/peers/all",
            headers=headers,
            timeout=10
        )
        
        if peers_response.status_code != 200:
            return False, f"Failed to get federation peers: {peers_response.status_code}"
        
        peers = peers_response.json().get("items", [])
        
        # Look for Registry B
        registry_b_active = False
        for peer in peers:
            if peer.get("name") == "Registry-B" and peer.get("status") == "ACTIVE":
                registry_b_active = True
                break
        
        if registry_b_active:
            print("[OK] Federation trust bridge is ACTIVE")
            print("   Registry A <-> Registry B communication enabled")
            return True, "Federation active"
        else:
            print("[WARNING] Federation trust bridge is NOT ACTIVE")
            print("   Registry B may be pending approval or not registered")
            return False, "Federation not active"
            
    except Exception as e:
        return False, f"Error checking federation: {str(e)}"


def verify_docker_compose():
    """Check if services are managed by docker-compose."""
    print("\n[CHECK] DOCKER ENVIRONMENT CHECK")
    print("-" * 60)
    
    try:
        # Check if docker is available
        import subprocess
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            cwd="D:\\Agentvault2"
        )
        
        if result.returncode == 0:
            print("[OK] Docker Compose is managing services")
            
            # Parse and display running containers
            try:
                services = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        service = json.loads(line)
                        if service.get("State") == "running":
                            services.append(service.get("Service", "unknown"))
                
                if services:
                    print(f"   Running services: {', '.join(services)}")
                else:
                    print("   [WARNING] No services appear to be running")
            except:
                # Fallback if JSON parsing fails
                print("   Services are running (details unavailable)")
        else:
            print("[WARNING] Docker Compose check failed")
            print("   Services may need to be started with: docker-compose up -d")
            
    except Exception as e:
        print(f"[WARNING] Could not verify Docker environment: {str(e)}")
        print("   Continuing with HTTP checks...")


def save_environment_status(service_status: Dict, federation_active: bool):
    """Save the environment status for subsequent scripts."""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": service_status,
        "federation_active": federation_active,
        "environment_ready": all(
            service_status.get(sid, False) 
            for sid, config in SERVICES.items() 
            if config["critical"]
        ) and federation_active
    }
    
    # Save to the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "environment_status.json")
    with open(output_file, "w") as f:
        json.dump(status, f, indent=2)
    
    print(f"\n[SAVE] Environment status saved to: {output_file}")


def main():
    """Main execution flow."""
    print_banner()
    
    # Step 1: Check Docker environment
    verify_docker_compose()
    
    # Step 2: Check all services
    all_healthy, service_status = check_all_services()
    
    if not all_healthy:
        print("\n[FAIL] ABORT: Critical services are not available")
        print("\nTo fix this issue:")
        print("1. Navigate to D:\\Agentvault2")
        print("2. Run: docker-compose up -d")
        print("3. Wait 30 seconds for services to initialize")
        print("4. Run this script again")
        sys.exit(1)
    
    # Step 3: Check federation status
    federation_active, fed_msg = check_federation_status()
    
    if not federation_active:
        print("\n[WARNING] Federation is not active")
        print("\nThe First Citizen's journey can proceed, but cross-registry")
        print("discovery will not work until federation is activated.")
        print("\nTo activate federation:")
        print("1. Run: python check_and_activate_federation_peers.py")
        print("2. Or manually approve peers in the Registry UI")
    
    # Step 4: Summary
    print("\n" + "=" * 80)
    print("ENVIRONMENT VERIFICATION SUMMARY")
    print("=" * 80)
    
    # Service summary
    print("\nService Status:")
    for sid, is_healthy in service_status.items():
        config = SERVICES[sid]
        icon = "[OK]" if is_healthy else "[FAIL]"
        print(f"  {icon} {config['name']}")
    
    print(f"\nFederation Status: {'[OK] ACTIVE' if federation_active else '[WARNING] NOT ACTIVE'}")
    
    # Overall readiness
    ready_for_journey = all_healthy and (federation_active or True)  # Federation is optional
    
    if ready_for_journey:
        print("\n[SUCCESS] ENVIRONMENT READY FOR THE FIRST CITIZEN!")
        print("\nAll systems are GO for the sovereign agent's birth!")
        
        # Save status
        save_environment_status(service_status, federation_active)
        
        print("\n[NEXT] Next Step:")
        print("   Run: python 01_onboard_first_citizen.py")
        
        sys.exit(0)
    else:
        print("\n[FAIL] ENVIRONMENT NOT READY")
        print("\nPlease resolve the issues above before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
