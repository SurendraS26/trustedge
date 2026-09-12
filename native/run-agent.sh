#!/usr/bin/env bash

set -e

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO/c1"
source "$REPO/c1/.venv/bin/activate"
[[ -f "$REPO/.env" ]] && set -a && source "$REPO/.env" && set +a

export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
export FRAMEWORK_URL="${FRAMEWORK_URL:-http://127.0.0.1:8000/evaluate}"

if ! curl -s "${OLLAMA_HOST}/api/version" >/dev/null 2>&1; then
    echo "[agent] Ollama isn't reachable at ${OLLAMA_HOST}."
    echo "[agent] Start it with: sudo systemctl start ollama"
    exit 1
fi

if ! curl -sf "${FRAMEWORK_URL%/evaluate}/health" >/dev/null 2>&1; then
    echo "[agent] Warning: framework not reachable at ${FRAMEWORK_URL}."
    echo "[agent] Start it with: systemctl --user start trustedge-framework"
    echo "[agent] Continuing anyway - every action will fail its policy check until it's up."
fi

echo "[agent] indexing local documents in data/ for retrieval (RAG)"
python ingest.py || echo "[agent] ingest.py reported an issue, continuing without a fresh index"

echo "[agent] launching agent"
exec python main.py
