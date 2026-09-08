"""
Verify the swtpm in c2 is running and responsive, and that the persisted
Attestation Key from scripts/setup_tpm.sh is readable.

Requires TPM2TOOLS_TCTI (or the TCTI env var) to point at the running
swtpm, e.g. swtpm:host=c2-tpm,port=2321. Run with:
    pytest tests/test_tpm.py
or directly:
    python tests/test_tpm.py
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TCTI = os.environ.get("TCTI") or os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=c2-tpm,port=2321")
os.environ["TPM2TOOLS_TCTI"] = TCTI

AK_HANDLE = "0x81010001"


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def test_tpm_startup_succeeds():
    result = _run(["tpm2_startup", "-c"])
    # A TPM that is already started returns a non-zero code with a
    # "already started" style message; either outcome proves it is live.
    assert result.returncode == 0 or "already" in (result.stderr or "").lower(), (
        f"TPM did not respond to startup: {result.stderr}"
    )


def test_pcr_read_succeeds():
    result = _run(["tpm2_pcrread", "sha256:16"])
    assert result.returncode == 0, f"tpm2_pcrread failed: {result.stderr}"
    assert "16" in result.stdout


def test_attestation_key_is_persisted():
    result = _run(["tpm2_readpublic", "-c", AK_HANDLE])
    assert result.returncode == 0, (
        f"attestation key not found at {AK_HANDLE}, run scripts/setup_tpm.sh first: {result.stderr}"
    )


if __name__ == "__main__":
    test_tpm_startup_succeeds()
    test_pcr_read_succeeds()
    test_attestation_key_is_persisted()
    print("test_tpm: all tests passed")
