FROM archlinux:latest

# Base packages, GPU drivers/CUDA, Python, and Ollama.
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
        python \
        python-pip \
        nvidia-utils \
        cuda \
        curl \
        base-devel && \
    pacman -Scc --noconfirm

# Install Ollama (official install script, works on Arch).
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY Modelfile .
COPY main.py .
COPY executor.py .
COPY rag.py .
COPY ingest.py .
COPY data ./data

ENV OLLAMA_HOST=0.0.0.0:11434
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

EXPOSE 11434

# Start the Ollama server, pull/build the model, then run the agent loop.
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
