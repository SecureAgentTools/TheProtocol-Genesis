#!/usr/bin/env python3
"""
Verify that the test runner correctly determines success/failure
"""

# Test the logic
test_cases = [
    # (return_code, failed_count, total_count, expected_success, description)
    (0, 0, 10, True, "All tests pass"),
    (0, 1, 10, False, "One test fails"),
    (0, 7, 8, False, "7 of 8 tests fail (disputes_enhanced case)"),
    (0, 0, 0, False, "No tests executed"),
    (1, 0, 10, False, "Non-zero exit code"),
    (0, 10, 10, False, "All tests fail"),
]

for return_code, failed_count, total_count, expected, desc in test_cases:
    # This is the new logic from our fix
    success = return_code == 0 and failed_count == 0 and total_count > 0
    
    status = "PASS" if success else "FAIL"
    correct = "✓" if success == expected else "✗"
    
    passed_count = total_count - failed_count
    print(f"{correct} {desc}:")
    print(f"   Return code: {return_code}, Tests: {passed_count}/{total_count} passed")
    print(f"   Result: {status} (expected {'PASS' if expected else 'FAIL'})")
    print()
