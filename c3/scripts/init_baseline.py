import json
import os
import subprocess
import sys

sys.path.insert(0, "/app")
from baseline_store.baseline_store import init_db, save_file_hash, save_pcr, hash_file

TCTI = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=c2,port=2321")
PCR  = os.environ.get("TPM_PCR", "16")
CFG  = "/app/integrity_monitor/measured_files.json"

init_db()

with open(CFG) as f:
    files = json.load(f).get("files", [])

for path in files:
    h = hash_file(path)
    if h:
        save_file_hash(path, h)
        print(f"[+] {path}")
    else:
        print(f"[!] skipped {path}")

r = subprocess.run(
    ["tpm2_pcrread", f"sha256:{PCR}"],
    capture_output=True, text=True,
    env={**os.environ, "TPM2TOOLS_TCTI": TCTI}
)

for line in r.stdout.splitlines():
    line = line.strip()
    if line.startswith(f"{PCR}:"):
        val = line.split()[1].lower()
        save_pcr(PCR, val)
        print(f"[+] PCR {PCR} = {val}")
        break

print("[+] Baseline init done")
