import os
import secrets
import subprocess
import tempfile

from integrity_monitor.integrity_monitor import hash_file, load_measured_files

# TCTI points to the Unix domain socket shared with c2 (swtpm)
TCTI         = "swtpm:path=/tmp/swtpm.sock"
PCR_REGISTER = "16"        # application-use PCR, resettable
AK_HANDLE    = "0x81010001"  # persisted Attestation Key handle in swtpm


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
    )


def extend_measurements() -> bool:
    """
    Hashes every measured file and extends the hash into PCR_REGISTER.
    Returns True if all extensions succeed.
    """
    _run(["tpm2_pcrreset", PCR_REGISTER])  # clean slate for this attestation

    files = load_measured_files()
    for file_path in files:
        file_hash = hash_file(file_path)
        if file_hash is None:
            return False
        result = _run([
            "tpm2_pcrextend",
            f"{PCR_REGISTER}:sha256={file_hash}"
        ])
        if result.returncode != 0:
            return False

    return True


def generate_nonce() -> str:
    return secrets.token_hex(32)


def request_quote() -> dict | None:
    """
    Extends PCRs, generates a nonce, and requests a signed TPM Quote.
    Returns a dict containing the quote file paths and nonce, or None on failure.
    """
    if not extend_measurements():
        return None

    nonce = generate_nonce()
    nonce_file = tempfile.mktemp(suffix=".nonce")
    quote_msg  = tempfile.mktemp(suffix=".msg")
    quote_sig  = tempfile.mktemp(suffix=".sig")
    pcrs_out   = tempfile.mktemp(suffix=".pcrs")

    with open(nonce_file, "w") as f:
        f.write(nonce)

    result = _run([
        "tpm2_quote",
        "-c", AK_HANDLE,
        "-l", f"sha256:{PCR_REGISTER}",
        "-q", nonce,
        "-m", quote_msg,
        "-s", quote_sig,
        "-o", pcrs_out,
        "-g", "sha256"
    ])

    if result.returncode != 0:
        return None

    return {
        "nonce":     nonce,
        "quote_msg": quote_msg,
        "quote_sig": quote_sig,
        "pcrs_out":  pcrs_out,
        "pcr":       PCR_REGISTER,
        "ak_handle": AK_HANDLE,
    }

