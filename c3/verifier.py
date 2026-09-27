import os
import subprocess
import uuid

PCR_INDEX = "16"


class Verifier:
    def __init__(self):
        self.tcti = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=trustedge-c2,port=2321")
        os.environ["TPM2TOOLS_TCTI"] = self.tcti

    def _run(self, args):
        return subprocess.run(args, capture_output=True, text=True, timeout=15)

    def attest(self, digest_hex: str) -> dict:
        extend = self._run(["tpm2_pcrextend", f"{PCR_INDEX}:sha256={digest_hex}"])
        if extend.returncode != 0:
            return {"attested": False, "reason": f"pcrextend failed: {extend.stderr.strip()}"}

        nonce = uuid.uuid4().hex
        quote = self._run([
            "tpm2_quote", "-c", "0x81000001",
            "-l", f"sha256:{PCR_INDEX}",
            "-q", nonce,
            "-m", "/tmp/quote.msg", "-s", "/tmp/quote.sig", "-o", "/tmp/quote.pcrs",
        ])
        if quote.returncode != 0:
            return {"attested": False, "reason": f"quote failed: {quote.stderr.strip()}"}

        check = self._run([
            "tpm2_checkquote", "-c", "0x81000001",
            "-m", "/tmp/quote.msg", "-s", "/tmp/quote.sig", "-f", "/tmp/quote.pcrs",
            "-q", nonce,
        ])
        if check.returncode != 0:
            return {"attested": False, "reason": f"checkquote failed: {check.stderr.strip()}"}

        return {"attested": True, "reason": "attested"}

