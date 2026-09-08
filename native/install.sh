#!/usr/bin/env bash
#
# TrustEdge - native installer (Arch Linux, no containers).
#
# Sets up swtpm, a Python venv per component, systemd --user services for
# the TPM/framework/dashboard, and pulls the Ollama models. Run once from
# a normal user account with sudo access; safe to re-run.
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NATIVE="$REPO/native"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "==> TrustEdge native install starting in $REPO"

if ! command -v pacman >/dev/null 2>&1; then
    echo "This installer targets Arch Linux (pacman not found). Aborting." >&2
    exit 1
fi

# ---------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------
echo "==> Installing system packages"
sudo pacman -Syu --needed --noconfirm \
    swtpm tpm2-tss tpm2-tools \
    python python-pip \
    sqlite zenity libnotify \
    base-devel curl jq

if command -v nvidia-smi >/dev/null 2>&1 || lspci 2>/dev/null | grep -qi nvidia; then
    echo "==> NVIDIA GPU detected, installing ollama-cuda"
    sudo pacman -S --needed --noconfirm ollama-cuda
else
    echo "==> No NVIDIA GPU detected, installing CPU-only ollama"
    sudo pacman -S --needed --noconfirm ollama
fi

echo "==> Enabling the Ollama system service"
sudo systemctl enable --now ollama

# ---------------------------------------------------------------------
# 2. .env
# ---------------------------------------------------------------------
if [[ ! -f "$REPO/.env" ]]; then
    echo "==> Writing $REPO/.env from native/native.env.example"
    sed "s|__HOME__|$HOME|g" "$NATIVE/native.env.example" > "$REPO/.env"
else
    echo "==> $REPO/.env already exists, leaving it as-is"
fi
set -a
source "$REPO/.env"
set +a

# ---------------------------------------------------------------------
# 3. Python venvs
# ---------------------------------------------------------------------
echo "==> Setting up c1 (agent) venv"
python -m venv "$REPO/c1/.venv"
"$REPO/c1/.venv/bin/pip" install --upgrade pip --quiet
"$REPO/c1/.venv/bin/pip" install -r "$REPO/c1/requirements.txt" --quiet

echo "==> Setting up c3 (framework) venv"
python -m venv "$REPO/c3/.venv"
"$REPO/c3/.venv/bin/pip" install --upgrade pip --quiet
"$REPO/c3/.venv/bin/pip" install -r "$REPO/c3/requirements.txt" --quiet

# ---------------------------------------------------------------------
# 4. Data directories
# ---------------------------------------------------------------------
mkdir -p "$HOME/.local/share/trustedge/tpm-state" "$HOME/.local/share/trustedge/data"

# ---------------------------------------------------------------------
# 5. systemd --user units
# ---------------------------------------------------------------------
echo "==> Installing systemd --user services"
mkdir -p "$SYSTEMD_USER_DIR"
cp "$NATIVE/trustedge-tpm.service" "$SYSTEMD_USER_DIR/"
sed "s|__REPO__|$REPO|g" "$NATIVE/trustedge-framework.service" > "$SYSTEMD_USER_DIR/trustedge-framework.service"
sed "s|__REPO__|$REPO|g" "$NATIVE/trustedge-dashboard.service" > "$SYSTEMD_USER_DIR/trustedge-dashboard.service"

chmod +x "$NATIVE"/start-framework.sh "$NATIVE"/start-dashboard.sh "$NATIVE"/run-agent.sh
chmod +x "$REPO/tools/trustedge-tricks.sh"

systemctl --user daemon-reload

# Let user services keep running after the terminal/session that enabled
# them closes (not after full logout, but covers normal desktop use).
loginctl enable-linger "$USER" 2>/dev/null || true

echo "==> Starting trustedge-tpm, trustedge-framework, trustedge-dashboard"
systemctl --user enable --now trustedge-tpm.service
sleep 2
systemctl --user enable --now trustedge-framework.service
sleep 2
systemctl --user enable --now trustedge-dashboard.service

# ---------------------------------------------------------------------
# 6. Ollama models
# ---------------------------------------------------------------------
echo "==> Pulling Ollama models (this can take a while on first run)"
ollama pull "${OLLAMA_MODEL:-qwen2.5:3b}"
ollama pull "${EMBED_MODEL:-mxbai-embed-large}"

echo "==> Building the trustedge-agent model from c1/Modelfile"
ollama create trustedge-agent -f "$REPO/c1/Modelfile"

echo
echo "==> Done."
echo "    Framework API: http://127.0.0.1:${FRAMEWORK_PORT:-8000}"
echo "    Dashboard:     http://127.0.0.1:${DASHBOARD_PORT:-8501}"
echo
echo "    Talk to the agent:      $NATIVE/run-agent.sh"
echo "    Configure everything:   $REPO/tools/trustedge-tricks.sh"
echo "    Check service status:   systemctl --user status trustedge-tpm trustedge-framework trustedge-dashboard"
