import os
import requests

FRAMEWORK_URL = os.environ.get("FRAMEWORK_URL", "http://c2-framework:8000/evaluate")


class ActionDenied(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def request_action(action_type: str, details: dict) -> dict:
    payload = {"action_type": action_type, "details": details}
    resp = requests.post(FRAMEWORK_URL, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    if result.get("decision") != "allow":
        raise ActionDenied(result.get("reason", "denied by framework"))

    return result


def execute_if_allowed(action_type: str, details: dict, executor):
    request_action(action_type, details)
    return executor()
