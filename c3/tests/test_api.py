"""Test c3 API endpoints — simulates c1 agent requests"""
import sys
import requests

URL = "http://localhost:8000"

print(f"\n=== API Tests ({URL}) ===")

# Health
try:
    r = requests.get(f"{URL}/health", timeout=5)
    print(f"  [{'PASS' if r.status_code==200 else 'FAIL'}] GET /health")
except Exception as e:
    print(f"  [FAIL] c3 not reachable: {e}")
    sys.exit(1)

# Policy check — sensitive
r = requests.get(f"{URL}/policy/check", params={"action": "delete", "target": "/etc/passwd"})
print(f"  [{'PASS' if r.json()['sensitive'] else 'FAIL'}] policy: delete /etc/passwd is sensitive")

# Policy check — non-sensitive
r = requests.get(f"{URL}/policy/check", params={"action": "read", "target": "/tmp/notes.txt"})
print(f"  [{'PASS' if not r.json()['sensitive'] else 'FAIL'}] policy: read /tmp/notes.txt is non-sensitive")

# Evaluate non-sensitive — should allow
r = requests.post(f"{URL}/evaluate", json={"action": "read", "target": "/tmp/notes.txt"})
d = r.json()
print(f"  [{'PASS' if d['allowed'] else 'FAIL'}] evaluate: non-sensitive action allowed")

# Evaluate sensitive — should go through full pipeline
r = requests.post(f"{URL}/evaluate", json={"action": "delete", "target": "/etc/passwd"})
d = r.json()
print(f"  [INFO] evaluate: sensitive action -> allowed={d['allowed']} reason={d['reason']}")

print()
