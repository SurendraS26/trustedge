"""
TrustEdge — TPM Connectivity Tests
Tests swtpm (c2) is reachable, PCR extend/read works, and quote generation works.
Run: python tests/test_tpm.py

Requires c2 (swtpm) running and TPM2TOOLS_TCTI set correctly.
"""

import os
import subprocess
import sys
import tempfile

TCTI = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=trustedge-c2,port=2321")
AK_HANDLE = os.environ.get("AK_HANDLE", "0x81010001")

PASS = "\033[1;32mPASS\033[0m"
FAIL = "\033[1;31mFAIL\033[0m"

passed = 0
failed = 0


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
    )


def check(desc: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        print(f"  [{PASS}] {desc}")
        passed += 1
    else:
        print(f"  [{FAIL}] {desc}")
        if detail:
            print(f"         {detail}")
        failed += 1


print(f"\n=== TPM Connectivity Tests ===")
print(f"    TCTI: {TCTI}\n")

# ── Test 1: startup ───────────────────────────────────────────────────────
r = run(["tpm2_startup", "-c"])
check("tpm2_startup succeeds", r.returncode == 0, r.stderr.strip())

# ── Test 2: PCR read ──────────────────────────────────────────────────────
r = run(["tpm2_pcrread", "sha256:16"])
check("tpm2_pcrread sha256:16 succeeds", r.returncode == 0, r.stderr.strip())
check("PCR output contains '16:'", "16:" in r.stdout)

# ── Test 3: PCR reset ─────────────────────────────────────────────────────
r = run(["tpm2_pcrreset", "16"])
check("tpm2_pcrreset 16 succeeds", r.returncode == 0, r.stderr.strip())

# Read after reset — should be all zeros
r = run(["tpm2_pcrread", "sha256:16"])
check("PCR 16 is zeroed after reset", "0000000000000000000000000000000000000000000000000000000000000000" in r.stdout)

# ── Test 4: PCR extend ────────────────────────────────────────────────────
test_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"  # sha256("hello")
r = run(["tpm2_pcrextend", f"16:sha256={test_hash}"])
check("tpm2_pcrextend succeeds", r.returncode == 0, r.stderr.strip())

r = run(["tpm2_pcrread", "sha256:16"])
check("PCR 16 changed after extend", "0000000000000000000000000000000000000000000000000000000000000000" not in r.stdout)

# ── Test 5: AK handle readable ───────────────────────────────────────────
r = run(["tpm2_readpublic", "-c", AK_HANDLE])
check(f"AK persisted at {AK_HANDLE}", r.returncode == 0,
      f"Run scripts/setup_tpm.sh first if this fails: {r.stderr.strip()}")

# ── Test 6: Quote generation ──────────────────────────────────────────────
nonce = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
quote_msg = tempfile.mktemp(suffix=".msg")
quote_sig = tempfile.mktemp(suffix=".sig")
pcrs_out  = tempfile.mktemp(suffix=".pcrs")

r = run([
    "tpm2_quote",
    "-c", AK_HANDLE,
    "-l", "sha256:16",
    "-q", nonce,
    "-m", quote_msg,
    "-s", quote_sig,
    "-o", pcrs_out,
    "-g", "sha256"
])
check("tpm2_quote succeeds", r.returncode == 0, r.stderr.strip())
check("quote message file created", os.path.exists(quote_msg))
check("quote signature file created", os.path.exists(quote_sig))

# ── Test 7: Quote verification ────────────────────────────────────────────
ak_pub = os.environ.get("AK_PUB_PATH", "/app/tpm_keys/ak.pub")
if os.path.exists(ak_pub):
    r = run([
        "tpm2_checkquote",
        "-u", ak_pub,
        "-m", quote_msg,
        "-s", quote_sig,
        "-f", pcrs_out,
        "-g", "sha256",
        "-l", "sha256:16",
        "-q", nonce
    ])
    check("tpm2_checkquote passes", r.returncode == 0, r.stderr.strip())
else:
    print(f"  [SKIP] tpm2_checkquote — AK public key not found at {ak_pub}")

# Cleanup
for f in [quote_msg, quote_sig, pcrs_out]:
    try:
        os.remove(f)
    except FileNotFoundError:
        pass

print(f"\nResults: {passed} passed, {failed} failed\n")
sys.exit(0 if failed == 0 else 1)
