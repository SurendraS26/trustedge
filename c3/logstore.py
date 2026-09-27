import os
import sqlite3
import time

DB_PATH = os.environ.get("SQLITE_PATH", "/data/trustedge.db")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            script TEXT,
            reasoning TEXT,
            decision TEXT,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()


def record(script, reasoning, decision, reason):
    conn = _connect()
    conn.execute(
        "INSERT INTO audit_log (timestamp, script, reasoning, decision, reason) VALUES (?, ?, ?, ?, ?)",
        (time.time(), script, reasoning, decision, reason),
    )
    conn.commit()
    conn.close()


def recent(limit=20):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

