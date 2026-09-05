"""
TrustEdge — Baseline Store
SQLite-backed storage for:
  - Trusted SHA-256 file hashes  (recorded once at init time)
  - Trusted PCR values           (recorded once at init time)

Populated by scripts/init_baseline.py on a known-clean system.
Read on every attestation event by the Integrity Monitor and Verifier.
"""

import hashlib
import logging
import os
import sqlite3

log = logging.getLogger("trustedge.baseline")

DB_PATH = os.environ.get("BASELINE_DB", "/app/baseline_store/baseline.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                path        TEXT PRIMARY KEY,
                sha256      TEXT NOT NULL,
                recorded_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pcr_baselines (
                pcr_index   TEXT PRIMARY KEY,
                pcr_value   TEXT NOT NULL,
                recorded_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    log.info(f"Baseline DB initialised at {DB_PATH}")


# ── File hash operations ──────────────────────────────────────────────────

def record_baseline_hash(path: str, sha256: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO file_hashes (path, sha256) VALUES (?, ?)",
            (path, sha256.lower())
        )
        conn.commit()


def get_baseline_hash(path: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT sha256 FROM file_hashes WHERE path = ?", (path,)
        ).fetchone()
    return row["sha256"] if row else None


# ── PCR baseline operations ───────────────────────────────────────────────

def record_baseline_pcr(pcr_index: str, pcr_value: str) -> None:
    normalised = pcr_value.lower().lstrip("0x") or "0"
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pcr_baselines (pcr_index, pcr_value) VALUES (?, ?)",
            (str(pcr_index), normalised)
        )
        conn.commit()


def get_baseline_pcr(pcr_index: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT pcr_value FROM pcr_baselines WHERE pcr_index = ?",
            (str(pcr_index),)
        ).fetchone()
    return row["pcr_value"] if row else None


# ── Initialisation ────────────────────────────────────────────────────────

def hash_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, PermissionError):
        return None


def initialise_baseline(file_paths: list[str], pcr_values: dict[str, str]) -> None:
    """
    Populates the baseline store.
    Run once on a known-clean system before starting the framework.
    """
    init_db()

    for path in file_paths:
        h = hash_file(path)
        if h:
            record_baseline_hash(path, h)
            log.info(f"Baseline recorded: {path} = {h}")
        else:
            log.warning(f"Could not hash: {path} — skipped")

    for pcr_index, pcr_value in pcr_values.items():
        record_baseline_pcr(pcr_index, pcr_value)
        log.info(f"Baseline PCR recorded: PCR {pcr_index} = {pcr_value}")
