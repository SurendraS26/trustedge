# TrustEdge — Setup Guide

Complete installation from scratch to a running three-container system.

---

## Prerequisites (Host — Arch Linux)

```bash
sudo pacman -S --needed docker docker-compose nvidia-container-toolkit audit git
sudo systemctl enable --now docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
sudo systemctl enable --now auditd
```

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/SurendraS26/trustedge.git
cd trustedge
```

---

## Step 2 — Build the containers

```bash
# c2 — pull your existing swtpm image
docker pull ghcr.io/surendras26/swtpm-arch-docker:latest
docker tag ghcr.io/surendras26/swtpm-arch-docker:latest trustedge-c2

# c3 — framework
docker build -t trustedge-c3 ./c3

# c1 — agent
docker build -t trustedge-c1 ./c1
```

---

## Step 3 — Create Docker network and volumes

```bash
docker network create trustedge-net
docker volume create swtpm-state
docker volume create ollama-models
```

---

## Step 4 — Start c2 (swtpm) first

```bash
docker run -d \
  --name trustedge-c2 \
  --network trustedge-net \
  -p 2321:2321 -p 2322:2322 \
  -v swtpm-state:/var/lib/swtpm/tpmstate \
  trustedge-c2
```

Verify c2 is up:
```bash
docker logs trustedge-c2
```

---

## Step 5 — TPM setup (run once)

Creates and persists the Attestation Key inside swtpm.

```bash
docker run --rm \
  --network trustedge-net \
  -e TPM2TOOLS_TCTI="swtpm:host=trustedge-c2,port=2321" \
  -v trustedge-tpm-keys:/app/tpm_keys \
  trustedge-c3 \
  bash scripts/setup_tpm.sh
```

---

## Step 6 — Baseline initialisation (run once)

Records clean-state file hashes and PCR value into the baseline store.
**Run this on a known-clean system before starting the framework.**

```bash
docker run --rm \
  --network trustedge-net \
  -e TPM2TOOLS_TCTI="swtpm:host=trustedge-c2,port=2321" \
  -v trustedge-tpm-keys:/app/tpm_keys \
  -v trustedge-baseline:/app/baseline_store \
  trustedge-c3 \
  python scripts/init_baseline.py
```

---

## Step 7 — Start c3 (framework)

```bash
docker run -d \
  --name trustedge-c3 \
  --network trustedge-net \
  --privileged \
  -p 8000:8000 \
  -e TPM2TOOLS_TCTI="swtpm:host=trustedge-c2,port=2321" \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /var/log/audit:/var/log/audit:ro \
  -v trustedge-tpm-keys:/app/tpm_keys \
  -v trustedge-baseline:/app/baseline_store \
  trustedge-c3
```

Verify c3 is up:
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Step 8 — Start c1 (agent)

```bash
docker run -d \
  --name trustedge-c1 \
  --network trustedge-net \
  --gpus all \
  -v ollama-models:/root/.ollama \
  trustedge-c1
```

---

## Step 9 — Run the tests

### Test 1: Policy Engine (no TPM needed)
```bash
docker exec trustedge-c3 python tests/test_policy.py
```

### Test 2: Integrity Monitor (no TPM needed)
```bash
docker exec trustedge-c3 python tests/test_integrity.py
```

### Test 3: TPM connectivity
```bash
docker exec trustedge-c3 python tests/test_tpm.py
```

### Test 4: Full API pipeline
```bash
docker exec trustedge-c3 python tests/test_api.py
```

---

## Quick docker-compose alternative (Steps 3–8 in one command)

```bash
docker compose up --build
```

See `docker-compose.yml` in the project root.

---

## Checking alerts

```bash
# Live framework logs
docker logs -f trustedge-c3

# Audit log (all deny events)
docker exec trustedge-c3 sqlite3 /app/alerts/audit.db \
  "SELECT timestamp, action, target, reason FROM audit_log ORDER BY id DESC LIMIT 20;"
```

---

## Resetting everything

```bash
docker stop trustedge-c1 trustedge-c2 trustedge-c3
docker rm   trustedge-c1 trustedge-c2 trustedge-c3
docker volume rm swtpm-state trustedge-tpm-keys trustedge-baseline
```

Then re-run from Step 4.
