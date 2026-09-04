import os
import sqlite3
import subprocess
from datetime import datetime

AUDIT_DB = os.environ.get("AUDIT_DB", "/app/alerts/audit.db")


# ── Database ──────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(AUDIT_DB)


def _init_audit_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                action      TEXT    NOT NULL,
                target      TEXT    NOT NULL,
                reason      TEXT    NOT NULL
            )
        """)
        conn.commit()


# ── Desktop alert helpers ─────────────────────────────────────────────────

def _notify_send(title: str, message: str) -> None:
    subprocess.Popen([
        "notify-send",
        "--urgency=critical",
        "--icon=dialog-warning",
        title,
        message
    ])


def _zenity_alert(title: str, message: str) -> None:
    subprocess.Popen([
        "zenity",
        "--warning",
        f"--title={title}",
        f"--text={message}",
        "--width=400"
    ])


def _play_alert_sound() -> None:
    subprocess.Popen([
        "canberra-gtk-play",
        "--id=dialog-warning",
        "--description=TrustEdge alert"
    ])


# ── Public interface ──────────────────────────────────────────────────────

def write_alert(action: str, target: str, reason: str) -> None:
    """
    Called by the framework on every Deny decision.
    Writes to the SQLite audit log and triggers all three desktop alerts.
    """
    _init_audit_db()

    timestamp = datetime.now().isoformat()

    # 1. SQLite audit log
    with _connect() as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp, action, target, reason) VALUES (?, ?, ?, ?)",
            (timestamp, action, target, reason)
        )
        conn.commit()

    print(f"[ALERT] {timestamp} | action={action} target={target} reason={reason}")

    # 2. Desktop notifications (non-blocking, fire-and-forget)
    alert_title   = "TrustEdge — Action Blocked"
    alert_message = f"Action: {action}\nTarget: {target}\nReason: {reason}"

    _notify_send(alert_title, alert_message)
    _zenity_alert(alert_title, alert_message)
    _play_alert_sound()

