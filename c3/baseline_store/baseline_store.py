import hashlib
import os
import sqlite3

DB = os.environ.get("BASELINE_DB", "/app/baseline_store/baseline.db")


def get_conn():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    return sqlite3.connect(DB)


def init_db():
    with get_conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, hash TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS pcrs  (pcr  TEXT PRIMARY KEY, value TEXT)")
        c.commit()


def save_file_hash(path, hash_value):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO files VALUES (?,?)", (path, hash_value.lower()))
        c.commit()


def get_file_hash(path):
    row = get_conn().execute("SELECT hash FROM files WHERE path=?", (path,)).fetchone()
    return row[0] if row else None


def save_pcr(pcr, value):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO pcrs VALUES (?,?)", (str(pcr), value.lower()))
        c.commit()


def get_pcr(pcr):
    row = get_conn().execute("SELECT value FROM pcrs WHERE pcr=?", (str(pcr),)).fetchone()
    return row[0] if row else None


def hash_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None
