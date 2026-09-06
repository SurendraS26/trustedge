#!/bin/bash
set -e

export TPM2TOOLS_TCTI="${TPM2TOOLS_TCTI:-swtpm:host=c2,port=2321}"
AK_HANDLE="${AK_HANDLE:-0x81010001}"
AK_PUB="${AK_PUB_PATH:-/app/tpm_keys/ak.pub}"
DIR=$(dirname "$AK_PUB")

mkdir -p "$DIR"

echo "[*] TPM startup"
tpm2_startup -c

echo "[*] Creating primary key"
tpm2_createprimary -C o -g sha256 -G ecc -c "$DIR/primary.ctx"

echo "[*] Creating attestation key"
tpm2_createak \
    -C "$DIR/primary.ctx" \
    -c "$DIR/ak.ctx" \
    -u "$AK_PUB" \
    -n "$DIR/ak.name" \
    -G ecc

echo "[*] Persisting AK at $AK_HANDLE"
tpm2_evictcontrol -C o -c "$DIR/ak.ctx" "$AK_HANDLE"

echo "[+] TPM setup done"
