FROM archlinux:latest

RUN pacman -Syu --noconfirm --needed \
        xfce4 xfce4-terminal tigervnc xorg-fonts-misc xorg-xdpyinfo xorg-xauth \
        chromium dbus git python python-pip noto-fonts sudo inetutils zenity xfce4-appfinder && \
    rm -rf /var/cache/pacman/pkg/*

RUN pip install --break-system-packages --no-cache-dir websockify fastapi uvicorn

# noVNC browser client (not in Arch's official repos, so cloned directly)
RUN git clone --depth=1 https://github.com/novnc/noVNC.git /opt/novnc && \
    rm -rf /opt/novnc/.git

# dbus needs a machine-id or every app on the desktop fails to reach
# the message bus (Xfconf, notifications, session manager, etc).
RUN dbus-uuidgen --ensure && ln -sf /var/lib/dbus/machine-id /etc/machine-id

# Desktop user with passwordless sudo, so approved scripts can install packages.
RUN useradd -m -u 1000 trustedge && \
    echo "trustedge ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/trustedge && \
    chmod 440 /etc/sudoers.d/trustedge

# Chromium refuses to start inside a container without these flags.
RUN printf '#!/bin/sh\nexec /usr/bin/chromium --no-sandbox --disable-gpu --disable-dev-shm-usage "$@"\n' \
        > /usr/local/bin/chromium && chmod +x /usr/local/bin/chromium

WORKDIR /app
COPY exec_listener.py .

ENV VNC_GEOMETRY=1280x800
ENV VNC_PASSWORD=trustedge

# 6080: noVNC (published). 9000: exec listener (internal only, never published).
EXPOSE 6080 9000

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
