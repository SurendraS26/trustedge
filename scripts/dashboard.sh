#!/usr/bin/env bash
# Live dashboard, re-rendered by glow whenever dashboard.md changes.
# Ctrl-C only closes the view, c3 keeps running.
exec docker exec -it trustedge-c3 /app/dashboard.sh
