#!/bin/bash
set -e

echo "[*] TrustEdge c1 — AI Agent starting..."

echo "[*] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "[*] Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "[+] Ollama ready."

echo "[*] Pulling base model..."
ollama pull qwen2.5:3b

echo "[*] Creating TrustEdge agent from Modelfile..."
ollama create trustedge-agent -f Modelfile
echo "[+] trustedge-agent model ready."

echo "[*] Starting agent..."
exec python main.py

