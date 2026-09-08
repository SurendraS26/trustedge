import subprocess
from framework.baseline_store import get_baseline

AK_PUB = "/app/framework/ak_pub.pem"


def _verify_quote_signature(evidence: dict) -> bool:
    try:
        subprocess.run(
            [
                "tpm2_checkquote",
                "-u", AK_PUB,
                "-m", evidence["quote_path"],
                "-s", evidence["sig_path"],
                "-f", evidence["pcr_path"],
                "-q", evidence["nonce"],
            ],
            capture_output=True, text=True, check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _compare_to_baseline(fresh_measurements: dict) -> tuple[bool, str]:
    baseline = get_baseline()
    if not baseline:
        return False, "baseline not initialized"

    for path, digest in fresh_measurements.items():
        expected = baseline.get(path)
        if expected is None:
            return False, f"file not in baseline: {path}"
        if digest != expected:
            return False, f"measurement mismatch (tampering suspected): {path}"
    return True, "ok"


def verify(evidence: dict, fresh_measurements: dict) -> dict:
    if not _verify_quote_signature(evidence):
        return {"decision": "deny", "reason": "invalid TPM quote signature or stale/mismatched nonce"}

    baseline_ok, reason = _compare_to_baseline(fresh_measurements)
    if not baseline_ok:
        return {"decision": "deny", "reason": reason}

    return {"decision": "allow", "reason": "quote verified, measurements match baseline"}
