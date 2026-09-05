#!/bin/bash
set -e

echo "[*] TrustEdge c3 — Framework starting..."

# ── TPM setup ─────────────────────────────────────────────────────────────
if [ ! -f /app/tpm_keys/ak.pub ]; then
    echo "[*] Attestation Key not found. Running TPM setup..."
    bash scripts/setup_tpm.sh
else
    echo "[+] Attestation Key already exists. Skipping TPM setup."
fi

# ── Baseline init ─────────────────────────────────────────────────────────
if [ ! -f /app/baseline_store/baseline.db ]; then
    echo "[*] Baseline not found. Initialising baseline..."
    python scripts/init_baseline.py
else
    echo "[+] Baseline already exists. Skipping init."
fi

# ── auditd rules ──────────────────────────────────────────────────────────
echo "[*] Installing auditd rules..."
bash interceptor/audit_rules.sh || echo "[WARN] auditd rules failed — interceptor may not work without CAP_AUDIT_CONTROL"

# ── Start interceptor ─────────────────────────────────────────────────────
echo "[*] Starting interceptor..."
python interceptor/interceptor.py &

# ── Start framework API ───────────────────────────────────────────────────
echo "[*] Starting TrustEdge framework API on port 8000..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
