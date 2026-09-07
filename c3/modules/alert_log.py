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

import json
import logging
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid

log = logging.getLogger("alert_log")

DB_PATH = os.environ.get("SQLITE_PATH", "/data/trustedge.db")
POLICY_PATH = os.environ.get(
    "TRUSTEDGE_POLICY_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "policy.json"),
)
DEFAULT_POPUP_TIMEOUT_SECONDS = 30
POLL_INTERVAL_SECONDS = 0.5


def _current_popup_timeout():
    try:
        with open(POLICY_PATH, "r") as f:
            return int(json.load(f).get("popup_timeout_seconds", DEFAULT_POPUP_TIMEOUT_SECONDS))
    except (OSError, ValueError, TypeError):
        return DEFAULT_POPUP_TIMEOUT_SECONDS

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

CREATE TABLE IF NOT EXISTS pending_approvals (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    reasoning TEXT,
    decision TEXT
);
"""


class AlertLog:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.executescript(SCHEMA)
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

    def create_pending(self, action, target, reasoning):
        approval_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO pending_approvals (id, created_at, action, target, reasoning, decision) "
            "VALUES (?, ?, ?, ?, ?, NULL)",
            (approval_id, time.time(), action, target, reasoning),
        )
        self.conn.commit()
        return approval_id

    def resolve_pending(self, approval_id, decision):
        """Called by the dashboard (or any client) when a human clicks ALLOW/BLOCK."""
        assert decision in ("ALLOW", "BLOCK")
        self.conn.execute(
            "UPDATE pending_approvals SET decision = ? WHERE id = ? AND decision IS NULL",
            (decision, approval_id),
        )
        self.conn.commit()

    def peek_pending_decision(self, approval_id):
        cur = self.conn.execute(
            "SELECT decision FROM pending_approvals WHERE id = ?", (approval_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def list_unresolved_pending(self):
        cur = self.conn.execute(
            "SELECT id, created_at, action, target, reasoning FROM pending_approvals "
            "WHERE decision IS NULL ORDER BY created_at ASC"
        )
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def _zenity_available(self):
        return bool(os.environ.get("DISPLAY")) and shutil.which("zenity") is not None

    def _notify_send_available(self):
        return shutil.which("notify-send") is not None

    def prompt_operator(self, action, target, reasoning):
        """
        Ask the operator to ALLOW or BLOCK a sensitive action.

        Two channels race for a response:
          1. A row in `pending_approvals` that the Streamlit dashboard shows
             with ALLOW/BLOCK buttons - works from any browser, no X11
             needed. This is the reliable path when calling the framework
             from the web agent.
          2. A local zenity popup, best-effort, for anyone with a desktop
             session and a reachable X11 display attached to this container.

        Returns "ALLOW", "BLOCK", or None (no response within the timeout,
        meaning the automated decision stands).
        """
        approval_id = self.create_pending(action, target, reasoning)
        log.info(
            "pending approval %s created for %s %s - open the dashboard "
            "(:8501) to ALLOW/BLOCK it, or respond to the desktop popup if one appears",
            approval_id, action, target,
        )

        message = f"Action: {action}\nTarget: {target}\nReasoning: {reasoning}"
        if self._zenity_available():
            threading.Thread(
                target=self._prompt_zenity_into_pending,
                args=(message, approval_id),
                daemon=True,
            ).start()
        elif self._notify_send_available():
            self._notify_send(message)
            log.info("no X11 display, sent notify-send notification only (no interactive override)")

        timeout_seconds = _current_popup_timeout()
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            decision = self.peek_pending_decision(approval_id)
            if decision is not None:
                log.info("operator chose %s (approval %s)", decision, approval_id)
                return decision
            time.sleep(POLL_INTERVAL_SECONDS)

        log.info("no operator response within %ds for approval %s", timeout_seconds, approval_id)
        return None

    def _prompt_zenity_into_pending(self, message, approval_id):
        """Runs in a background thread; writes a zenity result into the same
        pending row the web dashboard can also resolve, first writer wins."""
        decision = self._prompt_zenity(message)
        if decision is not None:
            self.resolve_pending(approval_id, decision)

    def _prompt_zenity(self, message):
        timeout_seconds = _current_popup_timeout()
        cmd = [
            "zenity", "--question",
            "--title=TrustEdge Alert",
            f"--text={message}",
            "--ok-label=ALLOW",
            "--cancel-label=BLOCK",
            f"--timeout={timeout_seconds}",
        ]
        start = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            log.warning("zenity binary disappeared mid-call, falling back to notify-send")
            if self._notify_send_available():
                self._notify_send(message)
            return None
        elapsed = time.time() - start

        # zenity returns the SAME exit code (1) both when the operator clicks
        # "BLOCK" and when it fails to even open a window (e.g. DISPLAY is
        # set but the X server refused the connection because `xhost` was
        # never run on the host). A real click takes human-scale time and
        # produces no stderr; a failed connection returns almost instantly
        # and logs a GTK/X11 error. Treat the latter as "no response", not
        # as an operator decision, so a broken display can't get silently
        # read as a security-relevant BLOCK.
        looks_like_display_failure = elapsed < 1.0 or bool(result.stderr.strip())
        if result.returncode == 1 and looks_like_display_failure:
            log.warning(
                "zenity exited 1 after %.2fs with stderr=%r - popup likely never "
                "displayed (is DISPLAY reachable? try `xhost +local:docker` on "
                "the host). Treating as no operator response, not BLOCK.",
                elapsed, result.stderr.strip(),
            )
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
            log.info("zenity popup timed out after %ds, no operator response", timeout_seconds)
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
