#!/bin/bash
set -e

echo "[*] Clearing existing TrustEdge audit rules..."
auditctl -D -k trustedge_exec 2>/dev/null || true

echo "[*] Installing execve watch rules..."
auditctl -a always,exit -F arch=b64 -S execve -k trustedge_exec
auditctl -a always,exit -F arch=b32 -S execve -k trustedge_exec

echo "[+] TrustEdge audit rules installed."
auditctl -l | grep trustedge_exec
