#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
docker build -t trustedge-c1 ./c1
docker build -t trustedge-c2 ./c2
docker build -t trustedge-c3 ./c3
docker build -t trustedge-c4 ./c4
echo "all images built"
