# TrustEdge

TrustEdge is a TPM-based security framework for AI agents. It intercepts every action an agent wants to take, checks it against policy, verifies integrity via TPM, and asks a human for final approval. The agent cannot bypass or approve its own actions.

## Contents

Docker edition: `docker-compose` installs everything automatically. {Recommended} 

Native edition: Scripts to install it on host to run trustedge.

## Usage

Installing trustedge on local device
```sh
git clone https://github.com/SurendraS26/trustedge.git
cd trustedge
docker compose build
docker compose up
```
> Note: There is a '.env' file which contain's environment variable's for container's

Launch AI agent in a new Terminal

```sh
docker attach trustedge-c1
task> write "It's Surendra here 😄🤞" to /app/scratch/misc.yml
```
> Note: Run this in a separate terminal window to interact with the agent.

Reviewing and approving actions

Audit dashboard: `http://localhost:8501`

> Note: You get a popup from `zenity` for sensitive actions — ALLOW to run, BLOCK to stop. No response in 30s = BLOCK.

Use your own documents to guide the Agent

```sh
cp <your.txt/md/pdf> trustedge/c1/data/
docker compose up
```
> Note: You drop files into `c1/data/` i,e `{txt,md,pdf}` — the agent automatically uses them for context.

TrustedgeTricks - Tinkering tool
```sh
./tools/trustedge-tricks.sh
```
> Note: One Zenity menu for everything — no terminal, no file edits.


## Requirements

My Gear
``` 
   Static hostname: loq
         Icon name: computer-laptop
           Chassis: laptop 💻
  Operating System: Arch Linux        
            Kernel: Linux 7.2.3-arch1-3
      Architecture: x86-64
   Hardware Vendor: Lenovo
    Hardware Model: LOQ 15IRX9
      Hardware SKU: LENOVO_MT_83DV_BU_idea_FM_LOQ 15IRX9
  Firmware Version: NECN50WW
     Firmware Date: Fri 2026-01-16
      Firmware Age: 7month 3w 2d
```
- Docker Engine + Docker Compose v2
- Linux host (swtpm's TCP mode and X11 popups are the tested path)
- `zenity`, `curl`, and `jq` on the host, for `trustedge-tricks.sh`
- NVIDIA GPU + NVIDIA Container Toolkit, for GPU-accelerated `c1`

> Warning: Use a GPU for running models or else you may end destroying your CPU.

## Acknowledgement

This project builds on [**swtpm**](https://github.com/stefanberger/swtpm) and [**libtpms**](https://github.com/stefanberger/libtpms) (IBM Corporation, 3-Clause BSD) for TPM emulation, [**tpm2-tools**](https://github.com/tpm2-software/tpm2-tools) for attestation, and [**Ollama**](https://ollama.com) for local model serving, and is built on [**Arch Linux**](https://archlinux.org/), whose components carry their own respective open-source licenses.


References
----------

- [swtpm-arch-docker](https://github.com/SurendraS26/swtpm-arch-docker) — SWTPM on Arch Linux, by Surendra S
- [swtpm-docker](https://github.com/danieltrick/swtpm-docker) — SWTPM Docker images, by Daniel Trick


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
