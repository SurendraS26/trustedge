#!/bin/bash
echo "[*] Starting Ollama server..."
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
echo "[*] Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/version >/dev/null 2>&1; do
    sleep 1
done
echo "[✓] Ollama ready."
echo "[*] Pulling model..."
ollama pull qwen2.5:3b
echo "[*] Creating TrustEdge agent..."
ollama create trustedge-agent -f Modelfile
echo "[✓] Agent ready."
echo "[*] main.py is a one-shot CLI, not a long-running service - run tasks with:"
echo "      docker exec -it trustedge-c1 python main.py \"<task>\""
# Keep the container alive on the Ollama server instead of running main.py
# here: main.py reads a task from argv/stdin and exits, and this entrypoint
# has no interactive stdin, so calling it here immediately hit EOFError on
# input() and crash-looped the container.
wait "$OLLAMA_PID"
