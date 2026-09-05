# ╔══════════════════════════════════════════════════════════════════════╗
# ║              TrustEdge — c3 Framework Container                       ║
# ║   Policy Engine · Integrity Monitor · Attestation Manager             ║
# ║   Verifier · Baseline Store · Interceptor · Alert System              ║
# ╚══════════════════════════════════════════════════════════════════════╝

FROM archlinux:base

LABEL maintainer="Surendra S" \
      org.opencontainers.image.title="trustedge-c3" \
      org.opencontainers.image.description="TrustEdge Framework Container"

RUN pacman -Syu --noconfirm --needed \
        python \
        python-pip \
        tpm2-tools \
        tpm2-tss \
        sqlite \
        audit \
        libnotify \
        zenity \
        libcanberra \
        xxd \
    && pacman -Scc --noconfirm \
    && rm -rf /var/cache/pacman/pkg/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
             scripts/setup_tpm.sh \
             interceptor/audit_rules.sh

# Directories for persistent data
RUN mkdir -p /app/baseline_store /app/alerts /app/tpm_keys

# /tmp/swtpm.sock  — shared volume with c2 (or TCP via env)
# /var/log/audit/  — mounted from host (read-only)

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
