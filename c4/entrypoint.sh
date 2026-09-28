#!/usr/bin/env bash
export DISPLAY=:1
RUNDIR=/tmp/runtime-trustedge

mkdir -p "$RUNDIR" /home/trustedge/.vnc
echo "${VNC_PASSWORD:-trustedge}" | vncpasswd -f > /home/trustedge/.vnc/passwd
chmod 600 /home/trustedge/.vnc/passwd
chmod 700 "$RUNDIR"
chown -R trustedge:trustedge "$RUNDIR" /home/trustedge/.vnc

echo "[c4] starting Xvnc"
su - trustedge -c "exec Xvnc :1 -geometry ${VNC_GEOMETRY:-1280x800} -depth 24 -rfbport 5901 -rfbauth /home/trustedge/.vnc/passwd -SecurityTypes VncAuth" > /tmp/xvnc.log 2>&1 &

for i in $(seq 1 30); do
    xdpyinfo -display :1 >/dev/null 2>&1 && break
    sleep 1
done

echo "[c4] starting XFCE4"
su - trustedge -c "export DISPLAY=:1 XDG_RUNTIME_DIR=$RUNDIR; exec dbus-run-session -- startxfce4" > /tmp/xfce.log 2>&1 &

echo "[c4] starting exec listener"
su - trustedge -c "export DISPLAY=:1 XDG_RUNTIME_DIR=$RUNDIR; cd /app && exec python exec_listener.py" > /tmp/exec_listener.log 2>&1 &

echo "[c4] desktop ready: http://localhost:6080/vnc.html (password: ${VNC_PASSWORD:-trustedge})"
exec /opt/novnc/utils/novnc_proxy --vnc localhost:5901 --listen 6080
