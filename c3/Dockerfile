FROM archlinux:base
RUN pacman -Syu --noconfirm --needed \
        python python-pip sqlite tpm2-tss tpm2-tools curl gcc pkgconf \
        glow entr && \
    pacman -Scc --noconfirm
WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 8000
RUN chmod +x entrypoint.sh dashboard.sh
ENTRYPOINT ["./entrypoint.sh"]

