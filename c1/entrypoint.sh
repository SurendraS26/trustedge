#!/bin/bash
echo "[*] Starting Ollama server..."
ollama serve > /dev/null 2>&1 &
echo "[*] Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/version >/dev/null 2>&1; do
    sleep 1
done
echo "[✓] Ollama ready."
echo "[*] Pulling model..."
ollama pull qwen2.5:3b
echo "[*] Creating TrustEdge agent..."
ollama create trustedge-agent -f Modelfile
echo "[✓] Agent ready. Talker running in background..."
python main.py
