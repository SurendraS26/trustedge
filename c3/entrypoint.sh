#!/usr/bin/env bash
set -e

export TPM2TOOLS_TCTI="${TPM2TOOLS_TCTI:-swtpm:host=trustedge-c2,port=2321}"
export DASHBOARD_PATH="${DASHBOARD_PATH:-/data/dashboard.md}"

for i in $(seq 1 30); do
    if tpm2_startup -c >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

tpm2_createprimary -C o -c /tmp/primary.ctx >/dev/null 2>&1 || true
tpm2_evictcontrol -C o -c /tmp/primary.ctx 0x81000001 >/dev/null 2>&1 || true

python main.py &
API_PID=$!

exec ./dashboard.sh

kill "$API_PID" 2>/dev/null || true

