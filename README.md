# TrustEdge

### Description
TPM-Assisted Secure Attestation Framework for AI Agents

---
### Overview
Artificial Intelligence (AI) agents are increasingly being deployed to automate tasks such as file access, database queries, cloud interactions, and tool execution. While these agents improve productivity, they also introduce significant security concerns because they often operate with elevated privileges and access to sensitive resources. Existing authentication mechanisms verify the identity of an agent during deployment but do not continuously verify its integrity during execution. This project proposes TrustEdge, a hardware-assisted runtime attestation framework that verifies the trustworthiness of an AI agent before allowing privileged operations, thereby improving the security of autonomous AI systems. 

---
### Workflow & Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI Agent Container                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  AI Agent (Python)                                                  │    │
│  │  - Model loading                                                    │    │
│  │  - Tool execution (file, DB, cloud)                                 │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐    │
│  │  TPM Measurement Module (Python + tpm2-tools)                       │    │
│  │  - tpm2_pcrread → hash agent code/config                            │    │
│  │  - tpm2_quote → sign PCRs with TPM key                              │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐    │
│  │  Runtime Monitor (Python + psutil + auditd)                         │    │
│  │  - CPU, memory, processes, network                                  │    │
│  │  - Logs → JSON                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/gRPC (Quote + Telemetry)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Attestation Verifier (Python + FastAPI)           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Quote Verification Module                                          │    │
│  │  - Validate signature (cryptography library)                        │    │
│  │  - Compare PCRs against YAML policies (policy.yaml)                 │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                           │
│  ┌──────────────────────────────▼──────────────────────────────────────┐    │
│  │  Policy & Risk Engine (Python)                                      │    │
│  │  - Allowlists (YAML)                                                │    │
│  │  - Invariant checks                                                 │    │
│  │  - Anomaly detection (scikit-learn Isolation Forest)                │    │
│  │  - Risk score → allow/deny/alert                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Dashboard (Streamlit)                             │
│  - Real-time metrics                                                        │
│  - Alerts                                                                   │
│  - Risk levels                                                              │
│  - Attestation status                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```
---
### Installation

```
cat > Dockerfile <<'EOF'
FROM archlinux:base

RUN pacman -Syu --noconfirm --needed swtpm tpm2-tools tpm2-tss && \
    pacman -Scc --noconfirm

RUN mkdir -p /var/lib/swtpm-state
EXPOSE 2321 2322

ENTRYPOINT ["swtpm", "socket", \
  "--tpmstate", "dir=/var/lib/swtpm-state", \
  "--ctrl", "type=tcp,port=2322", \
  "--server", "type=tcp,port=2321", \
  "--flags", "not-need-init", \
  "--tpm2", "--log", "level=1"]
EOF

docker build -t swtpm-arch .

docker run -d --name swtpm-arch \
  -p 2321:2321 -p 2322:2322 \
  -v swtpm-arch-state:/var/lib/swtpm-state \
  swtpm-arch

export TPM2TOOLS_TCTI="swtpm:host=127.0.0.1,port=2321"
tpm2_startup -c
tpm2_pcrread sha256:0,1,2,3
```
