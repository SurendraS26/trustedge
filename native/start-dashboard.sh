#!/usr/bin/env bash

set -e

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO/c3"
source "$REPO/c3/.venv/bin/activate"

export SQLITE_PATH="${SQLITE_PATH:-$HOME/.local/share/trustedge/data/trustedge.db}"

echo "[dashboard] starting on :${DASHBOARD_PORT:-8501}"
exec streamlit run dashboard/app.py \
    --server.port "${DASHBOARD_PORT:-8501}" \
    --server.address 127.0.0.1 \
    --server.headless true
