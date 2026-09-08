import os
import secrets
import subprocess

PCR_START = int(os.environ.get("PCR_START", 16))
PCR_COUNT = int(os.environ.get("PCR_COUNT", 4))
PCR_LIST = ",".join(str(PCR_START + i) for i in range(PCR_COUNT))

AK_CTX = "/tmp/ak.ctx"
QUOTE_OUT = "/tmp/quote.bin"
SIG_OUT = "/tmp/quote.sig"
PCR_OUT = "/tmp/pcrs.bin"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def extend_measurements(measurements: dict) -> None:
    target_pcr = str(PCR_START)
    for path, digest in measurements.items():
        if digest is None:
            continue
        _run(["tpm2_pcrextend", f"{target_pcr}:sha256={digest}"])


def generate_nonce() -> str:
    return secrets.token_hex(16)


def get_quote(nonce: str) -> dict:
    _run([
        "tpm2_quote",
        "-c", AK_CTX,
        "-l", f"sha256:{PCR_LIST}",
        "-q", nonce,
        "-m", QUOTE_OUT,
        "-s", SIG_OUT,
        "-o", PCR_OUT,
    ])
    return {
        "quote_path": QUOTE_OUT,
        "sig_path": SIG_OUT,
        "pcr_path": PCR_OUT,
        "nonce": nonce,
        "pcr_list": PCR_LIST,
    }


def run_attestation_cycle(measurements: dict) -> dict:
    extend_measurements(measurements)
    nonce = generate_nonce()
    return get_quote(nonce)
