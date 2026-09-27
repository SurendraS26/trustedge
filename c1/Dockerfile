FROM archlinux:latest
RUN echo "[c1] Installing requirements"
RUN pacman -Syu --noconfirm --needed \
    python python-pip curl base-devel && \
    pacman -Scc --noconfirm
RUN echo "[c1] Installing ollama"
RUN curl -fsSL https://ollama.com/install.sh | sh
WORKDIR /app
COPY requirements.txt .
RUN echo "[c1] Installing python requirements"
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt
COPY agent.py .
ENV OLLAMA_HOST=0.0.0.0:11434
EXPOSE 11434
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
RUN echo "[c1] Booting container"
ENTRYPOINT ["./entrypoint.sh"]


