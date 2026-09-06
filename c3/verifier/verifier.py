import os
import subprocess

from baseline_store.baseline_store import get_pcr

TCTI = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=c2,port=2321")


def tpm(cmd):
    return subprocess.run(
        cmd, capture_output=True, text=True,
        env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
    )


def cleanup(q):
    for key in ["msg", "sig", "pcrs"]:
        try:
            os.remove(q[key])
        except Exception:
            pass


def read_pcr(pcr):
    r = tpm(["tpm2_pcrread", f"sha256:{pcr}"])
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith(f"{pcr}:"):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1].lower().replace("0x", "")
    return None


def verify_quote(q):
    ak_pub = q.get("ak_pub")

    if not ak_pub or not os.path.exists(ak_pub):
        cleanup(q)
        return False, "AK public key not found"

    # Verify signature and nonce
    r = tpm([
        "tpm2_checkquote",
        "-u", ak_pub,
        "-m", q["msg"],
        "-s", q["sig"],
        "-f", q["pcrs"],
        "-g", "sha256",
        "-l", f"sha256:{q['pcr']}",
        "-q", q["nonce"]
    ])

    if r.returncode != 0:
        cleanup(q)
        return False, f"checkquote failed: {r.stderr.strip()}"

    # Compare PCR against baseline
    baseline = get_pcr(q["pcr"])
    if baseline is None:
        cleanup(q)
        return False, "no baseline PCR — run init_baseline.py first"

    current = read_pcr(q["pcr"])
    if current is None:
        cleanup(q)
        return False, "could not read PCR"

    if current.lstrip("0") != baseline.lstrip("0"):
        cleanup(q)
        return False, f"PCR mismatch"

    cleanup(q)
    return True, "ok"
