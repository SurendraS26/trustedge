"""
TrustEdge — Integrity Monitor Tests
Tests hash reading, baseline recording, and mismatch detection.
Run: python tests/test_integrity.py
No TPM required.
"""

import os
import sys
import tempfile

sys.path.insert(0, "/app")

from baseline_store.baseline_store import init_db, record_baseline_hash, get_baseline_hash
from integrity_monitor.integrity_monitor import hash_file

PASS = "\033[1;32mPASS\033[0m"
FAIL = "\033[1;31mFAIL\033[0m"

passed = 0
failed = 0


def check(desc: str, condition: bool):
    global passed, failed
    if condition:
        print(f"  [{PASS}] {desc}")
        passed += 1
    else:
        print(f"  [{FAIL}] {desc}")
        failed += 1


print("\n=== Integrity Monitor Tests ===\n")

# ── Test 1: hash a real file ──────────────────────────────────────────────
with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
    f.write("trusted content")
    tmp_path = f.name

h = hash_file(tmp_path)
check("hash_file returns a 64-char hex string", h is not None and len(h) == 64)

# ── Test 2: same content always produces same hash ────────────────────────
h2 = hash_file(tmp_path)
check("hash_file is deterministic", h == h2)

# ── Test 3: different content produces different hash ─────────────────────
with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
    f.write("tampered content")
    tmp_path2 = f.name

h3 = hash_file(tmp_path2)
check("different content produces different hash", h != h3)

# ── Test 4: non-existent file returns None ────────────────────────────────
h4 = hash_file("/does/not/exist.txt")
check("non-existent file returns None", h4 is None)

# ── Test 5: baseline store round-trip ────────────────────────────────────
os.environ["BASELINE_DB"] = "/tmp/trustedge_test_baseline.db"
init_db()
record_baseline_hash(tmp_path, h)
retrieved = get_baseline_hash(tmp_path)
check("baseline hash stored and retrieved correctly", retrieved == h)

# ── Test 6: mismatch detection ────────────────────────────────────────────
record_baseline_hash(tmp_path2, h)  # record OLD hash for path2
current = hash_file(tmp_path2)      # current hash is different (tampered content)
check("mismatch detected correctly", current != get_baseline_hash(tmp_path2))

# Cleanup
os.remove(tmp_path)
os.remove(tmp_path2)
try:
    os.remove("/tmp/trustedge_test_baseline.db")
except FileNotFoundError:
    pass

print(f"\nResults: {passed} passed, {failed} failed\n")
sys.exit(0 if failed == 0 else 1)
