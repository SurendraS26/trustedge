#!/usr/bin/env bash
docker run -d --rm \
  --name trustedge-c4 \
  --network trustedge-network \
  -p 6080:6080 \
  --shm-size=1g \
  trustedge-c4
