import json
import os
import time
import uuid

SHARED_DIR = "/shared"
POLL_INTERVAL_SECONDS = 0.5


def _request_path(request_id: str) -> str:
    return os.path.join(SHARED_DIR, f"request_{request_id}.json")


def _decision_path(request_id: str) -> str:
    return os.path.join(SHARED_DIR, f"decision_{request_id}.json")


def ask_popup(action_type: str, details: dict, urgency: str,
              timeout_seconds: int = 30, timeout_action: str = "deny") -> str:
    request_id = uuid.uuid4().hex
    request = {
        "id": request_id,
        "type": "popup",
        "action_type": action_type,
        "details": details,
        "urgency": urgency,
    }
    with open(_request_path(request_id), "w") as f:
        json.dump(request, f)

    deadline = time.time() + timeout_seconds
    decision_file = _decision_path(request_id)

    while time.time() < deadline:
        if os.path.exists(decision_file):
            with open(decision_file, "r") as f:
                result = json.load(f)
            os.remove(decision_file)
            return result.get("decision", timeout_action)
        time.sleep(POLL_INTERVAL_SECONDS)

    # Timed out -- fall back to configured default (deny recommended)
    if os.path.exists(_request_path(request_id)):
        os.remove(_request_path(request_id))
    return timeout_action


def ask_edit(file_path: str, timeout_seconds: int = 300) -> bool:
    request_id = uuid.uuid4().hex
    request = {"id": request_id, "type": "edit", "file_path": file_path}
    with open(_request_path(request_id), "w") as f:
        json.dump(request, f)

    deadline = time.time() + timeout_seconds
    decision_file = _decision_path(request_id)

    while time.time() < deadline:
        if os.path.exists(decision_file):
            os.remove(decision_file)
            return True
        time.sleep(POLL_INTERVAL_SECONDS)

    return False
