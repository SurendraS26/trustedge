FROM archlinux:latest

RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
        swtpm \
        tpm2-tss \
        tpm2-tools \
        iproute2 && \
    pacman -Scc --noconfirm

RUN mkdir -p /var/lib/swtpm

VOLUME ["/var/lib/swtpm"]

EXPOSE 2321 2322

# --tpmstate persists NVRAM/keys to the mounted volume so the TPM survives
# container restarts. --server/--ctrl listen over TCP so c3 can reach this
# TPM across the docker network (a unix socket cannot cross containers).
ENTRYPOINT ["swtpm", "socket", \
    "--tpmstate", "dir=/var/lib/swtpm", \
    "--ctrl", "type=tcp,port=2322,bindaddr=0.0.0.0", \
    "--server", "type=tcp,port=2321,bindaddr=0.0.0.0", \
    "--tpm2", \
    "--flags", "startup-clear", \
    "--log", "level=1"]
