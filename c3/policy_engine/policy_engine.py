import json
import os

POLICY_FILE = os.path.join(os.path.dirname(__file__), "policy.json")


def load_policy() -> dict:
    with open(POLICY_FILE) as f:
        return json.load(f)


def is_sensitive(action: str, target: str) -> bool:
    """
    Evaluates an action+target pair against the policy rules.
    Returns True  → sensitive, requires full attestation.
    Returns False → non-sensitive, directly allowed.
    """
    policy = load_policy()

    action_lower = action.lower()
    target_lower = target.lower()

    # Check sensitive actions
    for sensitive_action in policy.get("sensitive_actions", []):
        if sensitive_action in action_lower:
            return True

    # Check sensitive target prefixes/keywords
    for sensitive_target in policy.get("sensitive_targets", []):
        if target_lower.startswith(sensitive_target) or sensitive_target in target_lower:
            return True

    return False

