#!/bin/bash
echo "Started SWTPM"
docker run -d --name trustedge-c2 \
  --network trustedge-net \
  -p 2321:2321 -p 2322:2322 \
  -v swtpm-state:/var/lib/swtpm/tpmstate \
  trustedge-c2
echo "Stopped the container"
