#!/usr/bin/env bash
set -e
echo "[c1] starting ollama server"
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "[c1] pulling base model ${OLLAMA_MODEL:-qwen2.5:3b}"
ollama pull "${OLLAMA_MODEL:-qwen2.5:3b}"

echo "[c1] building trustedge-agent model from Modelfile"
ollama create trustedge-agent -f /app/Modelfile

echo "[c1] launching agent"
python main.py

kill "$OLLAMA_PID" 2>/dev/null || true
