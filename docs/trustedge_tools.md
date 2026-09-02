# TrustEdge — Required Tools & Technologies

## Phase 1: TPM Setup (Container 2)
- Docker
- Arch Linux (base image)
- swtpm
- tpm2-tools
- tpm2-tss

## Phase 2: Interceptor
- auditd
- Python 3
- hashlib (SHA-256)

## Phase 3: AI Agent
- Python 3
- Ollama
- Qwen2.5-3B or Llama3.2-3B (model)
- Docker

## Phase 4: Verifier
- FastAPI
- YAML
- SQLite
- tpm2-pytss
- cryptography (Python library)

## Framework Components (Container 1)
- Python 3
- JSON / SQLite (policy rules, baseline store)
- tpm2-pytss or tpm2-tools (via subprocess)
- requests (HTTP client, for Ollama API calls)

## Integration
- docker-compose
- Unix domain socket (`/tmp/swtpm.sock`)
- TCTI (TPM Command Transmission Interface)

## Documentation
- Markdown

## Version Control / CI
- Git
- GitHub
- GitHub Actions (multi-arch builds)
- GitHub CLI (`gh`)

## Supporting Utilities
- xz (compression)
- sha256sum
- Docker Buildx
