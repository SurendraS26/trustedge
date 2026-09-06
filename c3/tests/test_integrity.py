"""Test integrity monitor and baseline store — no TPM needed"""
import os, sys, tempfile
sys.path.insert(0, "/app")

os.environ["BASELINE_DB"] = "/tmp/test_baseline.db"
from baseline_store.baseline_store import init_db, save_file_hash, get_file_hash
from integrity_monitor.integrity_monitor import hash_file

print("\n=== Integrity Monitor ===")

init_db()

# Create a test file
f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
f.write("trusted content")
f.close()

h = hash_file(f.name)
save_file_hash(f.name, h)

print(f"  [{'PASS' if h and len(h)==64 else 'FAIL'}] hash_file returns SHA256")
print(f"  [{'PASS' if hash_file(f.name)==h else 'FAIL'}] hash is deterministic")
print(f"  [{'PASS' if get_file_hash(f.name)==h else 'FAIL'}] baseline store round-trip")
print(f"  [{'PASS' if hash_file('/does/not/exist') is None else 'FAIL'}] missing file returns None")

os.remove(f.name)
try: os.remove("/tmp/test_baseline.db")
except: pass
print()
