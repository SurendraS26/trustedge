import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.interceptor import Interceptor


def test_valid_payload_is_captured():
    interceptor = Interceptor()
    request = interceptor.capture({
        "action": "read_file",
        "target": "/app/notes.txt",
        "reasoning": "user asked to see the file",
    })
    assert request.action == "read_file"
    assert request.target == "/app/notes.txt"
    assert request.received_at > 0


def test_missing_field_is_rejected():
    interceptor = Interceptor()
    with pytest.raises(ValueError):
        interceptor.capture({"action": "read_file", "target": "/app/notes.txt"})


def test_non_dict_payload_is_rejected():
    interceptor = Interceptor()
    with pytest.raises(ValueError):
        interceptor.capture(["not", "a", "dict"])


def test_empty_action_is_rejected():
    interceptor = Interceptor()
    with pytest.raises(ValueError):
        interceptor.capture({"action": "  ", "target": "x", "reasoning": "y"})


def test_fields_are_stripped():
    interceptor = Interceptor()
    request = interceptor.capture({
        "action": "  read_file  ",
        "target": "  /app/notes.txt  ",
        "reasoning": "  because  ",
    })
    assert request.action == "read_file"
    assert request.target == "/app/notes.txt"


if __name__ == "__main__":
    test_valid_payload_is_captured()
    test_fields_are_stripped()
    print("test_interceptor: core tests passed (run under pytest for full coverage)")
