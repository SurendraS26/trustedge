FROM archlinux:latest

RUN pacman -Syu --noconfirm --needed \
    python python-pip \
    swtpm tpm2-tools tpm2-tss \
    sqlite curl \
    zenity gedit \
    pkgconf base-devel \
    && pacman -Scc --noconfirm

WORKDIR /app

COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/swtpm /app/audit
RUN chmod +x /app/swtpm/entrypoint.sh
RUN chmod +x /app/tools/trustedge-tricks.sh

EXPOSE 8000

ENTRYPOINT ["/app/swtpm/entrypoint.sh"]
