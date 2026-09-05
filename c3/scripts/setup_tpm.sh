#!/bin/bash
# TrustEdge — TPM Setup
# Creates a primary key and Attestation Key inside swtpm,
# persists the AK at handle 0x81010001, and exports the public key
# for use by the Verifier.
# Run once before starting the framework.

set -e

TCTI="${TPM2TOOLS_TCTI:-swtpm:host=trustedge-c2,port=2321}"
AK_HANDLE="${AK_HANDLE:-0x81010001}"
AK_PUB_PATH="${AK_PUB_PATH:-/app/tpm_keys/ak.pub}"
KEY_DIR=$(dirname "$AK_PUB_PATH")

export TPM2TOOLS_TCTI="$TCTI"

mkdir -p "$KEY_DIR"

echo "[*] Initialising TPM..."
tpm2_startup -c

echo "[*] Creating primary key..."
tpm2_createprimary -C o -g sha256 -G ecc -c "$KEY_DIR/primary.ctx"

echo "[*] Creating Attestation Key..."
tpm2_createak \
    -C "$KEY_DIR/primary.ctx" \
    -c "$KEY_DIR/ak.ctx" \
    -u "$AK_PUB_PATH" \
    -n "$KEY_DIR/ak.name" \
    -G ecc

echo "[*] Persisting Attestation Key at handle $AK_HANDLE..."
tpm2_evictcontrol -C o -c "$KEY_DIR/ak.ctx" "$AK_HANDLE"

echo "[+] TPM setup complete."
echo "[+] AK public key saved to: $AK_PUB_PATH"
echo "[+] AK persisted at handle: $AK_HANDLE"

# Verify
tpm2_readpublic -c "$AK_HANDLE"
