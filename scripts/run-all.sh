#!/usr/bin/env bash
# Starts c2, c4, c3 in the background, then runs c1 in the foreground
# (since that's the one you actually type into). For running things
# one at a time instead, use the individual run-cN.sh scripts.
set -e
cd "$(dirname "$0")"

./create-network.sh

docker run -d --rm --name trustedge-c2 --network trustedge-network \
  -p 2321-2322:2321-2322 -v trustedge-tpm-state:/var/lib/swtpm/tpmstate trustedge-c2

docker run -d --rm --name trustedge-c4 --network trustedge-network \
  -p 6080:6080 --shm-size=1g trustedge-c4

docker run -d --rm --name trustedge-c3 --network trustedge-network \
  -p 8000:8000 \
  -e TPM2TOOLS_TCTI=swtpm:host=trustedge-c2,port=2321 \
  -e C4_EXEC_URL=http://trustedge-c4:9000/execute \
  -v trustedge-framework-data:/data trustedge-c3

echo "c2, c3, c4 started in the background."
echo "dashboard: docker logs -f trustedge-c3"
echo "desktop:   http://localhost:6080/vnc.html"
echo "starting c1 now, in the foreground:"
echo ""

docker run -it --rm --name trustedge-c1 --network trustedge-network \
  -e OLLAMA_MODEL=qwen2.5:7b \
  -e FRAMEWORK_WS=ws://trustedge-c3:8000/agent-link trustedge-c1
