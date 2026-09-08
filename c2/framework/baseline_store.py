import sqlite3
import os
from framework.integrity_monitor import measure_all

DB_PATH = os.path.join(os.path.dirname(__file__), "baseline.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS baseline (path TEXT PRIMARY KEY, sha256 TEXT)"
    )
    return conn


def reinitialize():
    """Re-measures all monitored files and stores them as the new trusted baseline."""
    measurements = measure_all()
    conn = _get_conn()
    conn.execute("DELETE FROM baseline")
    conn.executemany(
        "INSERT INTO baseline (path, sha256) VALUES (?, ?)",
        list(measurements.items()),
    )
    conn.commit()
    conn.close()
    return measurements


def get_baseline() -> dict:
    conn = _get_conn()
    rows = conn.execute("SELECT path, sha256 FROM baseline").fetchall()
    conn.close()
    return dict(rows)


def is_initialized() -> bool:
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM baseline").fetchone()[0]
    conn.close()
    return count > 0
