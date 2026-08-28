FROM ubuntu:24.04
RUN apt-get update && apt-get install -y swtpm swtpm-tools tpm2-tools && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/lib/swtpm-state
EXPOSE 2321 2322
ENTRYPOINT ["swtpm", "socket", \
  "--tpmstate", "dir=/var/lib/swtpm-state", \
  "--ctrl", "type=tcp,port=2322", \
  "--server", "type=tcp,port=2321", \
  "--flags", "not-need-init", \
  "--tpm2", "--log", "level=1"]
