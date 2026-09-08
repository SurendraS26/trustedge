#!/usr/bin/env python3

import os
import subprocess
import hashlib

from modules import baseline_store

# TPM TCTI for c2 container (also set via TPM2TOOLS_TCTI env var in docker-compose)
TPM_TCTI = "swtpm:host=trustedge-c2,port=2321"

# PCR used to record a tamper-evident measurement log of everything executed
MEASUREMENT_PCR = 16


def get_file_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def get_tpm_hash(filepath):
    """Look up the trusted baseline hash for this target.

    A hardware/software TPM doesn't store per-file hashes on its own; instead
    we keep a baseline store of trusted hashes and use the TPM's PCRs to keep
    a tamper-evident measurement log of every executable that has been
    verified (see extend_measurement_pcr below).
    """
    return baseline_store.get_baseline(filepath)


def extend_measurement_pcr(file_hash):
    """Best-effort extend of the TPM measurement PCR with the verified hash.

    This is not fatal if the TPM is unreachable - it's an additional
    tamper-evidence layer on top of the baseline_store check, not the primary
    gate, so verification results should not depend on it succeeding.
    """
    try:
        env = os.environ.copy()
        env.setdefault("TPM2TOOLS_TCTI", TPM_TCTI)
        subprocess.run(
            ["tpm2_pcrextend", f"{MEASUREMENT_PCR}:sha256={file_hash}"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
    except Exception as e:
        print(f"[VERIFIER] TPM PCR extend skipped: {e}")


def verify(action, target):
    # Integrity verification only makes sense for things we're about to run.
    if action != "execute":
        return {"allowed": True, "reason": "Integrity verification not required for this action"}

    if not os.path.exists(target):
        return {"allowed": False, "reason": f"Target '{target}' does not exist"}

    current_hash = get_file_hash(target)
    if not current_hash:
        return {"allowed": False, "reason": f"Failed to hash target '{target}'"}

    baseline_hash = get_tpm_hash(target)

    if baseline_hash is None:
        # Trust-on-first-use: no baseline recorded yet for this target, so
        # establish one now and log the measurement into the TPM.
        baseline_store.store_baseline(target, current_hash)
        extend_measurement_pcr(current_hash)
        print(f"[VERIFIER] No baseline for {target}; new baseline established")
        return {"allowed": True, "reason": "No prior baseline; new baseline established (TOFU)"}

    if current_hash == baseline_hash:
        extend_measurement_pcr(current_hash)
        return {"allowed": True, "reason": "File integrity verified against baseline"}

    return {"allowed": False, "reason": f"Hash mismatch: {current_hash[:16]} != {baseline_hash[:16]}"}
