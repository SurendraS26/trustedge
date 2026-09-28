#!/usr/bin/env bash
docker run -d --rm \
  --name trustedge-c1 \
  --network trustedge-network \
  --gpus all \
  -e OLLAMA_MODEL=qwen2.5:7b \
  -e FRAMEWORK_WS=ws://trustedge-c3:8000/agent-link \
  -v trustedge-ollama:/root/.ollama \
  trustedge-c1
