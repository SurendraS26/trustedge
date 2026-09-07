FROM archlinux:latest

RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
        python \
        python-pip \
        sqlite \
        zenity \
        libnotify \
        tpm2-tss \
        tpm2-tools \
        curl \
        gcc \
        pkgconf && \
    pacman -Scc --noconfirm

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x scripts/setup_tpm.sh

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000 8501

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
