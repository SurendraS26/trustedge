FROM archlinux:latest
LABEL maintainer="SurendraS26" \
      org.opencontainers.image.title="trustedge-c3" \
      org.opencontainers.image.description="TPM-Assisted Secure Attestation Framework for AI Agents"
RUN pacman -Syu --noconfirm \
    python \
    python-pip \
    sqlite \
    zenity \
    && pacman -Scc --noconfirm
RUN pip install --break-system-packages \
    fastapi \
    uvicorn \
    streamlit \
    requests
WORKDIR /app
COPY requirements.txt .
RUN pip install --break--system-packages -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
EXPOSE 8000 8500
ENTRYPOINT ["./entrypoint.sh"] 
