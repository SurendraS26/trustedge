#!/usr/bin/env bash
set -e

mkdir -p /var/log
ollama serve > /var/log/ollama.log 2>&1 &
OLLAMA_PID=$!

for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

ollama pull "${OLLAMA_MODEL:-qwen2.5:7b}" >> /var/log/ollama.log 2>&1

exec python agent.py

kill "$OLLAMA_PID" 2>/dev/null || true

