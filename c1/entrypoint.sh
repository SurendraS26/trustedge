#!/usr/bin/env bash
set -e

ollama serve &
OLLAMA_PID=$!

until curl -s http://127.0.0.1:11434 >/dev/null 2>&1; do
    sleep 1
done

if [ -z "${OLLAMA_MODEL}" ]; then
    echo "[c1] ERROR: OLLAMA_MODEL is not set in .env."
    wait "$OLLAMA_PID"
    exit 1
fi

ollama pull "${OLLAMA_MODEL}"
python main.py

wait "$OLLAMA_PID"
