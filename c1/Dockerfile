FROM archlinux:base

LABEL maintainer="Surendra S" \
      org.opencontainers.image.title="trustedge-c1" \
      org.opencontainers.image.description="TrustEdge AI Agent Container"

# ── System dependencies ───────────────────────────────────────────────────
RUN pacman -Syu --noconfirm --needed \
        python \
        python-pip \
        curl \
        nvidia-utils \
    && pacman -Scc --noconfirm \
    && rm -rf /var/cache/pacman/pkg/*

# ── Install Ollama ────────────────────────────────────────────────────────
RUN curl -fsSL https://ollama.com/install.sh | sh

# ── Python dependencies ───────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

# ── Copy agent source ─────────────────────────────────────────────────────
COPY . .
RUN chmod +x entrypoint.sh

# ── Ollama model storage ──────────────────────────────────────────────────
VOLUME ["/root/.ollama"]

# Ollama API port
EXPOSE 11434

ENTRYPOINT ["./entrypoint.sh"]

