import hashlib
import json
import os

from baseline_store.baseline_store import get_baseline_hash

MEASURED_FILES_CONFIG = os.path.join(os.path.dirname(__file__), "measured_files.json")


def hash_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return None


def load_measured_files() -> list[str]:
    with open(MEASURED_FILES_CONFIG) as f:
        return json.load(f).get("files", [])


def run_integrity_check() -> tuple[bool, list[str]]:
    """
    Hashes all measured files and compares against the baseline.
    Returns (True, []) if all files match.
    Returns (False, [list of failed files]) if any file has changed.
    """
    measured_files = load_measured_files()
    failed = []

    for file_path in measured_files:
        current_hash = hash_file(file_path)

        if current_hash is None:
            failed.append(f"{file_path} (unreadable)")
            continue

        baseline_hash = get_baseline_hash(file_path)

        if baseline_hash is None:
            # File not in baseline yet — treat as untrusted
            failed.append(f"{file_path} (not in baseline)")
            continue

        if current_hash != baseline_hash:
            failed.append(f"{file_path} (hash mismatch)")

    return (len(failed) == 0, failed)

