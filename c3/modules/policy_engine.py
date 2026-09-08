#!/usr/bin/env python3

import json
import os
import hashlib

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

    # If the policy defines an explicit hash allowlist, only executables
    # whose hash appears in it may be run. An empty/absent list means no
    # extra restriction beyond the action check above (backward compatible).
    allowed_hashes = policy.get("allowed_hashes", [])
    if action == "execute" and allowed_hashes:
        if not os.path.exists(target):
            return {"allowed": False, "reason": f"Target '{target}' does not exist"}
        try:
            with open(target, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return {"allowed": False, "reason": f"Hash computation failed: {str(e)}"}
        if file_hash not in allowed_hashes:
            return {"allowed": False, "reason": "Executable hash not in policy allowlist"}

    return {"allowed": True, "reason": "Policy check passed"}
