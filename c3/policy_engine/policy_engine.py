"""
TrustEdge — Policy Engine
Deterministic rule-based classifier.
Returns True (sensitive) → full attestation required.
Returns False (non-sensitive) → directly allowed.
Fails closed — any error returns True (sensitive).
"""

import json
import logging
import os

log = logging.getLogger("trustedge.policy")

POLICY_FILE = os.path.join(os.path.dirname(__file__), "policy.json")


def load_policy() -> dict:
    with open(POLICY_FILE) as f:
        return json.load(f)


def is_sensitive(action: str, target: str) -> bool:
    """
    Fails closed — if the policy file cannot be read or parsed,
    treats the action as sensitive rather than allowing it through.
    """
    try:
        policy = load_policy()
    except Exception as e:
        log.error(f"Could not load policy file: {e} — failing closed (sensitive=True)")
        return True

    action_lower = action.lower().strip()
    target_lower = target.lower().strip()

    for sensitive_action in policy.get("sensitive_actions", []):
        if sensitive_action.lower() in action_lower:
            log.info(f"Sensitive action matched: '{sensitive_action}' in '{action}'")
            return True

    for sensitive_target in policy.get("sensitive_targets", []):
        if target_lower.startswith(sensitive_target.lower()) or \
           sensitive_target.lower() in target_lower:
            log.info(f"Sensitive target matched: '{sensitive_target}' in '{target}'")
            return True

    return False
