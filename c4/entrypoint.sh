#!/usr/bin/env bash
set -e

# Hyprland refuses to run as root, so the runtime dir it needs has to
# be owned by the non-root user before anything starts as that user.
mkdir -p "$XDG_RUNTIME_DIR"
chown trustedge:trustedge "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

echo "[c4] starting hyprland (headless) as trustedge"
su - trustedge -c "export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=$WAYLAND_DISPLAY WLR_BACKENDS=$WLR_BACKENDS; exec dbus-run-session -- Hyprland" > /tmp/hyprland.log 2>&1 &

for i in $(seq 1 30); do
    if [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then
        break
    fi
    sleep 1
done

echo "[c4] starting wayvnc as trustedge"
# NOTE: wayvnc runs unauthenticated here (no VNC password). It is only
# reachable inside trustedge-network, not published to the host beyond
# the noVNC bridge on 6080 - see SETUP.md for the tradeoff this makes.
su - trustedge -c "export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=$WAYLAND_DISPLAY; exec wayvnc 0.0.0.0 5900" > /tmp/wayvnc.log 2>&1 &

for i in $(seq 1 30); do
    if (echo > /dev/tcp/127.0.0.1/5900) 2>/dev/null; then
        break
    fi
    sleep 1
done

echo "[c4] starting exec listener on :9000 as trustedge"
su - trustedge -c "export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=$WAYLAND_DISPLAY; cd /app && exec python exec_listener.py" > /tmp/exec_listener.log 2>&1 &

echo "[c4] starting noVNC on :6080"
exec /opt/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 6080

