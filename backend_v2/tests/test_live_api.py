#!/usr/bin/env python3
"""
Live API smoke tests for production/staging server.
These tests verify the API is responding correctly without modifying data.

Usage:
    python test_live_api.py                  # Test localhost:8000
    python test_live_api.py http://server    # Test specific server
"""
import sys
import requests
from datetime import datetime


def log(status, message):
    """Log test result."""
    icon = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "WARN"
    print(f"  [{icon}] {message}")
    return status == "PASS"


def run_tests(base_url):
    """Run all smoke tests."""
    print(f"\n{'='*60}")
    print(f"  HEALTHY API SMOKE TESTS")
    print(f"  Server: {base_url}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0

    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        r = requests.get(f"{base_url}/", timeout=10)
        if r.status_code == 200:
            passed += 1 if log("PASS", f"GET / returned 200") else 0
        else:
            failed += 1
            log("FAIL", f"GET / returned {r.status_code}")
    except Exception as e:
        failed += 1
        log("FAIL", f"GET / failed: {e}")

    # Test 2: Auth endpoint exists
    print("\n2. Testing auth endpoint...")
    try:
        r = requests.post(f"{base_url}/auth/token", data={
            "username": "test@nonexistent.com",
            "password": "wrongpassword"
        }, timeout=10)
        if r.status_code == 401:
            passed += 1 if log("PASS", "Auth returns 401 for invalid credentials") else 0
        else:
            failed += 1
            log("FAIL", f"Auth returned {r.status_code}, expected 401")
    except Exception as e:
        failed += 1
        log("FAIL", f"Auth endpoint failed: {e}")

    # Test 3: Protected endpoint without auth
    print("\n3. Testing protected endpoints require auth...")
    for endpoint in ["/dashboard/stats", "/documents", "/users/me"]:
        try:
            r = requests.get(f"{base_url}{endpoint}", timeout=10)
            if r.status_code == 401:
                passed += 1 if log("PASS", f"GET {endpoint} returns 401 without auth") else 0
            else:
                failed += 1
                log("FAIL", f"GET {endpoint} returned {r.status_code}, expected 401")
        except Exception as e:
            failed += 1
            log("FAIL", f"GET {endpoint} failed: {e}")

    # Test 4: CORS headers
    print("\n4. Testing CORS headers...")
    try:
        r = requests.options(f"{base_url}/auth/token", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }, timeout=10)
        if "access-control-allow-origin" in r.headers:
            passed += 1 if log("PASS", "CORS headers present") else 0
        else:
            # CORS might not be configured for OPTIONS
            log("WARN", "CORS headers not in OPTIONS response (may be OK)")
    except Exception as e:
        log("WARN", f"CORS check failed: {e}")

    # Test 5: Invalid JSON handling
    print("\n5. Testing input validation...")
    try:
        r = requests.post(f"{base_url}/auth/register",
            json={"email": "invalid", "password": ""},
            timeout=10)
        if r.status_code in [400, 422]:
            passed += 1 if log("PASS", "Invalid input returns 400/422") else 0
        else:
            failed += 1
            log("FAIL", f"Invalid input returned {r.status_code}")
    except Exception as e:
        failed += 1
        log("FAIL", f"Input validation test failed: {e}")

    # Test 6: Health/admin endpoints (if available)
    print("\n6. Testing admin endpoints (should require auth)...")
    try:
        r = requests.get(f"{base_url}/admin/users", timeout=10)
        if r.status_code in [401, 403]:
            passed += 1 if log("PASS", "Admin endpoint protected") else 0
        else:
            log("WARN", f"Admin returned {r.status_code} (may need different auth)")
    except Exception as e:
        log("WARN", f"Admin check failed: {e}")

    # Summary
    print(f"\n{'='*60}")
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} tests passed")
    if failed == 0:
        print("  STATUS: ALL TESTS PASSED")
    else:
        print(f"  STATUS: {failed} TESTS FAILED")
    print(f"{'='*60}\n")

    return failed == 0


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = run_tests(base_url.rstrip("/"))
    sys.exit(0 if success else 1)
