import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.policy_engine import PolicyEngine


def test_non_sensitive_action_is_allowed():
    engine = PolicyEngine()
    result = engine.evaluate("read_file", "/app/notes.txt")
    assert result["classification"] == "non_sensitive"
    assert result["decision"] == "ALLOW"


def test_sensitive_action_requires_review():
    engine = PolicyEngine()
    result = engine.evaluate("write_file", "/app/output.txt")
    assert result["classification"] == "sensitive"
    assert result["decision"] == "REVIEW"


def test_unknown_action_is_blocked():
    engine = PolicyEngine()
    result = engine.evaluate("format_disk", "/dev/sda")
    assert result["decision"] == "BLOCK"


def test_denied_target_is_blocked_even_if_action_is_sensitive():
    engine = PolicyEngine()
    result = engine.evaluate("write_file", "/etc/shadow")
    assert result["decision"] == "BLOCK"
    assert "denied pattern" in result["reason"]


def test_denied_command_target_is_blocked():
    engine = PolicyEngine()
    result = engine.evaluate("run_command", "rm -rf / --no-preserve-root")
    assert result["decision"] == "BLOCK"


if __name__ == "__main__":
    test_non_sensitive_action_is_allowed()
    test_sensitive_action_requires_review()
    test_unknown_action_is_blocked()
    test_denied_target_is_blocked_even_if_action_is_sensitive()
    test_denied_command_target_is_blocked()
    print("test_policy: all tests passed")
