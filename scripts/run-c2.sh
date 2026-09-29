#!/usr/bin/env bash
# TPM emulator
docker run -d --rm \
  --name trustedge-c2 \
  --network trustedge-network \
  -p 2321-2322:2321-2322 \
  -v trustedge-tpm-state:/var/lib/swtpm/tpmstate \
  trustedge-c2
