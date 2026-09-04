#!/bin/bash
set -e

echo "[*] C3 - Framework starting...."

echo "[*] Initializing baseline store...."

python -c "from baseline_store.baseline_store import init_db; init_db()"

echo "[*] Installing auditd rules...."
bash interceptor/audit_rules.sh

echo "[*] Starting interceptor in background...."
python interceptor/interceptor.py &

echo "[*] Starting framework API...."
exec uvicorn main:app --host 0.0.0.0 --port 8000

