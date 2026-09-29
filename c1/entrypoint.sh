#!/usr/bin/env bash
MODEL="${OLLAMA_MODEL:-qwen2.5-coder:7b}"

ollama serve > /var/log/ollama.log 2>&1 &
OLLAMA_PID=$!

until curl -s http://localhost:11434/api/version >/dev/null 2>&1; do sleep 1; done

if ollama list | grep -q "^${MODEL}"; then
    echo "[c1] model ${MODEL} already downloaded"
else
    echo "[c1] downloading ${MODEL} (first run only, stored in a volume)"
    ollama pull "${MODEL}" >> /var/log/ollama.log 2>&1
fi

echo "[c1] loading model into memory"
curl -s http://localhost:11434/api/generate -d "{\"model\":\"${MODEL}\",\"prompt\":\"\",\"keep_alive\":\"30m\"}" >/dev/null
ollama ps
echo "[c1] ready - open the agent with: ./scripts/agent.sh"

wait "$OLLAMA_PID"
