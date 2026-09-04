import os
import subprocess
import tempfile

from baseline_store.baseline_store import get_ak_pubkey_path

TCTI = "swtpm:path=/tmp/swtpm.sock"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
    )


def verify_quote(quote_data: dict) -> tuple[bool, str]:
    """
    Verifies the signed TPM Quote returned by the Attestation Manager.
    Returns (True, "ok") on success.
    Returns (False, reason) on any failure.
    """

    ak_pub = get_ak_pubkey_path()
    if ak_pub is None or not os.path.exists(ak_pub):
        return False, "AK public key not found in baseline store"

    # ── Check 1: Quote signature validation + nonce match ────────────────
    result = _run([
        "tpm2_checkquote",
        "-u", ak_pub,
        "-m", quote_data["quote_msg"],
        "-s", quote_data["quote_sig"],
        "-f", quote_data["pcrs_out"],
        "-g", "sha256",
        "-l", f"sha256:{quote_data['pcr']}",
        "-q", quote_data["nonce"]
    ])

    if result.returncode != 0:
        return False, f"quote signature or nonce check failed: {result.stderr.strip()}"

    # ── Check 2: PCR value against baseline ──────────────────────────────
    from baseline_store.baseline_store import get_baseline_pcr

    baseline_pcr = get_baseline_pcr(quote_data["pcr"])
    if baseline_pcr is None:
        return False, "no baseline PCR value recorded — run baseline initialisation first"

    current_pcr_result = _run([
        "tpm2_pcrread",
        f"sha256:{quote_data['pcr']}"
    ])

    if current_pcr_result.returncode != 0:
        return False, "failed to read current PCR value"

    # Parse the PCR value from tpm2_pcrread output
    current_pcr = None
    for line in current_pcr_result.stdout.splitlines():
        if f"{quote_data['pcr']}:" in line:
            parts = line.split()
            if len(parts) >= 2:
                current_pcr = parts[1].lower().lstrip("0x")

    if current_pcr is None:
        return False, "could not parse PCR value from tpm2_pcrread output"

    if current_pcr.lower() != baseline_pcr.lower():
        return False, f"PCR {quote_data['pcr']} mismatch: current={current_pcr}, baseline={baseline_pcr}"

    return True, "ok"

