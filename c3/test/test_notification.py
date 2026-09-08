#!/usr/bin/env python3

import subprocess
import os

def test_zenity():
    print("[TEST] Testing Zenity notification...")

    try:
        result = subprocess.run(
            [
                "zenity",
                "--warning",
                "--title=TrustEdge Test",
                "--text=This is a test notification from TrustEdge!",
                "--width=400"
            ],
            timeout=10
        )
        if result.returncode == 0:
            print("[PASS] Zenity notification displayed")
            return True
        else:
            print("[FAIL] Zenity closed with error")
            return False
    except FileNotFoundError:
        print("[FAIL] Zenity not installed. Run: sudo pacman -S zenity")
        return False
    except subprocess.TimeoutExpired:
        print("[FAIL] Zenity timeout")
        return False
    except Exception as e:
        print(f"[FAIL] Zenity error: {e}")
        return False

def test_question():
    print("[TEST] Testing Zenity question dialog...")

    try:
        result = subprocess.run(
            [
                "zenity",
                "--question",
                "--title=TrustEdge Test",
                "--text=Do you want to allow this action?",
                "--ok-label=ALLOW",
                "--cancel-label=BLOCK",
                "--timeout=10"
            ],
            timeout=15
        )
        if result.returncode == 0:
            print("[PASS] User selected ALLOW")
            return True
        else:
            print("[PASS] User selected BLOCK or timeout")
            return True
    except Exception as e:
        print(f"[FAIL] Question error: {e}")
        return False

def test_info():
    print("[TEST] Testing Zenity info dialog...")

    try:
        result = subprocess.run(
            [
                "zenity",
                "--info",
                "--title=TrustEdge Test",
                "--text=TrustEdge is running successfully!",
                "--width=400"
            ],
            timeout=10
        )
        if result.returncode == 0:
            print("[PASS] Info dialog displayed")
            return True
        else:
            print("[FAIL] Info dialog failed")
            return False
    except Exception as e:
        print(f"[FAIL] Info error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TrustEdge — Notification Test Suite")
    print("=" * 50)

    all_passed = True

    if not test_zenity():
        all_passed = False

    if not test_question():
        all_passed = False

    if not test_info():
        all_passed = False

    print("=" * 50)
    if all_passed:
        print("[✓] All notification tests passed.")
    else:
        print("[✗] Some notification tests failed.")
