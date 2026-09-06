import hashlib
import json
import os
import secrets
import subprocess
import tempfile

TCTI      = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=c2,port=2321")
PCR       = os.environ.get("TPM_PCR", "16")
AK_HANDLE = os.environ.get("AK_HANDLE", "0x81010001")
AK_PUB    = os.environ.get("AK_PUB_PATH", "/app/tpm_keys/ak.pub")
CFG       = "/app/integrity_monitor/measured_files.json"


def tpm(cmd):
    return subprocess.run(
        cmd, capture_output=True, text=True,
        env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
    )


def hash_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def request_quote():
    # Reset PCR
    if tpm(["tpm2_pcrreset", PCR]).returncode != 0:
        return None

    # Extend each file hash into PCR
    with open(CFG) as f:
        files = json.load(f).get("files", [])

    for path in files:
        h = hash_file(path)
        if h is None:
            return None
        if tpm(["tpm2_pcrextend", f"{PCR}:sha256={h}"]).returncode != 0:
            return None

    # Generate quote
    nonce = secrets.token_hex(32)
    msg   = tempfile.mktemp(suffix=".msg")
    sig   = tempfile.mktemp(suffix=".sig")
    pcrs  = tempfile.mktemp(suffix=".pcrs")

    r = tpm([
        "tpm2_quote",
        "-c", AK_HANDLE,
        "-l", f"sha256:{PCR}",
        "-q", nonce,
        "-m", msg,
        "-s", sig,
        "-o", pcrs,
        "-g", "sha256"
    ])

    if r.returncode != 0:
        return None

    return {"nonce": nonce, "msg": msg, "sig": sig, "pcrs": pcrs, "pcr": PCR, "ak_pub": AK_PUB}
