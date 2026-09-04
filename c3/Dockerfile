FROM archlinux:base

LABEL maintainer="Surendra S"

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
	pkg-config \
	gcc \
	make \
    && pacman -Scc --noconfirm \
    && rm -rf /var/cache/pacman/pkg/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh interceptor/audit_rules.sh

# /tpm/swtpm.sock - shared volume with c2
# /var/log/audit/ - mounted from host (read-only)

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

