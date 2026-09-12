import logging
import os
import secrets
import subprocess
import tempfile

log = logging.getLogger("verifier")

AK_HANDLE = "0x81010001"
PCR_INDEX = 16
PCR_BANK = "sha256"
DATA_DIR = os.environ.get("SQLITE_PATH", "/data/trustedge.db")
DATA_DIR = os.path.dirname(DATA_DIR) or "/data"
AK_PUB = os.path.join(DATA_DIR, "ak.pub")


def _run(cmd):
    log.debug("running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({' '.join(cmd)}): {result.stderr.strip()}"
        )
    return result.stdout


class Verifier:
    """
    A single Verifier instance handles one attestation round for one
    proposed action: reset the PCR, extend it with the current combined
    measurement digest, get a quote, and check that quote.
    """

    def __init__(self, ak_handle=AK_HANDLE, pcr_index=PCR_INDEX, ak_pub_path=AK_PUB):
        self.ak_handle = ak_handle
        self.pcr_index = pcr_index
        self.ak_pub_path = ak_pub_path

    def extend_pcr(self, combined_digest_hex):
        """Extend PCR_INDEX with the given hex digest of measured state."""
        _run([
            "tpm2_pcrextend",
            f"{self.pcr_index}:{PCR_BANK}={combined_digest_hex}",
        ])
        log.info("extended PCR %d with digest %s", self.pcr_index, combined_digest_hex[:16])

    def read_pcr(self):
        output = _run(["tpm2_pcrread", f"{PCR_BANK}:{self.pcr_index}"])
        return output.strip()

    def quote(self):
        """
        Request a signed quote over PCR_INDEX bound to a fresh nonce.

        Returns (nonce_hex, message_path, signature_path, pcrs_path) - the
        caller is responsible for cleaning up the temp files.
        """
        nonce_hex = secrets.token_hex(16)
        tmpdir = tempfile.mkdtemp(prefix="quote-")
        message_path = os.path.join(tmpdir, "quote.msg")
        signature_path = os.path.join(tmpdir, "quote.sig")
        pcrs_path = os.path.join(tmpdir, "pcrs.out")

        _run([
            "tpm2_quote",
            "-c", self.ak_handle,
            "-l", f"{PCR_BANK}:{self.pcr_index}",
            "-q", nonce_hex,
            "-m", message_path,
            "-s", signature_path,
            "-o", pcrs_path,
            "-g", PCR_BANK,
        ])
        log.info("quote generated for PCR %d, nonce=%s", self.pcr_index, nonce_hex[:16])
        return nonce_hex, message_path, signature_path, pcrs_path

    def verify_quote(self, nonce_hex, message_path, signature_path, pcrs_path):
        """
        Verify the quote's signature and nonce using tpm2_checkquote.
        Returns True if the quote is valid, False otherwise.
        """
        if not os.path.exists(self.ak_pub_path):
            log.error("AK public key not found at %s; run setup_tpm.sh first", self.ak_pub_path)
            return False

        try:
            _run([
                "tpm2_checkquote",
                "-u", self.ak_pub_path,
                "-m", message_path,
                "-s", signature_path,
                "-f", pcrs_path,
                "-g", PCR_BANK,
                "-q", nonce_hex,
            ])
            return True
        except RuntimeError as exc:
            log.error("quote verification failed: %s", exc)
            return False

    def attest(self, combined_digest_hex):
        """
        Full attestation round for one proposed action.

        Returns a dict: { "attested": bool, "reason": str }
        """
        try:
            self.extend_pcr(combined_digest_hex)
            nonce_hex, message_path, signature_path, pcrs_path = self.quote()
            ok = self.verify_quote(nonce_hex, message_path, signature_path, pcrs_path)
            if ok:
                return {"attested": True, "reason": "quote signature and nonce verified"}
            return {"attested": False, "reason": "quote verification failed"}
        except RuntimeError as exc:
            log.error("attestation round failed: %s", exc)
            return {"attested": False, "reason": str(exc)}
