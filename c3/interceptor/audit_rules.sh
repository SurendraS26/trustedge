#!/bin/bash
auditctl -D -k trustedge_exec 2>/dev/null || true
auditctl -a always,exit -F arch=b64 -S execve -k trustedge_exec
auditctl -a always,exit -F arch=b32 -S execve -k trustedge_exec
echo "[+] Audit rules installed"
