#!/usr/bin/env python3
import json
import os
import subprocess
import time
import glob

SHARED_DIR = os.environ.get("TRUSTEDGE_SHARED_DIR", "./shared")
POLL_INTERVAL_SECONDS = 0.5

URGENCY_ICON = {
    "low": "info",
    "normal": "warning",
    "critical": "error",
}


def handle_popup_request(req: dict):
    urgency = req.get("urgency", "normal")
    action_type = req.get("action_type", "unknown")
    details = req.get("details", {})
    icon = URGENCY_ICON.get(urgency, "warning")

    text = (
        f"TrustEdge: agent wants to perform an action\n\n"
        f"Action: {action_type}\n"
        f"Urgency: {urgency.upper()}\n"
        f"Details: {json.dumps(details)}"
    )

    result = subprocess.run(
        [
            "zenity", f"--{icon}",
            "--title=TrustEdge Approval",
            f"--text={text}",
            "--ok-label=Allow",
            "--cancel-label=Block",
        ]
    )
    decision = "allow" if result.returncode == 0 else "block"

    decision_path = os.path.join(SHARED_DIR, f"decision_{req['id']}.json")
    with open(decision_path, "w") as f:
        json.dump({"decision": decision}, f)


def handle_edit_request(req: dict):
    file_path = req.get("file_path")
    subprocess.run(["gedit", "--wait", file_path])

    decision_path = os.path.join(SHARED_DIR, f"decision_{req['id']}.json")
    with open(decision_path, "w") as f:
        json.dump({"decision": "closed"}, f)


def main():
    print(f"[relay] Watching {SHARED_DIR} for TrustEdge requests...")
    seen = set()
    while True:
        for path in glob.glob(os.path.join(SHARED_DIR, "request_*.json")):
            if path in seen:
                continue
            try:
                with open(path, "r") as f:
                    req = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

            seen.add(path)
            os.remove(path)

            if req.get("type") == "popup":
                handle_popup_request(req)
            elif req.get("type") == "edit":
                handle_edit_request(req)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
