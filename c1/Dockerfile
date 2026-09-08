FROM archlinux:latest

RUN pacman -Syu --noconfirm --needed \
    python python-pip curl ca-certificates git \
    && pacman -Scc --noconfirm

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 11434

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
