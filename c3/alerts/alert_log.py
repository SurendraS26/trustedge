"""
TrustEdge — Alert System
On every Deny event:
  1. Write permanent entry to SQLite audit log     (always)
  2. notify-send desktop notification              (if DISPLAY is set)
  3. zenity blocking dialog                        (if DISPLAY is set)
  4. canberra-gtk-play alert sound                 (if DISPLAY is set)

If no display is available (e.g. headless container), items 2-4 are
skipped gracefully — the SQLite log is always written regardless.
"""

import logging
import os
import sqlite3
import subprocess
from datetime import datetime

log = logging.getLogger("trustedge.alerts")

AUDIT_DB   = os.environ.get("AUDIT_DB",  "/app/alerts/audit.db")
HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(AUDIT_DB), exist_ok=True)
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


def _notify_send(title: str, message: str) -> None:
    try:
        subprocess.Popen(
            ["notify-send", "--urgency=critical", "--icon=dialog-warning", title, message],
            env=os.environ
        )
    except FileNotFoundError:
        log.debug("notify-send not available")


def _zenity_alert(title: str, message: str) -> None:
    try:
        subprocess.Popen(
            ["zenity", "--warning", f"--title={title}", f"--text={message}", "--width=400"],
            env=os.environ
        )
    except FileNotFoundError:
        log.debug("zenity not available")


def _play_sound() -> None:
    try:
        subprocess.Popen(
            ["canberra-gtk-play", "--id=dialog-warning", "--description=TrustEdge alert"],
            env=os.environ
        )
    except FileNotFoundError:
        log.debug("canberra-gtk-play not available")


def write_alert(action: str, target: str, reason: str) -> None:
    """
    Called on every Deny decision.
    Always writes to the SQLite audit log.
    Fires desktop alerts only if a display is available.
    """
    _init_audit_db()

    timestamp = datetime.now().isoformat()

    # 1. SQLite audit log — always
    with _connect() as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp, action, target, reason) VALUES (?, ?, ?, ?)",
            (timestamp, action, target, reason)
        )
        conn.commit()

    log.warning(f"ALERT | {timestamp} | action={action} target={target} reason={reason}")

    # 2-4. Desktop alerts — only if display is available
    if HAS_DISPLAY:
        title   = "TrustEdge — Action Blocked"
        message = f"Action:  {action}\nTarget:  {target}\nReason:  {reason}"
        _notify_send(title, message)
        _zenity_alert(title, message)
        _play_sound()
    else:
        log.info("No display found — desktop alerts skipped (audit log written)")
