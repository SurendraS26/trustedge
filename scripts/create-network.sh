#!/usr/bin/env bash
docker network create trustedge-network 2>/dev/null || echo "trustedge-network already exists"
