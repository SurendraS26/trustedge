FROM archlinux:base

RUN pacman -Syu --noconfirm --needed \
        python python-pip tpm2-tools tpm2-tss \
        sqlite audit libnotify zenity xxd \
    && pacman -Scc --noconfirm \
    && rm -rf /var/cache/pacman/pkg/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh scripts/setup_tpm.sh interceptor/audit_rules.sh
RUN mkdir -p /app/tpm_keys /app/baseline_store /app/alerts

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
