#!/usr/bin/env bash
# Sandbox desktop (XFCE4 + TigerVNC + noVNC).
# Open http://localhost:6080/vnc.html - VNC password: trustedge
docker run -d --rm \
  --name trustedge-c4 \
  --network trustedge-network \
  -p 6080:6080 \
  --shm-size=1g \
  trustedge-c4
