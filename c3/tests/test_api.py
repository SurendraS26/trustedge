"""
Verify the FastAPI endpoints respond correctly using FastAPI's TestClient
(in-process, no running server or TPM required for the non-sensitive
paths). Run with: pytest tests/test_api.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SQLITE_PATH", "/tmp/trustedge-test.db")

from fastapi.testclient import TestClient

import main as framework_main

client = TestClient(framework_main.app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_evaluate_non_sensitive_action_is_allowed():
    resp = client.post("/evaluate", json={
        "action": "read_file",
        "target": "/app/notes.txt",
        "reasoning": "user requested contents",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "ALLOW"


def test_evaluate_unknown_action_is_blocked():
    resp = client.post("/evaluate", json={
        "action": "format_disk",
        "target": "/dev/sda",
        "reasoning": "not a real capability",
    })
    assert resp.status_code == 200
    assert resp.json()["decision"] == "BLOCK"


def test_evaluate_malformed_request_is_rejected():
    resp = client.post("/evaluate", json={"action": "read_file"})
    # Pydantic model requires 'target'; FastAPI returns 422 for schema errors.
    assert resp.status_code == 422


if __name__ == "__main__":
    test_health_endpoint()
    test_evaluate_non_sensitive_action_is_allowed()
    test_evaluate_unknown_action_is_blocked()
    print("test_api: non-TPM tests passed")
