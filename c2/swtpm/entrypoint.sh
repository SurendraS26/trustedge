#!/usr/bin/env bash
set -e

SOCK=/tmp/swtpm.sock
STATE_DIR=/var/lib/swtpm

echo "[c2] Starting swtpm..."
swtpm socket \
    --tpm2 \
    --tpmstate dir="${STATE_DIR}" \
    --ctrl type=unixio,path="${SOCK}.ctrl" \
    --server type=unixio,path="${SOCK}" \
    --flags not-need-init \
    --daemon

export TPM2TOOLS_TCTI="swtpm:path=${SOCK}"

# Wait for the socket to appear
for i in $(seq 1 20); do
    [ -S "${SOCK}" ] && break
    sleep 0.5
done

if [ ! -f "${STATE_DIR}/.ak_created" ]; then
    echo "[c2] First run: creating primary key + Attestation Key..."
    tpm2_startup -c || true
    tpm2_createprimary -C o -c /tmp/primary.ctx
    tpm2_createak -C /tmp/primary.ctx -c /tmp/ak.ctx -u /app/framework/ak_pub.pem -f pem
    touch "${STATE_DIR}/.ak_created"
fi

echo "[c2] Starting TrustEdge decision server on :8765..."
cd /app
export PYTHONPATH=/app
python -m framework.decision_server
