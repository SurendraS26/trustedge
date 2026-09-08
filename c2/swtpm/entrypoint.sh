#!/usr/bin/env bash
set -e

SOCK=/tmp/swtpm.sock
STATE_DIR=/var/lib/swtpm

swtpm socket \
    --tpm2 \
    --tpmstate dir="${STATE_DIR}" \
    --ctrl type=unixio,path="${SOCK}.ctrl" \
    --server type=unixio,path="${SOCK}" \
    --flags not-need-init \
    --daemon

export TPM2TOOLS_TCTI="swtpm:path=${SOCK}"

for i in $(seq 1 20); do
    [ -S "${SOCK}" ] && break
    sleep 0.5
done

if [ ! -f "${STATE_DIR}/.ak_created" ]; then
    tpm2_startup -c || true
    tpm2_createprimary -C o -c /tmp/primary.ctx
    tpm2_createak -C /tmp/primary.ctx -c /tmp/ak.ctx -u /app/framework/ak_pub.pem -f pem
    touch "${STATE_DIR}/.ak_created"
fi

cd /app
export PYTHONPATH=/app
python -m framework.decision_server
