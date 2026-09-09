#!/usr/bin/env bash
set -e

echo "[*] Ollama Server: Starting"
ollama serve &
OLLAMA_PID=$!

# Wait for the server to accept connections.
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
        break
    fi
    sleep 1 && echo "[*] Ollama Server: Running"
done

echo "[*] pulling base model ${OLLAMA_MODEL:-mistral:7b}"
ollama pull "${OLLAMA_MODEL:-mistral:7b}"

echo "[*] building trustedge-agent model from Modelfile"
ollama create trustedge-agent -f /app/Modelfile

echo "[*] pulling embedding model ${EMBED_MODEL:-mxbai-embed-large}"
ollama pull "${EMBED_MODEL:-mxbai-embed-large}"

echo "[*] indexing local documents in data/ for retrieval (RAG)"
python ingest.py || echo "[*] ingest.py reported an issue, continuing without a fresh index"

echo "[*] launching agent"
python main.py

kill "$OLLAMA_PID" 2>/dev/null || true
