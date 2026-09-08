#!/usr/bin/env python3

import json
import os

POLICY_FILE = "/app/policy.json"

def load_policy():
    if not os.path.exists(POLICY_FILE):
        return {"allowed_actions": ["read", "write", "execute", "list", "query"], "allowed_hashes": []}
    with open(POLICY_FILE, "r") as f:
        return json.load(f)

def check(action, target):
    policy = load_policy()

    if action not in policy.get("allowed_actions", []):
        return {"allowed": False, "reason": f"Action '{action}' not allowed by policy"}

    return {"allowed": True, "reason": "Policy check passed"}
