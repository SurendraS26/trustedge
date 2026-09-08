#!/usr/bin/env python3

import subprocess
import os

def test_tpm():
    print("[TEST] Checking TPM connectivity...")

    # Set TCTI for swtpm
    os.environ["TPM2TOOLS_TCTI"] = "swtpm:host=trustedge-c2,port=2321"

    # Test tpm2_pcrread
    try:
        result = subprocess.run(
            ["tpm2_pcrread"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("[PASS] TPM is responding")
            return True
        else:
            print(f"[FAIL] TPM error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] TPM test failed: {e}")
        return False

def test_pcr_extend():
    print("[TEST] Testing PCR extend...")
    try:
        result = subprocess.run(
            ["tpm2_pcrextend", "16:sha256=0000000000000000000000000000000000000000000000000000000000000000"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("[PASS] PCR extend successful")
            return True
        else:
            print(f"[FAIL] PCR extend failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] PCR extend error: {e}")
        return False

def test_quote():
    print("[TEST] Testing TPM quote...")
    try:
        result = subprocess.run(
            ["tpm2_quote", "-c", "0x81000001", "-l", "sha256:16", "-q", "1234", "-m", "/tmp/quote.bin", "-s", "/tmp/sig.bin"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("[PASS] TPM quote successful")
            return True
        else:
            print(f"[FAIL] Quote failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[FAIL] Quote error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TrustEdge — TPM Test Suite")
    print("=" * 50)

    tpm_ok = test_tpm()
    if not tpm_ok:
        print("\n[ERROR] TPM not responding. Make sure c2 container is running.")
        exit(1)

    test_pcr_extend()
    test_quote()

    print("\n[✓] TPM tests completed.")
