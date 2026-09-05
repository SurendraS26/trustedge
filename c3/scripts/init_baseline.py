"""
TrustEdge — Baseline Initialisation
Run once on a known-clean system before starting the framework.
Records SHA-256 hashes of all measured files and the current PCR 16
value into the baseline store.

Usage:
    python scripts/init_baseline.py
"""

import json
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("trustedge.init")

# Add /app to path so we can import baseline_store
sys.path.insert(0, "/app")

from baseline_store.baseline_store import initialise_baseline, init_db

TCTI              = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=trustedge-c2,port=2321")
PCR_REGISTER      = os.environ.get("TPM_PCR", "16")
MEASURED_FILES_CFG = "/app/integrity_monitor/measured_files.json"


def get_pcr_value(pcr_index: str) -> str | None:
    """Read current PCR value directly from swtpm."""
    result = subprocess.run(
        ["tpm2_pcrread", f"sha256:{pcr_index}"],
        capture_output=True,
        text=True,
        env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
    )
    if result.returncode != 0:
        log.error(f"tpm2_pcrread failed: {result.stderr.strip()}")
        return None

    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{pcr_index}:"):
            parts = stripped.split()
            if len(parts) >= 2:
                return parts[1].lower()

    return None


def load_measured_files() -> list[str]:
    with open(MEASURED_FILES_CFG) as f:
        return json.load(f).get("files", [])


def main():
    log.info("=== TrustEdge Baseline Initialisation ===")
    log.info(f"TCTI: {TCTI}")
    log.info(f"PCR:  {PCR_REGISTER}")

    # Ensure DB schema exists
    init_db()

    # Load file list
    try:
        file_paths = load_measured_files()
    except Exception as e:
        log.error(f"Cannot load measured files config: {e}")
        sys.exit(1)

    log.info(f"Files to baseline: {len(file_paths)}")

    # Get current PCR value as baseline
    # (PCR 16 should be reset to zero before running this — it will be zero
    #  if swtpm was freshly started or if you ran tpm2_pcrreset 16 first)
    pcr_value = get_pcr_value(PCR_REGISTER)
    if pcr_value is None:
        log.error("Cannot read PCR value from swtpm — is c2 running?")
        sys.exit(1)

    log.info(f"PCR {PCR_REGISTER} baseline value: {pcr_value}")

    # Write everything to the baseline store
    initialise_baseline(
        file_paths=file_paths,
        pcr_values={PCR_REGISTER: pcr_value}
    )

    log.info("=== Baseline initialisation complete ===")


if __name__ == "__main__":
    main()
