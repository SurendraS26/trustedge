"""
Baseline Store

Maintains the known-good SHA-256 hashes of the framework's own critical
files (policy config, enforcement modules) in SQLite. On first run it
measures the files listed in policy.json's "critical_files" and records
them as the trusted baseline. On every later run it re-measures the same
files so the Verifier can detect tampering before it trusts a decision.
"""

import hashlib
import json
import logging
import os
import sqlite3
import time

log = logging.getLogger("baseline_store")

C3_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_PATH = os.path.join(C3_ROOT, "policy.json")
DB_PATH = os.environ.get("SQLITE_PATH", "/data/trustedge.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS baseline (
    file_path TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    recorded_at REAL NOT NULL
);
"""


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class BaselineStore:
    def __init__(self, db_path=DB_PATH, policy_path=POLICY_PATH):
        self.db_path = db_path
        self.policy_path = policy_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def _critical_files(self):
        with open(self.policy_path, "r") as f:
            policy = json.load(f)
        return [os.path.join(C3_ROOT, rel) for rel in policy.get("critical_files", [])]

    def establish_baseline_if_empty(self):
        """Seed the baseline table the first time the framework boots."""
        cur = self.conn.execute("SELECT COUNT(*) FROM baseline")
        count = cur.fetchone()[0]
        if count > 0:
            log.info("baseline already established (%d files)", count)
            return

        for path in self._critical_files():
            if not os.path.exists(path):
                log.warning("critical file missing, skipping baseline: %s", path)
                continue
            digest = _sha256_file(path)
            self.conn.execute(
                "INSERT INTO baseline (file_path, sha256, recorded_at) VALUES (?, ?, ?)",
                (path, digest, time.time()),
            )
        self.conn.commit()
        log.info("baseline established for %d files", len(self._critical_files()))

    def current_measurements(self):
        """Re-hash every critical file right now."""
        measurements = {}
        for path in self._critical_files():
            if os.path.exists(path):
                measurements[path] = _sha256_file(path)
        return measurements

    def baseline_measurements(self):
        cur = self.conn.execute("SELECT file_path, sha256 FROM baseline")
        return {row[0]: row[1] for row in cur.fetchall()}

    def combined_digest(self, measurements):
        """Deterministically combine per-file hashes into a single digest
        suitable for extending into a PCR."""
        h = hashlib.sha256()
        for path in sorted(measurements.keys()):
            h.update(path.encode("utf-8"))
            h.update(measurements[path].encode("utf-8"))
        return h.hexdigest()

    def check_integrity(self):
        """
        Compare current file hashes against the recorded baseline.

        Returns (is_intact, mismatched_files, combined_digest_of_current_state)
        """
        baseline = self.baseline_measurements()
        current = self.current_measurements()

        mismatched = [
            path for path, digest in current.items()
            if baseline.get(path) != digest
        ]
        return (len(mismatched) == 0, mismatched, self.combined_digest(current))
