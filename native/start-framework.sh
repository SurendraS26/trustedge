#!/usr/bin/env bash
#
# Native launcher for the TrustEdge framework API (c3), run by
# trustedge-framework.service. Waits for the local swtpm, provisions the
# attestation key, then starts the FastAPI app - the same sequence
# c3/entrypoint.sh did inside the container, just against a local venv
# and localhost TPM instead of a docker network.
#
set -e

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO/c3"
source "$REPO/c3/.venv/bin/activate"

export TCTI="${TCTI:-swtpm:host=127.0.0.1,port=2321}"
export TPM2TOOLS_TCTI="$TCTI"
export SQLITE_PATH="${SQLITE_PATH:-$HOME/.local/share/trustedge/data/trustedge.db}"
export DATA_DIR="$(dirname "$SQLITE_PATH")"
export DISPLAY="${DISPLAY:-:0}"
mkdir -p "$DATA_DIR"

echo "[c3] waiting for TPM at $TCTI"
for i in $(seq 1 30); do
    if tpm2_startup -c >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "[c3] provisioning attestation key (idempotent)"
bash scripts/setup_tpm.sh || echo "[c3] setup_tpm.sh reported an issue, continuing"

echo "[c3] starting API on :${FRAMEWORK_PORT:-8000}"
exec python main.py
