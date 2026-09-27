#!/usr/bin/env bash
# Framework: policy + attestation + dashboard. Run this third.
docker run -it --rm \
  --name trustedge-c3 \
  --network trustedge-network \
  -p 8000:8000 \
  -e TPM2TOOLS_TCTI=swtpm:host=trustedge-c2,port=2321 \
  -e C4_EXEC_URL=http://trustedge-c4:9000/execute \
  -v trustedge-framework-data:/data \
  trustedge-c3
