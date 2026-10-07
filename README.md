![TrustEdge Bare/Box Edition Logo](etc/banner.png)

TrustEdge - Bare/Box Edition
===========

TrustEdge is a TPM-based security framework for AI agents. It intercepts every action an agent wants to take, checks it against policy, verifies attestation via a TPM quote, and asks a human for final approval. The agent cannot bypass or approve its own actions, approved scripts run only inside an isolated desktop sandbox.

Usage
-----

Installing TrustEdge Bare/Box Edition
```sh
git clone https://github.com/SurendraS26/trustedge.git
cd trustedge
docker compose build
docker compose up
```
> Note: On first run `c1` downloads the model and is stored in the `trustedge-ollama` volume, wait for it to be ready. 


Launch AI agent in new terminal: 

```sh
./scripts/agent.sh
> open chromium and play favourite music on youtube
```
> Note: Run this in a separate terminal window to interact with the agent. `Ctrl-C` only closes the prompt, the containers keep running. Type `q` to quit.


Sandbox Desktop using [`noVNC`](https://github.com/novnc/noVNC):
```sh
<Your-Web-browser> http://localhost:6080/vnc.html
```
> Note: Vnc password - `trustedge` , Port - `6080` and approved scripts run inside the desktop


Audit dashboard using [`glow`](https://github.com/charmbracelet/glow): 
```sh
./scripts/dashboard.sh
```


Decision Logs JSON:
```sh
<Your-Web-browser> http://localhost:8000/log
```


System Stats:
- TPM PCR live view - `tpm-view`
- GPU stats - `gpu-view`
- Top - `top-view`
```sh
./scripts/<?-view>.sh
```
>`tpm-view.sh` host-side needs `tpm2-tools` and port `2321` from `trustedge-c2`. 
> <br>
>`gpu-view.sh` needs host `nvidia-smi` Nvidia GPU's.
> <br>
>`top-view` is top tool for sandbox environment. `q` to quit.

Architecture Diagram
--------------------
<div align="center">

```mermaid
flowchart LR
    U([User]) --> A[c1 · Agent] --> P{c3 · Policy} --> T{c2 · TPM quote} --> H{Human approval} --> S[c4 · Sandbox]
    P & T & H -.->|fail / reject| D[Deny]
```

</div>

My Workstation Specs
--------------------
<table>
  <tr><td>OS</td><td>Arch Linux x86_64</td></tr>
  <tr><td>WM</td><td>Hyprland</td></tr>
  <tr><td>CPU</td><td>Intel Core i7-14700HX (16+12) @ 5.50 GHz</td></tr>
  <tr><td>GPU 1</td><td>NVIDIA GeForce RTX 4060 Max-Q / Mobile</td></tr>
  <tr><td>GPU 2</td><td>Intel Raptor Lake-S UHD Graphics @ 1.60 GHz</td></tr>
  <tr><td>Memory</td><td>15.32 GiB</td></tr>
  <tr><td>Disk</td><td>937.73 GiB</td></tr>
</table>

Requirements
------------
- Host Machine - Linux distro's
- Docker Engine + Docker Compose v2
- TPM2 tools `tpm2-tools` and `nvidia-smi` for Nvidia GPU
- NVIDIA GPU + NVIDIA Container Toolkit, for GPU-accelerated `c1`

> Warning: Use a GPU for running models.

Acknowledgement
---------------

This project builds on [**swtpm**](https://github.com/stefanberger/swtpm) and [**libtpms**](https://github.com/stefanberger/libtpms) (IBM Corporation, 3-Clause BSD) for TPM emulation, [**tpm2-tools**](https://github.com/tpm2-software/tpm2-tools) for attestation, and [**Ollama**](https://ollama.com) for local model serving, and is built on [**Arch Linux**](https://archlinux.org/), whose components carry their own respective open-source licenses.


References
----------

- [swtpm-arch-docker](https://github.com/SurendraS26/swtpm-arch-docker) — SWTPM on Arch Linux, by Surendra S
- [swtpm-docker](https://github.com/danieltrick/swtpm-docker) — SWTPM Docker images, by Daniel Trick
- [Ollama AI agent](https://www.cloudvyn.com/blog/local-ai-agent-python-ollama-langchain-rag) — Build AI agent using Ollama, by Abhishek Madoliya
- [Ollama Docs](https://docs.ollama.com/linux) — Ollama documentation for Linux.


License
-------

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
