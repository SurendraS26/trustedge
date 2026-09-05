"""
TrustEdge — Policy Engine Tests
Run: python tests/test_policy.py
No TPM or container required.
"""

import sys
sys.path.insert(0, "/app")

from policy_engine.policy_engine import is_sensitive

PASS = "\033[1;32mPASS\033[0m"
FAIL = "\033[1;31mFAIL\033[0m"

tests = [
    # (action, target, expected_sensitive, description)
    ("read",    "/tmp/notes.txt",        False, "read public file — non-sensitive"),
    ("read",    "/etc/passwd",           True,  "read /etc/ — sensitive target"),
    ("delete",  "/tmp/notes.txt",        True,  "delete — sensitive action"),
    ("execute", "/usr/bin/ls",           True,  "execute — sensitive action"),
    ("write",   "/home/user/doc.txt",    True,  "write — sensitive action"),
    ("read",    "secret_key.pem",        True,  "secret in filename — sensitive"),
    ("query",   "database:users",        True,  "database query — sensitive"),
    ("read",    "/var/log/syslog",       True,  "read /var/ — sensitive target"),
    ("list",    "/home/user/documents",  False, "list public directory — non-sensitive"),
    ("read",    "password.txt",          True,  "password in filename — sensitive"),
]

passed = 0
failed = 0

print("\n=== Policy Engine Tests ===\n")

for action, target, expected, desc in tests:
    result = is_sensitive(action, target)
    ok = result == expected
    status = PASS if ok else FAIL
    print(f"  [{status}] {desc}")
    if not ok:
        print(f"         action={action} target={target}")
        print(f"         expected sensitive={expected}, got {result}")
        failed += 1
    else:
        passed += 1

print(f"\nResults: {passed} passed, {failed} failed\n")
sys.exit(0 if failed == 0 else 1)
