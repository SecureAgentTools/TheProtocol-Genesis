#!/usr/bin/env python3
"""
Operation Cerberus - Test Script for agent_builder.py endpoints
================================================================
This script tests all endpoints in the agent_builder router.
This router handles agent package generation functionality.
"""

import os
import sys
import requests
import json
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service Configuration
REGISTRY_A_URL = "http://localhost:8000"

# Test developer credentials - COMMANDER ACCOUNT
TEST_EMAIL = "commander@agentvault.com"
TEST_PASSWORD = "SovereignKey!2025"

# Test results tracking
test_results = []

def print_test_header():
    """Print test script header"""
    print("\n" + "="*60)
    print("  OPERATION CERBERUS: agent_builder.py Endpoint Tests")
    print("="*60)
    print(f"Registry URL: {REGISTRY_A_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

def log_result(passed: bool, method: str, endpoint: str, message: str = ""):
    """Log and print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    result_msg = f"{status} {method} {endpoint}"
    if message and not passed:
        result_msg += f" - {message}"
    print(result_msg)
    test_results.append({
        "endpoint": f"{method} {endpoint}",
        "passed": passed,
        "message": message
    })

def authenticate_developer() -> Optional[str]:
    """Authenticate and get JWT token for developer"""
    # Use OAuth2PasswordRequestForm format 
    auth_data = {
        "grant_type": "password",
        "username": TEST_EMAIL,  
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/auth/login",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"[INFO] Developer authentication successful")
            return token_data.get("access_token")
        else:
            print(f"[ERROR] Developer authentication failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"[ERROR] Details: {error_detail}")
            except:
                print(f"[ERROR] Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Authentication error: {str(e)}")
        return None

def test_generate_simple_wrapper():
    """Test POST /api/v1/agent-builder/generate - Simple Wrapper Agent"""
    token = authenticate_developer()
    if not token:
        log_result(False, "POST", "/api/v1/agent-builder/generate", 
                  "Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "agent_name": "Test Simple Wrapper Agent",
        "agent_description": "A test simple wrapper agent created by Operation Cerberus",
        "human_readable_id": "cerberus/test-simple-wrapper",
        "agent_builder_type": "simple_wrapper",
        "wrapper_llm_backend_type": "openai_api",  # Changed from "openai"
        "wrapper_model_name": "gpt-4",
        "wrapper_system_prompt": "You are a helpful test agent created by Operation Cerberus.",
        "wrapper_auth_type": "apiKey",  # Changed from "api_key"
        "wrapper_service_id": "test-service-id"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/agent-builder/generate",
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            # Should receive a ZIP file
            content_type = response.headers.get('content-type', '')
            if 'application/zip' in content_type:
                # Save and verify ZIP
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                # Verify it's a valid ZIP
                try:
                    with zipfile.ZipFile(tmp_path, 'r') as zf:
                        file_list = zf.namelist()
                        # Check for expected files
                        expected_files = [
                            "requirements.txt", "Dockerfile", 
                            "agent-card.json", "INSTRUCTIONS.md"
                        ]
                        missing = [f for f in expected_files if not any(f in name for name in file_list)]
                        
                        if not missing:
                            log_result(True, "POST", "/api/v1/agent-builder/generate", 
                                      f"Simple wrapper agent ZIP generated ({len(file_list)} files)")
                        else:
                            log_result(False, "POST", "/api/v1/agent-builder/generate", 
                                      f"Missing expected files: {missing}")
                except Exception as e:
                    log_result(False, "POST", "/api/v1/agent-builder/generate", 
                              f"Invalid ZIP file: {str(e)}")
                finally:
                    os.unlink(tmp_path)
            else:
                log_result(False, "POST", "/api/v1/agent-builder/generate", 
                          f"Wrong content type: {content_type}")
        else:
            log_result(False, "POST", "/api/v1/agent-builder/generate", 
                      f"Status code: {response.status_code}")
            # Print error details for debugging
            if response.status_code == 422:
                try:
                    error_detail = response.json()
                    print(f"[DEBUG] Validation error: {error_detail}")
                except:
                    print(f"[DEBUG] Response: {response.text}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/agent-builder/generate", str(e))

def test_generate_adk_agent():
    """Test POST /api/v1/agent-builder/generate - ADK Agent"""
    token = authenticate_developer()
    if not token:
        log_result(False, "POST", "/api/v1/agent-builder/generate (ADK)", 
                  "Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "agent_name": "Test ADK Agent",
        "agent_description": "A test ADK agent created by Operation Cerberus",
        "human_readable_id": "cerberus/test-adk-agent",
        "agent_builder_type": "adk_agent",
        "adk_model_name": "claude-3-5-sonnet-20241022",
        "adk_instruction": "You are a helpful ADK test agent created by Operation Cerberus.",
        "adk_tools": ["get_current_time", "google_search"]  # Changed to valid tools
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/agent-builder/generate",
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            # Should receive a ZIP file
            content_type = response.headers.get('content-type', '')
            if 'application/zip' in content_type:
                # Save and verify ZIP
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name
                
                # Verify it's a valid ZIP
                try:
                    with zipfile.ZipFile(tmp_path, 'r') as zf:
                        file_list = zf.namelist()
                        # Check for ADK-specific files
                        expected_patterns = [
                            "tools.py", "requirements.txt", 
                            "agent.py", "main.py"
                        ]
                        missing = [p for p in expected_patterns if not any(p in name for name in file_list)]
                        
                        if not missing:
                            log_result(True, "POST", "/api/v1/agent-builder/generate (ADK)", 
                                      f"ADK agent ZIP generated ({len(file_list)} files)")
                        else:
                            log_result(False, "POST", "/api/v1/agent-builder/generate (ADK)", 
                                      f"Missing expected files: {missing}")
                except Exception as e:
                    log_result(False, "POST", "/api/v1/agent-builder/generate (ADK)", 
                              f"Invalid ZIP file: {str(e)}")
                finally:
                    os.unlink(tmp_path)
            else:
                log_result(False, "POST", "/api/v1/agent-builder/generate (ADK)", 
                          f"Wrong content type: {content_type}")
        else:
            log_result(False, "POST", "/api/v1/agent-builder/generate (ADK)", 
                      f"Status code: {response.status_code}")
            # Print error details for debugging
            if response.status_code == 422:
                try:
                    error_detail = response.json()
                    print(f"[DEBUG] ADK Validation error: {error_detail}")
                except:
                    print(f"[DEBUG] ADK Response: {response.text}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/agent-builder/generate (ADK)", str(e))

def test_generate_invalid_type():
    """Test POST /api/v1/agent-builder/generate - Invalid Type"""
    token = authenticate_developer()
    if not token:
        log_result(False, "POST", "/api/v1/agent-builder/generate (Invalid)", 
                  "Authentication failed")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    request_data = {
        "agent_name": "Test Invalid Agent",
        "agent_description": "Testing invalid agent type",
        "agent_builder_type": "invalid_type"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/agent-builder/generate",
            headers=headers,
            json=request_data,
            timeout=10
        )
        
        if response.status_code == 422:
            # Expected validation error
            log_result(True, "POST", "/api/v1/agent-builder/generate (Invalid)", 
                      "Correctly rejected invalid agent type")
        else:
            log_result(False, "POST", "/api/v1/agent-builder/generate (Invalid)", 
                      f"Expected 422, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/agent-builder/generate (Invalid)", str(e))

def test_generate_no_auth():
    """Test POST /api/v1/agent-builder/generate - No Authentication"""
    request_data = {
        "agent_name": "Test Agent",
        "agent_description": "Testing without auth",
        "agent_builder_type": "simple_wrapper"
    }
    
    try:
        response = requests.post(
            f"{REGISTRY_A_URL}/api/v1/agent-builder/generate",
            json=request_data,
            timeout=10
        )
        
        if response.status_code == 401:
            log_result(True, "POST", "/api/v1/agent-builder/generate (No Auth)", 
                      "Correctly requires authentication")
        else:
            log_result(False, "POST", "/api/v1/agent-builder/generate (No Auth)", 
                      f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        log_result(False, "POST", "/api/v1/agent-builder/generate (No Auth)", str(e))

def main():
    """Run all tests for agent_builder.py endpoints"""
    print_test_header()
    
    print("[INFO] Testing agent builder endpoints\n")
    print("[NOTE] These endpoints require developer JWT authentication\n")
    
    # Run all endpoint tests
    test_generate_simple_wrapper()
    test_generate_adk_agent()
    test_generate_invalid_type()
    test_generate_no_auth()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All agent_builder.py endpoints verified successfully!")
    else:
        print(f"\n[FAILED] {total - passed} test(s) failed")
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['endpoint']}: {result['message']}")
    
    # Save results
    results_file = "cerberus_agent_builder_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "router": "agent_builder.py",
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
