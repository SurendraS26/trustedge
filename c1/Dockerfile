FROM archlinux:base

LABEL maintainer="Surendra S" \
      org.opencontainers.image.title="trustedge-c1" \
      org.opencontainers.image.description="TrustEdge AI Agent Container"

RUN pacman -Syu --noconfirm --needed \
        python \
        python-pip \
        curl \
        nvidia-utils \
    && pacman -Scc --noconfirm \
    && rm -rf /var/cache/pacman/pkg/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

VOLUME ["/root/.ollama"]

EXPOSE 11434

ENTRYPOINT ["./entrypoint.sh"]

