import os
import secrets
import shutil
import subprocess
import tempfile

AK_HANDLE = "0x81010001"
PCR_INDEX = 16
PCR_BANK = "sha256"
DATA_DIR = os.path.dirname(os.environ.get("SQLITE_PATH", "/data/trustedge.db")) or "/data"
AK_PUB = os.path.join(DATA_DIR, "ak.pub")


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {result.stderr.strip()[-200:]}")
    return result.stdout


class Verifier:
    def attest(self, digest_hex: str) -> dict:
        if not os.path.exists(AK_PUB):
            return {"attested": False, "reason": "attestation key not provisioned"}

        tmpdir = tempfile.mkdtemp(prefix="quote-")
        msg = os.path.join(tmpdir, "quote.msg")
        sig = os.path.join(tmpdir, "quote.sig")
        pcrs = os.path.join(tmpdir, "pcrs.out")
        nonce = secrets.token_hex(16)

        try:
            _run(["tpm2_pcrextend", f"{PCR_INDEX}:{PCR_BANK}={digest_hex}"])
            _run(["tpm2_quote", "-c", AK_HANDLE, "-l", f"{PCR_BANK}:{PCR_INDEX}",
                  "-q", nonce, "-m", msg, "-s", sig, "-o", pcrs, "-g", PCR_BANK])
            _run(["tpm2_checkquote", "-u", AK_PUB, "-m", msg, "-s", sig,
                  "-f", pcrs, "-g", PCR_BANK, "-q", nonce])
            return {"attested": True, "reason": "quote verified"}
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            return {"attested": False, "reason": str(exc)}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
