"""
Policy Engine

First checkpoint in the pipeline. Deterministic, rule-based classification
of an agent's proposed action:
  - Unknown actions are denied outright.
  - Non-sensitive actions (e.g. read_file) are allowed immediately, with no
    attestation overhead.
  - Sensitive actions (e.g. write_file, run_command) are passed on for
    integrity verification and attestation before a decision is made.
  - Any action whose target matches a denied pattern is blocked regardless
    of classification.
"""

import json
import logging
import os

log = logging.getLogger("policy_engine")

POLICY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy.json")


class PolicyEngine:
    def __init__(self, policy_path=POLICY_PATH):
        self.policy_path = policy_path
        self.reload()

    def reload(self):
        with open(self.policy_path, "r") as f:
            self.policy = json.load(f)
        log.info("policy loaded from %s", self.policy_path)

    def _target_is_denied(self, target):
        target = (target or "").lower()
        for pattern in self.policy.get("denied_targets", []):
            if pattern.lower() in target:
                return pattern
        return None

    def classify(self, action):
        """Return 'non_sensitive', 'sensitive', or 'unknown'."""
        if action in self.policy.get("non_sensitive_actions", []):
            return "non_sensitive"
        if action in self.policy.get("sensitive_actions", []):
            return "sensitive"
        return "unknown"

    def evaluate(self, action, target):
        """
        First-pass policy decision.

        Returns a dict with:
          classification: non_sensitive | sensitive | unknown
          decision: ALLOW | BLOCK | REVIEW
          reason: human-readable explanation
        """
        if action not in self.policy.get("allowed_actions", []):
            return {
                "classification": "unknown",
                "decision": "BLOCK",
                "reason": f"action '{action}' is not in allowed_actions",
            }

        denied_pattern = self._target_is_denied(target)
        if denied_pattern:
            return {
                "classification": self.classify(action),
                "decision": "BLOCK",
                "reason": f"target matches denied pattern '{denied_pattern}'",
            }

        classification = self.classify(action)
        if classification == "non_sensitive":
            return {
                "classification": classification,
                "decision": "ALLOW",
                "reason": "non-sensitive action, allowed without attestation",
            }

        # Sensitive actions require integrity verification + attestation
        # before a final decision can be made.
        return {
            "classification": classification,
            "decision": "REVIEW",
            "reason": "sensitive action, requires attestation",
        }
