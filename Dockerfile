# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# Arch Linux version — swtpm installed directly from pacman (no source build) #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
###################### A cOmmIt cAn nEvEr bE fAkEd ############################
FROM archlinux:base

RUN pacman -Syu --noconfirm --needed swtpm tpm2-tss && \
    pacman -Scc --noconfirm && \
    rm -rf /var/cache/pacman/pkg/* /var/lib/pacman/sync/*

RUN mkdir -p /var/lib/swtpm/tpmstate

ENTRYPOINT ["/usr/bin/swtpm"]
CMD ["socket", "--tpm2", \
    "--server", "type=tcp,port=2321,bindaddr=0.0.0.0", \
    "--ctrl",   "type=tcp,port=2322,bindaddr=0.0.0.0", \
    "--flags", "not-need-init", \
    "--tpmstate", "dir=/var/lib/swtpm/tpmstate"]
