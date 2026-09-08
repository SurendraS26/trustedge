#!/usr/bin/env python3

import os
import subprocess
import hashlib

# TPM TCTI for c2 container
TPM_TCTI = "swtpm:host=trustedge-c2,port=2321"

def get_file_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def get_tpm_hash(filepath):
    return None

def verify(target):
    if not os.path.exists(target):
        return {"allowed": False, "reason": f"Target '{target}' does not exist"}

    current_hash = get_file_hash(target)
    if not current_hash:
        return {"allowed": False, "reason": f"Failed to hash target '{target}'"}

    tpm_hash = get_tpm_hash(target)

    if tpm_hash is None:
        print(f"[VERIFIER] No TPM hash for {target}, skipping verification")
        return {"allowed": True, "reason": "TPM verification disabled"}

    if current_hash == tpm_hash:
        return {"allowed": True, "reason": "File integrity verified"}

    return {"allowed": False, "reason": f"Hash mismatch: {current_hash[:16]} != {tpm_hash[:16]}"}
