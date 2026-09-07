#!/usr/bin/env bash
set -e
OLLAMA_PID=$!
OLLAMA_MODEL=mistral:7b
echo "[*] starting ollama server"
ollama serve > /dev/null 2>&1 &
until curl -s http://localhost:11434/api/version >/dev/null 2>&1; do sleep 1; done
echo "[*] pull model $OLLAMA_MODEL"
ollama pull $OLLAMA_MODEL
echo "[*] creating trustedge-agent < Modelfile"
ollama create trustedge-agent -f /app/Modelfile
echo "[*] Running trustedge-agent"
python main.py
kill "$OLLAMA_PID" 2>/dev/null || true
