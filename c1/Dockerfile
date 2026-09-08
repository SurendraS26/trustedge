FROM archlinux:latest

LABEL maintainer="SurendraS26" \
      org.opencontainers.image.title="TrustEdge Agent" \
      org.opencontainers.image.description="AI Agent with Ollama"

RUN pacman -Syu --noconfirm \
    python \
    python-pip \
    curl \
    && pacman -Scc --noconfirm

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 11434

ENTRYPOINT ["./entrypoint.sh"]
