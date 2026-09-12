#!/usr/bin/env bash
set -e

AK_HANDLE="0x81010001"
DATA_DIR="${DATA_DIR:-/data}"
AK_PUB="${DATA_DIR}/ak.pub"
AK_NAME="${DATA_DIR}/ak.name"

mkdir -p "${DATA_DIR}"

if tpm2_readpublic -c "${AK_HANDLE}" -o "${AK_PUB}" -n "${AK_NAME}" >/dev/null 2>&1; then
    echo "[setup_tpm] attestation key already provisioned at ${AK_HANDLE}"
    exit 0
fi

# swtpm's reference implementation only has a handful of transient object
# slots, so free them between steps rather than letting EK/AK contexts pile
# up (otherwise later commands fail with "out of memory for object contexts").
tpm2_flushcontext -t >/dev/null 2>&1 || true

echo "[setup_tpm] creating endorsement key"
tpm2_createek -c /tmp/ek.ctx -G rsa -u /tmp/ek.pub

echo "[setup_tpm] creating attestation key"
tpm2_createak \
    -C /tmp/ek.ctx \
    -c /tmp/ak.ctx \
    -G rsa \
    -g sha256 \
    -s rsassa \
    -u /tmp/ak.pub \
    -n /tmp/ak.name

tpm2_flushcontext -t >/dev/null 2>&1 || true

echo "[setup_tpm] persisting attestation key at ${AK_HANDLE}"
tpm2_evictcontrol -C o -c /tmp/ak.ctx "${AK_HANDLE}"

tpm2_flushcontext -t >/dev/null 2>&1 || true

tpm2_readpublic -c "${AK_HANDLE}" -o "${AK_PUB}" -n "${AK_NAME}"

echo "[setup_tpm] done"
