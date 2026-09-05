FROM archlinux:base
LABEL maintainer="Surendra S" \
      org.opencontainers.image.title="trustedge-c3" \
      org.opencontainers.image.description="TrustEdge Framwork Container"
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
WORKDIR /stuff
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh \
             scripts/setup_tpm.sh \
	     interceptor/audit_rules.sh
RUN mkdir -p /stuff/baseline_store /stuff/alerts /app/tpm_keys
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

