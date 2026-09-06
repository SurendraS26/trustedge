"""Test TPM operations — requires c2 running"""
import os, subprocess, sys, tempfile
sys.path.insert(0, "/app")

TCTI   = os.environ.get("TPM2TOOLS_TCTI", "swtpm:host=c2,port=2321")
AK     = os.environ.get("AK_HANDLE", "0x81010001")
AK_PUB = os.environ.get("AK_PUB_PATH", "/app/tpm_keys/ak.pub")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True,
                          env={**os.environ, "TPM2TOOLS_TCTI": TCTI})


print(f"\n=== TPM Tests (TCTI: {TCTI}) ===")

r = run(["tpm2_startup", "-c"])
print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] tpm2_startup")

r = run(["tpm2_pcrreset", "16"])
print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] tpm2_pcrreset 16")

r = run(["tpm2_pcrread", "sha256:16"])
print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] tpm2_pcrread sha256:16")

r = run(["tpm2_pcrextend", "16:sha256=2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"])
print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] tpm2_pcrextend")

r = run(["tpm2_readpublic", "-c", AK])
print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] AK readable at {AK}")

msg  = tempfile.mktemp(suffix=".msg")
sig  = tempfile.mktemp(suffix=".sig")
pcrs = tempfile.mktemp(suffix=".pcrs")
r = run(["tpm2_quote", "-c", AK, "-l", "sha256:16",
         "-q", "deadbeef"*8, "-m", msg, "-s", sig, "-o", pcrs, "-g", "sha256"])
print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] tpm2_quote")

if os.path.exists(AK_PUB) and r.returncode == 0:
    r = run(["tpm2_checkquote", "-u", AK_PUB, "-m", msg, "-s", sig,
             "-f", pcrs, "-g", "sha256", "-l", "sha256:16", "-q", "deadbeef"*8])
    print(f"  [{'PASS' if r.returncode==0 else 'FAIL'}] tpm2_checkquote")

for f in [msg, sig, pcrs]:
    try: os.remove(f)
    except: pass
print()
