"""
TrustEdge — Verifier
Final trust decision engine.
Checks:
  1. TPM Quote signature (tpm2_checkquote)
  2. Nonce match (anti-replay — handled inside tpm2_checkquote via -q flag)
  3. Live PCR value vs baseline PCR value

Issues Allow or Deny. Fails closed on any error.
"""

import logging
import os
import subprocess

log = logging.getLogger("trustedge.verifier")

TCTI = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=trustedge-c2,port=2321")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "TPM2TOOLS_TCTI": TCTI}
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _cleanup(quote_data: dict) -> None:
    for key in ["quote_msg", "quote_sig", "pcrs_out"]:
        try:
            os.remove(quote_data[key])
        except (FileNotFoundError, KeyError):
            pass


def _parse_pcr_value(tpm2_output: str, pcr_index: str) -> str | None:
    """
    Parse PCR value from tpm2_pcrread output.
    Output format:
      sha256:
        16: 0x9851312028...
    Field 1 = "16:", Field 2 = "0x9851..."
    Always returns lowercase without 0x prefix.
    """
    for line in tpm2_output.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{pcr_index}:"):
            parts = stripped.split()
            if len(parts) >= 2:
                return parts[1].lower().lstrip("0x")
    return None


def verify_quote(quote_data: dict) -> tuple[bool, str]:
    """
    Returns (True, "ok") if all checks pass.
    Returns (False, reason) on any failure.
    Always cleans up temp files before returning.
    """
    from baseline_store.baseline_store import get_baseline_pcr

    ak_pub = quote_data.get("ak_pub")
    if not ak_pub or not os.path.exists(ak_pub):
        _cleanup(quote_data)
        return False, f"AK public key not found at {ak_pub}"

    # ── Check 1: Quote signature + nonce ─────────────────────────────────
    r = _run([
        "tpm2_checkquote",
        "-u", ak_pub,
        "-m", quote_data["quote_msg"],
        "-s", quote_data["quote_sig"],
        "-f", quote_data["pcrs_out"],
        "-g", "sha256",
        "-l", f"sha256:{quote_data['pcr']}",
        "-q", quote_data["nonce"]
    ])

    if r.returncode != 0:
        _cleanup(quote_data)
        return False, f"quote signature/nonce check failed: {r.stderr.strip()}"

    log.info("Quote signature and nonce verified")

    # ── Check 2: Live PCR vs baseline ────────────────────────────────────
    baseline_pcr = get_baseline_pcr(quote_data["pcr"])
    if baseline_pcr is None:
        _cleanup(quote_data)
        return False, f"no baseline PCR value for PCR {quote_data['pcr']} — run init_baseline.py first"

    r2 = _run(["tpm2_pcrread", f"sha256:{quote_data['pcr']}"])
    if r2.returncode != 0:
        _cleanup(quote_data)
        return False, f"tpm2_pcrread failed: {r2.stderr.strip()}"

    current_pcr = _parse_pcr_value(r2.stdout, quote_data["pcr"])
    if current_pcr is None:
        _cleanup(quote_data)
        return False, "could not parse PCR value from tpm2_pcrread output"

    # Normalise both sides — lowercase, strip leading zeros/0x
    current_norm  = current_pcr.lower().lstrip("0x").lstrip("0") or "0"
    baseline_norm = baseline_pcr.lower().lstrip("0x").lstrip("0") or "0"

    if current_norm != baseline_norm:
        _cleanup(quote_data)
        return False, f"PCR {quote_data['pcr']} mismatch — current={current_pcr}, baseline={baseline_pcr}"

    log.info(f"PCR {quote_data['pcr']} matches baseline")
    _cleanup(quote_data)
    return True, "ok"
