import json
import os

POLICY_FILE = os.path.join(os.path.dirname(__file__), "policy.json")


def is_sensitive(action: str, target: str) -> bool:
    try:
        with open(POLICY_FILE) as f:
            policy = json.load(f)
    except Exception:
        return True  # fail closed

    action = action.lower()
    target = target.lower()

    for s in policy.get("sensitive_actions", []):
        if s in action:
            return True

    for s in policy.get("sensitive_targets", []):
        if target.startswith(s) or s in target:
            return True

    return False
