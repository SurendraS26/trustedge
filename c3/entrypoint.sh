#!/usr/bin/env bash
export TPM2TOOLS_TCTI="${TPM2TOOLS_TCTI:-swtpm:host=trustedge-c2,port=2321}"

echo "[c3] waiting for TPM"
for i in $(seq 1 30); do
    tpm2_startup -c >/dev/null 2>&1 && break
    sleep 1
done

if bash scripts/setup_tpm.sh > /var/log/setup_tpm.log 2>&1; then
    echo "[c3] attestation key ready"
else
    echo "[c3] TPM setup failed (see /var/log/setup_tpm.log) - actions will be blocked"
fi

echo "[c3] api starting on :8000"
echo "[c3] view the dashboard with: ./scripts/dashboard.sh"
exec python main.py
