#!/usr/bin/env python3

import sqlite3
import os
import hashlib

DB_PATH = "/app/baseline.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            hash TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def store_baseline(filepath, hash_value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO baseline (filepath, hash) VALUES (?, ?)",
        (filepath, hash_value)
    )
    conn.commit()
    conn.close()

def get_baseline(filepath):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT hash FROM baseline WHERE filepath = ?",
        (filepath,)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def compute_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def is_modified(filepath):
    stored_hash = get_baseline(filepath)
    if stored_hash is None:
        return True
    current_hash = compute_hash(filepath)
    return current_hash != stored_hash
