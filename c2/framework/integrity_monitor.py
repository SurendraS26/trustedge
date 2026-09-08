import hashlib
import json
import os

MEASURED_FILES_PATH = os.path.join(os.path.dirname(__file__), "measured_files.json")


def _load_file_list() -> list[str]:
    with open(MEASURED_FILES_PATH, "r") as f:
        return json.load(f)["measured_files"]


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def measure_all() -> dict:
    measurements = {}
    for path in _load_file_list():
        try:
            measurements[path] = _hash_file(path)
        except FileNotFoundError:
            measurements[path] = None  # missing file is itself a red flag
    return measurements
