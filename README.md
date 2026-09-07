# TrustEdge

![status](https://img.shields.io/badge/status-prototype-yellow)
![license](https://img.shields.io/badge/license-MIT-blue)
![platform](https://img.shields.io/badge/base-Arch%20Linux-1793d1)
![python](https://img.shields.io/badge/python-3-3776AB)
![docker](https://img.shields.io/badge/docker-compose-2496ED)

TrustEdge is a TPM-based remote attestation framework that verifies an AI
agent's actions before they execute, instead of trusting the agent's own
judgment. A compromised or malicious agent cannot bypass it because the
agent has no access to the TPM or the enforcement code.

Every action the agent proposes — read a file, write a file, run a
command, hit the network — is intercepted, classified, checked against a
policy, verified against a hardware-backed integrity baseline, attested by
a TPM, and only then handed to a human for a final ALLOW/BLOCK call.

## Architecture

Three containers, each on Arch Linux:

| Container | Role |
|---|---|
| `c1` | AI agent (Ollama, `qwen2.5:3b`). Proposes actions as JSON. Never executes anything itself. |
| `c2` | Software TPM (`swtpm` + `tpm2-tools`). Signs quotes. Never trusts the agent. |
| `c3` | Framework: Policy Engine, Interceptor, Baseline Store, Verifier, Alert Log, FastAPI, Streamlit dashboard. |

```
c1 proposes action
   -> c3 Interceptor
   -> c3 Policy Engine        (allow / block / review)
   -> [if sensitive] c3 Baseline Store integrity check
   -> c3 Verifier requests TPM quote from c2
   -> operator ALLOW/BLOCK    (dashboard or zenity)
   -> c3 Alert Log
```

## Usage

### Installing TrustEdge

```sh
git clone <this repo>
cd trustedge
cp .env.example .env
docker compose build
docker compose up
```

Note: don't skip `cp .env.example .env` — the framework won't find its
TPM socket or ports without it.

### Talking to the agent

```sh
docker attach trustedge-c1
task> write "hello" to /app/scratch/output.txt
```

### Reviewing and approving actions

Dashboard (audit log + pending ALLOW/BLOCK queue):

```
http://localhost:8501
```

Or from a desktop with a working X11 display, respond to the `zenity`
popup directly.

### Configuring everything

`trustedge-tricks.sh` is a single winetricks-style `zenity` control panel
for the whole project — live policy, pending approvals, `.env` runtime
settings, and the docker compose stack itself — categorized into one
menu, no container shell or hand-edited files required:

```sh
./tools/trustedge-tricks.sh
```

| Category | Covers |
|---|---|
| Live Policy | Allowed actions, action sensitivity, denied targets, critical files, approval timeout, raw `policy.json` — pushed through the admin API, effective immediately |
| Pending Approvals | Review and ALLOW/BLOCK actions waiting on a human |
| Runtime Settings | `.env`: Ollama model/host, TPM ports, framework/dashboard ports, DB path, approval timeout, X11 display |
| Stack Control | Start, stop, restart, rebuild (resets the baseline), status, per-container logs, open the dashboard, health check |

### API

```sh
curl http://localhost:8000/health
curl http://localhost:8000/policy
```

See [GUIDE.md](GUIDE.md) for prerequisites, detailed setup, and testing.

## Requirements

- Docker Engine and Docker Compose v2 (`docker compose ...`)
- Linux host (swtpm's TCP mode and X11 popups are the tested path)
- NVIDIA GPU + NVIDIA Container Toolkit, optional, for GPU-accelerated `c1`
- `zenity`, `curl`, and `jq` on the host, if you want to use `trustedge-tricks.sh`

## Repository layout

```
trustedge/
├── c1/        AI agent container (CLI)
├── c2/        TPM container
├── c3/        Framework container (policy, verifier, dashboard, tests)
└── tools/     Host-side zenity control panel (trustedge-tricks.sh)
```

## Acknowledgement

This project builds on [swtpm](https://github.com/stefanberger/swtpm) and
[libtpms](https://github.com/stefanberger/libtpms) (IBM Corporation,
3-Clause BSD) for TPM emulation, [tpm2-tools](https://github.com/tpm2-software/tpm2-tools)
for attestation, [Ollama](https://ollama.com) for local model serving, and
is built on [Arch Linux](https://archlinux.org/), whose components carry
their own respective open-source licenses.

## License

```
MIT License

Copyright (c) 2026 Surendra S

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
