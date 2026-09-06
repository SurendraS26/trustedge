import os
import sqlite3
import subprocess
from datetime import datetime

DB          = os.environ.get("AUDIT_DB", "/app/alerts/audit.db")
HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def get_conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action    TEXT,
            target    TEXT,
            reason    TEXT
        )
    """)
    c.commit()
    return c


def write_alert(action, target, reason):
    ts = datetime.now().isoformat()

    with get_conn() as c:
        c.execute("INSERT INTO log (timestamp,action,target,reason) VALUES (?,?,?,?)",
                  (ts, action, target, reason))
        c.commit()

    print(f"[ALERT] {ts} | {action} -> {target} | {reason}")

    if HAS_DISPLAY:
        title = "TrustEdge — Blocked"
        msg   = f"Action: {action}\nTarget: {target}\nReason: {reason}"
        try:
            subprocess.Popen(["notify-send", "--urgency=critical", title, msg])
        except Exception:
            pass
        try:
            subprocess.Popen(["zenity", "--warning", f"--title={title}", f"--text={msg}"])
        except Exception:
            pass
