#!/usr/bin/env python3

import os
import subprocess
import hashlib

def capture(action, target):
    if action != "execute":
        return {"allowed": True, "reason": "Action not intercepted"}

    if not os.path.exists(target):
        return {"allowed": False, "reason": f"Target '{target}' does not exist"}

    try:
        with open(target, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        return {"allowed": False, "reason": f"Hash computation failed: {str(e)}"}

    print(f"[INTERCEPT] Action: {action}, Target: {target}, Hash: {file_hash[:16]}...")

    return {"allowed": True, "reason": "Interception passed"}
