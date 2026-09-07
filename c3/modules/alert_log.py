"""
Alert Log

Two responsibilities:
  1. Persist every evaluated action (allowed, blocked, or reviewed) to a
     SQLite audit log that the Streamlit dashboard reads from.
  2. For sensitive actions, show the operator a desktop popup with the
     action, target, and reasoning, and ALLOW/BLOCK buttons with a 30s
     timeout. Uses Zenity when an X11 display is available, and falls back
     to a plain notify-send notification (informational only, no
     interactive response) otherwise.
"""

import logging
import os
import shutil
import sqlite3
import subprocess
import time

log = logging.getLogger("alert_log")

DB_PATH = os.environ.get("SQLITE_PATH", "/data/trustedge.db")
POPUP_TIMEOUT_SECONDS = 30

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    reasoning TEXT,
    classification TEXT,
    attested TEXT,
    final_decision TEXT NOT NULL,
    reason TEXT
);
"""


class AlertLog:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def record(self, action, target, reasoning, classification, attested, final_decision, reason):
        self.conn.execute(
            """
            INSERT INTO audit_log
                (timestamp, action, target, reasoning, classification, attested, final_decision, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                time.time(),
                action,
                target,
                reasoning,
                classification,
                str(attested),
                final_decision,
                reason,
            ),
        )
        self.conn.commit()
        log.info("audit entry recorded: action=%s decision=%s", action, final_decision)

    def _zenity_available(self):
        return bool(os.environ.get("DISPLAY")) and shutil.which("zenity") is not None

    def _notify_send_available(self):
        return shutil.which("notify-send") is not None

    def prompt_operator(self, action, target, reasoning):
        """
        Ask the operator to ALLOW or BLOCK a sensitive action.

        Returns "ALLOW", "BLOCK", or None (no human response available or
        the popup timed out, meaning the automated decision stands).
        """
        message = f"Action: {action}\nTarget: {target}\nReasoning: {reasoning}"

        if self._zenity_available():
            return self._prompt_zenity(message)

        if self._notify_send_available():
            self._notify_send(message)
            log.info("no X11 display, sent notify-send notification only (no interactive override)")
            return None

        log.warning("no zenity and no notify-send available, skipping desktop popup")
        return None

    def _prompt_zenity(self, message):
        cmd = [
            "zenity", "--question",
            "--title=TrustEdge Alert",
            f"--text={message}",
            "--ok-label=ALLOW",
            "--cancel-label=BLOCK",
            f"--timeout={POPUP_TIMEOUT_SECONDS}",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            log.warning("zenity binary disappeared mid-call, falling back to notify-send")
            if self._notify_send_available():
                self._notify_send(message)
            return None

        if result.returncode == 0:
            log.info("operator chose ALLOW via zenity")
            return "ALLOW"
        if result.returncode == 1:
            log.info("operator chose BLOCK via zenity")
            return "BLOCK"
        if result.returncode == 5:
            log.info("zenity popup timed out after %ds, no operator response", POPUP_TIMEOUT_SECONDS)
            return None

        log.warning("zenity exited with unexpected code %d", result.returncode)
        return None

    def _notify_send(self, message):
        try:
            subprocess.run(
                ["notify-send", "TrustEdge Alert", message],
                capture_output=True, text=True, timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            log.warning("notify-send failed: %s", exc)

    def recent_entries(self, limit=200):
        cur = self.conn.execute(
            """
            SELECT id, timestamp, action, target, reasoning, classification,
                   attested, final_decision, reason
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
