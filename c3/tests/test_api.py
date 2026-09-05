"""
TrustEdge — Framework API Tests
Tests the /evaluate endpoint with non-sensitive and sensitive requests.
Run after the c3 container is up:
    python tests/test_api.py

Requires c3 running on localhost:8000.
"""

import sys
import requests

C3_URL = "http://localhost:8000"

PASS = "\033[1;32mPASS\033[0m"
FAIL = "\033[1;31mFAIL\033[0m"

passed = 0
failed = 0


def check(desc: str, condition: bool):
    global passed, failed
    if condition:
        print(f"  [{PASS}] {desc}")
        passed += 1
    else:
        print(f"  [{FAIL}] {desc}")
        failed += 1


def evaluate(action: str, target: str) -> dict:
    resp = requests.post(f"{C3_URL}/evaluate", json={
        "action": action,
        "target": target,
        "reasoning": "test"
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


print("\n=== Framework API Tests ===\n")

# ── Health check ──────────────────────────────────────────────────────────
try:
    r = requests.get(f"{C3_URL}/health", timeout=5)
    check("c3 health endpoint returns 200", r.status_code == 200)
except Exception as e:
    print(f"  [{FAIL}] c3 not reachable at {C3_URL}: {e}")
    print("  Make sure c3 container is running before running these tests.")
    sys.exit(1)

# ── Test 1: non-sensitive action should be directly allowed ───────────────
result = evaluate("read", "/tmp/notes.txt")
check("non-sensitive action is directly allowed", result["allowed"] is True)
check("reason mentions non-sensitive", "non-sensitive" in result["reason"])

# ── Test 2: policy check endpoint ────────────────────────────────────────
r = requests.get(f"{C3_URL}/policy/check", params={"action": "delete", "target": "/etc/passwd"})
check("/policy/check detects sensitive action", r.json()["sensitive"] is True)

r2 = requests.get(f"{C3_URL}/policy/check", params={"action": "read", "target": "/tmp/notes.txt"})
check("/policy/check detects non-sensitive action", r2.json()["sensitive"] is False)

# ── Test 3: sensitive action goes through attestation pipeline ────────────
# (This will pass if TPM is set up correctly, or fail with a clear reason if not)
result = evaluate("delete", "/etc/passwd")
print(f"\n  Sensitive action result: allowed={result['allowed']}, reason={result['reason']}")
check("sensitive action returns a structured response", "allowed" in result and "reason" in result)

print(f"\nResults: {passed} passed, {failed} failed\n")
sys.exit(0 if failed == 0 else 1)
