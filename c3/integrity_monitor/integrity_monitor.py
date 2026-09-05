"""
TrustEdge — Integrity Monitor
Hashes all measured files and compares against the baseline.
Fails closed — missing or unreadable files are treated as failures.
"""

import hashlib
import json
import logging
import os

log = logging.getLogger("trustedge.integrity")

MEASURED_FILES_CONFIG = os.path.join(os.path.dirname(__file__), "measured_files.json")


def hash_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        log.warning(f"Cannot hash {path}: {e}")
        return None


def load_measured_files() -> list[str]:
    with open(MEASURED_FILES_CONFIG) as f:
        return json.load(f).get("files", [])


def run_integrity_check() -> tuple[bool, list[str]]:
    """
    Returns (True, []) if all files match baseline.
    Returns (False, [failed_files]) if any mismatch or missing.
    """
    from baseline_store.baseline_store import get_baseline_hash

    try:
        measured_files = load_measured_files()
    except Exception as e:
        log.error(f"Cannot load measured files config: {e}")
        return False, ["measured_files.json unreadable"]

    failed = []

    for file_path in measured_files:
        current_hash = hash_file(file_path)

        if current_hash is None:
            failed.append(f"{file_path} (unreadable)")
            continue

        try:
            baseline_hash = get_baseline_hash(file_path)
        except Exception as e:
            log.error(f"Baseline store error for {file_path}: {e}")
            failed.append(f"{file_path} (baseline store error)")
            continue

        if baseline_hash is None:
            log.warning(f"{file_path} not in baseline — treating as untrusted")
            failed.append(f"{file_path} (not in baseline)")
            continue

        if current_hash.lower() != baseline_hash.lower():
            log.warning(f"{file_path} HASH MISMATCH")
            failed.append(f"{file_path} (hash mismatch)")

    ok = len(failed) == 0
    if ok:
        log.info("Integrity check passed")
    else:
        log.warning(f"Integrity check failed: {failed}")

    return ok, failed
