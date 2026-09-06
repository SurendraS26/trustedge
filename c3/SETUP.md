# TrustEdge Setup

## Prerequisites

```bash
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker
```

## Build c2

```bash
cd c2
docker build -t trustedge-c2 .
cd ..
```

## Run (single command)

From the `c3/` directory:

```bash
docker compose up --build
```

That's it. This starts both c2 (swtpm) and c3 (framework) together.
On first run, c3 automatically runs TPM setup and baseline init before starting.

---

## Test

Open a second terminal:

```bash
# No TPM needed
docker exec trustedge-c3 python tests/test_policy.py
docker exec trustedge-c3 python tests/test_integrity.py

# Needs c2 running
docker exec trustedge-c3 python tests/test_tpm.py

# Needs c3 API running
docker exec trustedge-c3 python tests/test_api.py
```

## View alerts

```bash
docker exec trustedge-c3 sqlite3 /app/alerts/audit.db \
  "SELECT timestamp, action, target, reason FROM log ORDER BY id DESC LIMIT 20;"
```

## Stop

```bash
docker compose down
```

## Reset everything

```bash
docker compose down -v
```
