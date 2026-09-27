#!/usr/bin/env bash
# Agent. Run this last - this is where you type tasks.
docker run -it --rm \
  --name trustedge-c1 \
  --network trustedge-network \
  -e OLLAMA_MODEL=qwen2.5:7b \
  -e FRAMEWORK_WS=ws://trustedge-c3:8000/agent-link \
  trustedge-c1
