# trustedge - tools and packages

### C1 - Agent + Framework
- `python`
- `ollama`
- `ollama-cuda` 
- `python-requests`
- `python-fastapi`
- `python-yaml`
- `python-cryptography`
- `python-tpm2-pytss`
- `tpm2-tools`
- `sqlite`
- `docker`

> Note: Qwen2.5-3B / Llama3.2-3B LLM's to be pulled via Ollama.

### C2 - swtpm-arch-docker - ***SurendraS26***

<details>
  <summary>Link here</summary>
https://github.com/SurendraS26/swtpm-arch-docker
</details>

  - `docker`
  - `linux`
  - `linux-firmware`
  - `base`
  - `swtpm`
  - `tpm2-tools`
  - `tpm2-tss`
> Note: No need to build this , refer the above github link 'swtpm-arch-docker'

### On Host Machine
- `audit` (provides `auditd`)
- `python`
- `docker`
- `docker-compose`
- `docker-buildx`
- `xz`
- `coreutils` (provides `sha256sum`)

> Unix domain sockets and TCTI are kernel/library features, not standalone packages — TCTI comes bundled with `tpm2-tss`.

### Optional but good for version control
- `git`
- `github-cli` (provides `gh`)

> GitHub and GitHub Actions are hosted services, not pacman packages.