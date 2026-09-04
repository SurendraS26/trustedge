FROM archlinux:base
RUN pacman -Syu --noconfirm --needed swtpm tpm2-tss && \
    pacman -Scc --noconfirm && \
    rm -rf /var/cache/pacman/pkg/* /var/lib/pacman/sync/*
RUN mkdir -p /var/lib/swtpm/tpmstate
COPY start.sh .
CMD ["chmod 777 start.sh"]
ENTRYPOINT ["./start.sh"]

