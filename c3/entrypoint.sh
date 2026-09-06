#!/bin/bash
set -e

echo "[*] TrustEdge c3 starting..."

# Wait for c2 to be ready
echo "[*] Waiting for swtpm (c2)..."
until tpm2_startup -T "$TPM2TOOLS_TCTI" -c 2>/dev/null; do
    echo "[*] swtpm not ready yet, retrying in 2s..."
    sleep 2
done
echo "[+] swtpm ready"

# TPM setup — only if AK does not exist yet
if [ ! -f "$AK_PUB_PATH" ]; then
    echo "[*] Running TPM setup..."
    bash scripts/setup_tpm.sh
else
    echo "[+] AK already exists, skipping TPM setup"
fi

# Baseline init — only if DB does not exist yet
if [ ! -f "$BASELINE_DB" ]; then
    echo "[*] Running baseline init..."
    python scripts/init_baseline.py
else
    echo "[+] Baseline already exists, skipping"
fi

# Audit rules
bash interceptor/audit_rules.sh || echo "[WARN] audit rules failed"

# Start interceptor in background
python -m interceptor.interceptor &

echo "[*] Starting API on port 8000..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
