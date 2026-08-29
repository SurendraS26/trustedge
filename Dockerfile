FROM archlinux:base

RUN pacman -Syu --noconfirm --needed swtpm tpm2-tools tpm2-tss && \
    pacman -Scc --noconfirm

RUN mkdir -p /var/lib/swtpm-state
EXPOSE 2321 2322

ENTRYPOINT ["swtpm", "socket", \
  "--tpmstate", "dir=/var/lib/swtpm-state", \
  "--ctrl", "type=tcp,port=2322", \
  "--server", "type=tcp,port=2321", \
  "--flags", "not-need-init", \
  "--tpm2", "--log", "level=1"]
