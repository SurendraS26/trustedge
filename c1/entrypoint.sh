#!/usr/bin/env bash
set -e
echo "[c1] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!
until curl -s http://127.0.0.1:11434 >/dev/null 2>&1; do
    sleep 1
done
echo "[c1] Ollama is up."
if [ -z "${OLLAMA_MODEL}" ]; then
    echo "[c1] ERROR: OLLAMA_MODEL is not set in .env. Set it manually and restart."
    wait "$OLLAMA_PID"
    exit 1
fi
echo "[c1] Ensuring model '${OLLAMA_MODEL}' is pulled (manual model choice)..."
ollama pull "${OLLAMA_MODEL}"
echo "[c1] Launching agent CLI..."
python main.py
wait "$OLLAMA_PID"
