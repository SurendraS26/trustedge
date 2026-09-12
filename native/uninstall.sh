#!/usr/bin/env bash

set -euo pipefail

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "==> Stopping TrustEdge services"
systemctl --user disable --now trustedge-dashboard.service trustedge-framework.service trustedge-tpm.service 2>/dev/null || true

echo "==> Removing unit files"
rm -f "$SYSTEMD_USER_DIR/trustedge-tpm.service" \
      "$SYSTEMD_USER_DIR/trustedge-framework.service" \
      "$SYSTEMD_USER_DIR/trustedge-dashboard.service"

systemctl --user daemon-reload

echo "==> Done. Data left in place:"
echo "    ~/.local/share/trustedge/  (TPM state, sqlite db, attestation key)"
echo "    c1/.venv, c3/.venv         (Python environments)"
echo "    .env                       (your configuration)"
