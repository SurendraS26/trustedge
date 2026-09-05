"""
TrustEdge — Attestation Manager
Bridges c3 with swtpm (c2) via TCP or Unix socket.
1. Resets PCR 16
2. Extends all measured file hashes into PCR 16
3. Generates a nonce
4. Requests a signed TPM Quote
5. Returns quote data dict to the Verifier

TCTI is read from the environment variable TPM2TOOLS_TCTI.
Default: swtpm:host=trustedge-c2,port=2321 (Docker network TCP)
"""

import logging
import os
import secrets
import subprocess
import tempfile

from integrity_monitor.integrity_monitor import hash_file, load_measured_files

log = logging.getLogger("trustedge.attestation")

# Configurable via environment — supports both TCP and Unix socket
TCTI         = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=trustedge-c2,port=2321")
PCR_REGISTER = os.environ.get("TPM_PCR", "16")
AK_HANDLE    = os.environ.get("AK_HANDLE", "0x81010001")
AK_PUB_PATH  = os.environ.get("AK_PUB_PATH", "/app/tpm_keys/ak.pub")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "TPM2TOOLS_TCTI": TCTI}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        log.debug(f"Command {cmd[0]} stderr: {result.stderr.strip()}")
    return result


def extend_measurements() -> bool:
    """Reset PCR 16 and extend all measured file hashes into it."""

    # Reset
    r = _run(["tpm2_pcrreset", PCR_REGISTER])
    if r.returncode != 0:
        log.error(f"tpm2_pcrreset failed: {r.stderr.strip()}")
        return False

    # Extend each file hash
    try:
        files = load_measured_files()
    except Exception as e:
        log.error(f"Cannot load measured files: {e}")
        return False

    for file_path in files:
        file_hash = hash_file(file_path)
        if file_hash is None:
            log.error(f"Cannot hash {file_path} — aborting extend")
            return False

        r = _run(["tpm2_pcrextend", f"{PCR_REGISTER}:sha256={file_hash}"])
        if r.returncode != 0:
            log.error(f"tpm2_pcrextend failed for {file_path}: {r.stderr.strip()}")
            return False

    log.info(f"All hashes extended into PCR {PCR_REGISTER}")
    return True


def request_quote() -> dict | None:
    """
    Extends PCRs, generates a nonce, requests a signed TPM Quote.
    Returns a dict of file paths and nonce for the Verifier, or None on failure.
    """
    if not extend_measurements():
        return None

    nonce     = secrets.token_hex(32)
    quote_msg = tempfile.mktemp(prefix="trustedge_", suffix=".msg")
    quote_sig = tempfile.mktemp(prefix="trustedge_", suffix=".sig")
    pcrs_out  = tempfile.mktemp(prefix="trustedge_", suffix=".pcrs")

    r = _run([
        "tpm2_quote",
        "-c", AK_HANDLE,
        "-l", f"sha256:{PCR_REGISTER}",
        "-q", nonce,
        "-m", quote_msg,
        "-s", quote_sig,
        "-o", pcrs_out,
        "-g", "sha256"
    ])

    if r.returncode != 0:
        log.error(f"tpm2_quote failed: {r.stderr.strip()}")
        # Clean up temp files
        for f in [quote_msg, quote_sig, pcrs_out]:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
        return None

    log.info("TPM Quote generated successfully")
    return {
        "nonce":      nonce,
        "quote_msg":  quote_msg,
        "quote_sig":  quote_sig,
        "pcrs_out":   pcrs_out,
        "pcr":        PCR_REGISTER,
        "ak_handle":  AK_HANDLE,
        "ak_pub":     AK_PUB_PATH,
    }
