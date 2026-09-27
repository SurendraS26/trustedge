FROM archlinux:latest
RUN pacman -Syu --noconfirm --needed \
        hyprland xorg-xwayland wayvnc \
        foot mako rofi pcmanfm chromium \
        dbus git python python-pip noto-fonts sudo && \
    pacman -Scc --noconfirm
RUN pip install --break-system-packages --no-cache-dir websockify fastapi uvicorn pydantic
RUN git clone --depth=1 https://github.com/novnc/noVNC.git /opt/novnc && \
    rm -rf /opt/novnc/.git
RUN useradd -m -u 1000 -G video,input trustedge
RUN git clone --depth=1 https://github.com/SurendraS26/dotfiles.git /home/trustedge/dotfiles && \
    rm -rf /home/trustedge/dotfiles/.git && \
    chown -R trustedge:trustedge /home/trustedge
RUN su - trustedge -c "cd ~/dotfiles && chmod +x install-files.sh && ./install-files.sh"
WORKDIR /app
COPY exec_listener.py .
ENV XDG_RUNTIME_DIR=/run/user/1000
ENV WAYLAND_DISPLAY=wayland-1
ENV WLR_BACKENDS=headless
ENV VNC_PASSWORD=trustedge
EXPOSE 6080 9000
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

