#!/usr/bin/env python3

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    print("[TEST] Testing health endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            print("[PASS] Health check passed")
            return True
        else:
            print(f"[FAIL] Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False

def test_evaluate():
    print("[TEST] Testing evaluate endpoint...")
    payload = {
        "action": "execute",
        "target": "/bin/ls",
        "reasoning": "Testing API"
    }
    try:
        resp = requests.post(f"{BASE_URL}/evaluate", json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[PASS] Evaluate response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"[FAIL] Evaluate failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Evaluate error: {e}")
        return False

def test_logs():
    print("[TEST] Testing logs endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/logs", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[PASS] Logs: {len(data.get('logs', []))} entries")
            return True
        else:
            print(f"[FAIL] Logs failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Logs error: {e}")
        return False

def test_root():
    print("[TEST] Testing root endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        if resp.status_code == 200:
            print(f"[PASS] Root: {resp.json().get('message')}")
            return True
        else:
            print(f"[FAIL] Root failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Root error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TrustEdge — API Test Suite")
    print("=" * 50)

    all_passed = True

    if not test_root():
        all_passed = False

    if not test_health():
        all_passed = False

    if not test_evaluate():
        all_passed = False

    if not test_logs():
        all_passed = False

    print("=" * 50)
    if all_passed:
        print("[✓] All API tests passed.")
    else:
        print("[✗] Some API tests failed.")
        sys.exit(1)
