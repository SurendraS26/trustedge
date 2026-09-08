#!/usr/bin/env python3

import sqlite3
from datetime import datetime

DB_PATH = "/app/audit.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            action TEXT,
            target TEXT,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def log(action, target, reason):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO audit (timestamp, action, target, reason) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), action, target, reason)
    )
    conn.commit()
    conn.close()

def get_logs(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT timestamp, action, target, reason FROM audit ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows
