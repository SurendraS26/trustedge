#!/usr/bin/env bash
# Agent + Ollama. Needs the NVIDIA Container Toolkit for --gpus all.
# The model is stored in the trustedge-ollama volume, so it is only
# downloaded once.
docker run -d --rm \
  --name trustedge-c1 \
  --network trustedge-network \
  --gpus all \
  -e OLLAMA_MODEL=qwen2.5-coder:7b \
  -e FRAMEWORK_WS=ws://trustedge-c3:8000/agent-link \
  -v trustedge-ollama:/root/.ollama \
  trustedge-c1
