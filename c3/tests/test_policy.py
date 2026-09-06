"""Test policy engine — no TPM needed"""
import sys
sys.path.insert(0, "/app")
from policy_engine.policy_engine import is_sensitive

cases = [
    ("read",    "/tmp/notes.txt",   False, "read public file"),
    ("read",    "/etc/passwd",      True,  "read /etc/"),
    ("delete",  "/tmp/file.txt",    True,  "delete action"),
    ("execute", "/usr/bin/ls",      True,  "execute action"),
    ("write",   "/home/user/a.txt", True,  "write action"),
    ("read",    "secret.pem",       True,  "secret in name"),
    ("list",    "/home/user/docs",  False, "list non-sensitive"),
]

print("\n=== Policy Engine ===")
passed = 0
for action, target, expected, desc in cases:
    result = is_sensitive(action, target)
    ok = result == expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    if ok:
        passed += 1
print(f"\n{passed}/{len(cases)} passed\n")
