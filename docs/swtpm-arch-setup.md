# swtpm on ARCH Linux (Docker) - Setup and Testing documentation

## Dockerfile

I use Arch btw , so it's the base for 'swtpm' installed directly from the pacman repo 
NO SOURCE BUILD !!

```Dockerfile
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
```

## Build and Run the container

### Build the container
```bash
docker build -t swtpm-arch .
```
### Run the container
```bash
docker run -d --name swtpm-arch -p 2321:2321 -p 2322:2322 -v swtpm-arch-state:/var/lib/swtpm/tpmstate swtpm-arch
```

## For testing install the tpm2-tools on the host (I use Arch btw)
```bash
sudo pacman -Syu --needed tpm2-tools tpm2-tss
```


