import hashlib
import json
import os

from baseline_store.baseline_store import get_file_hash

CFG = os.path.join(os.path.dirname(__file__), "measured_files.json")


def hash_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def run_integrity_check():
    with open(CFG) as f:
        files = json.load(f).get("files", [])

    failed = []
    for path in files:
        current = hash_file(path)
        if current is None:
            failed.append(f"{path} (unreadable)")
            continue

        baseline = get_file_hash(path)
        if baseline is None:
            failed.append(f"{path} (not in baseline)")
            continue

        if current.lower() != baseline.lower():
            failed.append(f"{path} (mismatch)")

    return len(failed) == 0, failed
