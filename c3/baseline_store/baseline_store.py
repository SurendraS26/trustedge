import hashlib
import os
import sqlite3

DB_PATH     = os.environ.get("BASELINE_DB", "/app/baseline_store/baseline.db")
AK_PUB_PATH = os.environ.get("AK_PUB_PATH", "/app/baseline_store/ak.pub")


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create the baseline tables if they don't exist."""
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


# ── File hash operations ──────────────────────────────────────────────────

def record_baseline_hash(path: str, sha256: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO file_hashes (path, sha256) VALUES (?, ?)",
            (path, sha256)
        )
        conn.commit()


def get_baseline_hash(path: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT sha256 FROM file_hashes WHERE path = ?", (path,)
        ).fetchone()
    return row[0] if row else None


# ── PCR baseline operations ───────────────────────────────────────────────

def record_baseline_pcr(pcr_index: str, pcr_value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pcr_baselines (pcr_index, pcr_value) VALUES (?, ?)",
            (pcr_index, pcr_value.lower().lstrip("0x"))
        )
        conn.commit()


def get_baseline_pcr(pcr_index: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT pcr_value FROM pcr_baselines WHERE pcr_index = ?", (pcr_index,)
        ).fetchone()
    return row[0] if row else None


# ── AK public key path ────────────────────────────────────────────────────

def get_ak_pubkey_path() -> str:
    return AK_PUB_PATH


# ── Initialisation helper ─────────────────────────────────────────────────

def initialise_baseline(file_paths: list[str], pcr_values: dict[str, str]) -> None:
    """
    Populates the baseline store from scratch.
    Call this once on a known-clean system before running the framework.
    file_paths   — list of paths to hash and store
    pcr_values   — dict of {"16": "0x...", ...} from a clean TPM read
    """
    init_db()

    for path in file_paths:
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            record_baseline_hash(path, h.hexdigest())
            print(f"[baseline] recorded {path}")
        except Exception as e:
            print(f"[baseline] WARN: could not hash {path}: {e}")

    for pcr_index, pcr_value in pcr_values.items():
        record_baseline_pcr(pcr_index, pcr_value)
        print(f"[baseline] recorded PCR {pcr_index} = {pcr_value}")

