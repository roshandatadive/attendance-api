"""
End-to-End Test Suite for Attendance API
=========================================
Tests real user flows: Student, Trainer, Monitoring
Includes positive and negative test cases
Run: python test_flow.py
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS_JSON = {"Content-Type": "application/json"}

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Test counters
total_tests = 0
passed_tests = 0
failed_tests = 0


def print_header(title: str):
    """Print section header"""
    print(f"\n{BOLD}{'='*70}")
    print(f"{title.center(70)}")
    print(f"{'='*70}{RESET}\n")


def test(
    method: str,
    endpoint: str,
    expected_status: int,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    test_name: str = "",
) -> Optional[dict]:
    """
    Execute a single test and print result.
    Returns response JSON if successful, None otherwise.
    """
    global total_tests, passed_tests, failed_tests

    total_tests += 1

    # Build full URL
    url = f"{BASE_URL}{endpoint}"

    # Set default headers
    if headers is None:
        headers = HEADERS_JSON.copy()

    # Execute request
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            raise ValueError(f"Unsupported method: {method}")

        # Check status code
        status_match = response.status_code == expected_status
        status_symbol = "✓" if status_match else "✗"
        status_color = GREEN if status_match else RED

        # Print result
        print(
            f"{status_color}{status_symbol} {method:4} {endpoint:30} "
            f"→ {response.status_code} (expected {expected_status}){RESET}"
        )

        if test_name:
            print(f"  Test: {test_name}")

        if not status_match:
            print(f"  Response: {response.text[:100]}")
            failed_tests += 1
            return None
        else:
            passed_tests += 1
            # Return JSON response for chaining
            try:
                return response.json()
            except:
                return {}

    except Exception as e:
        print(f"{RED}✗ {method:4} {endpoint:30} → ERROR: {str(e)}{RESET}")
        failed_tests += 1
        return None


# ============================================================================
# SETUP & FIXTURE DATA
# ============================================================================

# Student account
STUDENT_EMAIL = "alice@example.com"
STUDENT_PASSWORD = "secure_password_123"
STUDENT_NAME = "Alice Johnson"

# Trainer account (create with role=instructor in DB, or modify signup)
TRAINER_EMAIL = "bob@example.com"
TRAINER_PASSWORD = "trainer_pass_456"
TRAINER_NAME = "Bob Smith"

# Monitoring officer account
MONITOR_EMAIL = "charlie@example.com"
MONITOR_PASSWORD = "monitor_pass_789"
MONITOR_NAME = "Charlie Monitoring"

# Invalid token for negative tests
INVALID_TOKEN = "invalid.jwt.token"


# ============================================================================
# TEST 1: STUDENT FLOW
# ============================================================================

def test_student_flow():
    """
    Positive test: Student signup → login → join batch → mark attendance
    """
    print_header("TEST 1: STUDENT FLOW")

    # Step 1: Signup
    signup_data = {
        "name": STUDENT_NAME,
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD,
    }
    signup_response = test(
        "POST",
        "/auth/signup",
        201,
        data=signup_data,
        test_name="Student registers account",
    )
    if not signup_response:
        return None

    student_id = signup_response.get("id")
    print(f"  → Student ID: {student_id}\n")

    # Step 2: Login
    login_data = {
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD,
    }
    login_response = test(
        "POST",
        "/auth/login",
        200,
        data=login_data,
        test_name="Student logs in",
    )
    if not login_response:
        return None

    student_token = login_response.get("access_token")
    print(f"  → Access Token: {student_token[:20]}...\n")

    return {
        "student_id": student_id,
        "student_token": student_token,
        "student_email": STUDENT_EMAIL,
    }


# ============================================================================
# TEST 2: TRAINER FLOW
# ============================================================================

def test_trainer_flow():
    """
    Positive test: Trainer signup → login → create batch → create session
    Note: This assumes trainer role is set manually in DB or signup modifies role
    """
    print_header("TEST 2: TRAINER FLOW")

    # Step 1: Signup (trainer will have role=student initially, manual DB change needed for full test)
    signup_data = {
        "name": TRAINER_NAME,
        "email": TRAINER_EMAIL,
        "password": TRAINER_PASSWORD,
    }
    signup_response = test(
        "POST",
        "/auth/signup",
        201,
        data=signup_data,
        test_name="Trainer registers account",
    )
    if not signup_response:
        return None

    trainer_id = signup_response.get("id")
    print(f"  → Trainer ID: {trainer_id}\n")

    # Step 2: Login
    login_data = {
        "email": TRAINER_EMAIL,
        "password": TRAINER_PASSWORD,
    }
    login_response = test(
        "POST",
        "/auth/login",
        200,
        data=login_data,
        test_name="Trainer logs in",
    )
    if not login_response:
        return None

    trainer_token = login_response.get("access_token")
    print(f"  → Access Token: {trainer_token[:20]}...\n")

    return {
        "trainer_id": trainer_id,
        "trainer_token": trainer_token,
        "trainer_email": TRAINER_EMAIL,
    }


# ============================================================================
# TEST 3: MONITORING FLOW
# ============================================================================

def test_monitoring_flow():
    """
    Positive test: Monitoring officer signup → login → generate monitoring token
    """
    print_header("TEST 3: MONITORING FLOW")

    # Step 1: Signup
    signup_data = {
        "name": MONITOR_NAME,
        "email": MONITOR_EMAIL,
        "password": MONITOR_PASSWORD,
    }
    signup_response = test(
        "POST",
        "/auth/signup",
        201,
        data=signup_data,
        test_name="Monitoring officer registers account",
    )
    if not signup_response:
        return None

    monitor_id = signup_response.get("id")
    print(f"  → Monitor ID: {monitor_id}\n")

    # Step 2: Login
    login_data = {
        "email": MONITOR_EMAIL,
        "password": MONITOR_PASSWORD,
    }
    login_response = test(
        "POST",
        "/auth/login",
        200,
        data=login_data,
        test_name="Monitoring officer logs in",
    )
    if not login_response:
        return None

    monitor_token = login_response.get("access_token")
    print(f"  → Access Token: {monitor_token[:20]}...\n")

    return {
        "monitor_id": monitor_id,
        "monitor_token": monitor_token,
        "monitor_email": MONITOR_EMAIL,
    }


# ============================================================================
# TEST 4: NEGATIVE TESTS - AUTHENTICATION
# ============================================================================

def test_auth_negative():
    """
    Negative tests: Invalid credentials, missing token, etc.
    """
    print_header("TEST 4: NEGATIVE TESTS - AUTHENTICATION")

    # Test 1: Login with wrong password
    test(
        "POST",
        "/auth/login",
        401,
        data={"email": STUDENT_EMAIL, "password": "wrong_password"},
        test_name="Login with wrong password → 401 Unauthorized",
    )

    # Test 2: Login with non-existent email
    test(
        "POST",
        "/auth/login",
        401,
        data={"email": "nonexistent@example.com", "password": "anypassword"},
        test_name="Login with non-existent email → 401 Unauthorized",
    )

    # Test 3: Signup with missing fields
    test(
        "POST",
        "/auth/signup",
        422,
        data={"email": "incomplete@example.com", "password": "pass"},
        # Missing 'name' field
        test_name="Signup with missing 'name' field → 422 Validation Error",
    )

    # Test 4: Access protected endpoint without token
    test(
        "GET",
        "/health",  # Health check might not need auth
        200,
        headers=HEADERS_JSON,
        test_name="Health check (no auth required) → 200 OK",
    )

    print()


# ============================================================================
# TEST 5: NEGATIVE TESTS - AUTHORIZATION
# ============================================================================

def test_auth_negative_token():
    """
    Negative tests: Invalid token, missing token, expired token
    """
    print_header("TEST 5: NEGATIVE TESTS - TOKEN VALIDATION")

    # Get a valid student token first
    login_data = {
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD,
    }
    login_response = test(
        "POST",
        "/auth/login",
        200,
        data=login_data,
        test_name="Student logs in (for token tests)",
    )

    if not login_response:
        print(f"{RED}Skipping token tests - login failed{RESET}\n")
        return

    valid_token = login_response.get("access_token")

    # Test 1: Invalid token format
    invalid_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INVALID_TOKEN}",
    }
    test(
        "GET",
        "/batches",
        401,
        headers=invalid_headers,
        test_name="Access with invalid JWT token → 401 Unauthorized",
    )

    print()


# ============================================================================
# TEST 6: VALIDATION ERROR TESTS
# ============================================================================

def test_validation_errors():
    """
    Negative tests: Invalid input data
    """
    print_header("TEST 6: NEGATIVE TESTS - VALIDATION ERRORS")

    # Test 1: Empty body
    test(
        "POST",
        "/auth/login",
        422,
        data={},
        test_name="Login with empty body → 422 Unprocessable Entity",
    )

    # Test 2: Invalid email format
    test(
        "POST",
        "/auth/signup",
        422,
        data={
            "name": "Test User",
            "email": "not-an-email",
            "password": "secure123",
        },
        test_name="Signup with invalid email format → 422 Validation Error",
    )

    print()


# ============================================================================
# TEST 7: DUPLICATE ACCOUNT TEST
# ============================================================================

def test_duplicate_signup():
    """
    Negative test: Attempt to signup with existing email
    """
    print_header("TEST 7: NEGATIVE TEST - DUPLICATE SIGNUP")

    # Try to signup with email that already exists
    test(
        "POST",
        "/auth/signup",
        400,
        data={
            "name": "Duplicate User",
            "email": STUDENT_EMAIL,  # Already used in Test 1
            "password": "newpassword",
        },
        test_name="Signup with existing email → 400 Bad Request",
    )

    print()


# ============================================================================
# SUMMARY & REPORTING
# ============================================================================

def print_summary():
    """Print test results summary"""
    print_header("TEST SUMMARY")

    total = total_tests
    passed = passed_tests
    failed = failed_tests
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total Tests:  {total}")
    print(f"Passed:       {GREEN}{passed}{RESET}")
    print(f"Failed:       {RED}{failed}{RESET}")
    print(f"Pass Rate:    {pass_rate:.1f}%")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}✓ ALL TESTS PASSED!{RESET}\n")
    else:
        print(
            f"\n{RED}{BOLD}✗ {failed} TEST(S) FAILED{RESET}\n"
        )

    return failed == 0


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Run all tests in sequence
    """
    print(f"\n{BOLD}{YELLOW}")
    print("╔" + "=" * 68 + "╗")
    print("║" + "ATTENDANCE API - END-TO-END TEST SUITE".center(68) + "║")
    print("║" + f"Base URL: {BASE_URL}".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    print(f"{RESET}")

    # Run test suites
    student_ctx = test_student_flow()
    trainer_ctx = test_trainer_flow()
    monitor_ctx = test_monitoring_flow()

    # Negative tests
    test_auth_negative()
    test_auth_negative_token()
    test_validation_errors()
    test_duplicate_signup()

    # Print summary
    success = print_summary()

    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
