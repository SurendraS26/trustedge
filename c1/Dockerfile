FROM archlinux:latest

RUN pacman -Syu --noconfirm --needed \
        python python-pip curl zstd pciutils base-devel && \
    rm -rf /var/cache/pacman/pkg/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY agent.py .

# GPU access: also needs `--gpus all` at run time and the NVIDIA
# Container Toolkit on the host (see SETUP.md).
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_KEEP_ALIVE=30m
EXPOSE 11434

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
