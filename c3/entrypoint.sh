#!/usr/bin/env bash
set -e

echo "[c3] waiting for TPM at ${TCTI:-swtpm:host=c2-tpm,port=2321}"
export TPM2TOOLS_TCTI="${TCTI:-swtpm:host=c2-tpm,port=2321}"

for i in $(seq 1 30); do
    if tpm2_startup -c >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "[c3] provisioning attestation key (idempotent)"
bash scripts/setup_tpm.sh || echo "[c3] setup_tpm.sh reported an issue, continuing"

echo "[c3] starting dashboard on :8501"
streamlit run dashboard/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true &

echo "[c3] starting API on :8000"
exec python main.py
