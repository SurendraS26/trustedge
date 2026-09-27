#!/usr/bin/env bash
# Sandbox desktop (Hyprland, wayvnc, noVNC). Run this second.
# Open http://localhost:6080/vnc.html in a browser once this is up.
docker run -it --rm \
  --name trustedge-c4 \
  --network trustedge-network \
  -p 6080:6080 \
  --shm-size=1g \
  trustedge-c4
