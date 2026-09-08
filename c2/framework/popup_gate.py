import subprocess


def ask_popup(action_type: str, details: dict, urgency: str,
              timeout_seconds: int = 30, timeout_action: str = "deny") -> str:
    text = f"Action: {action_type}\nUrgency: {urgency}\n\n{details}"
    try:
        result = subprocess.run(
            ["zenity", "--question", "--title=TrustEdge",
             f"--text={text}", "--ok-label=Allow", "--cancel-label=Block",
             f"--timeout={timeout_seconds}"],
        )
        if result.returncode == 0:
            return "allow"
        if result.returncode == 1:
            return "block"
        return timeout_action
    except FileNotFoundError:
        return timeout_action


def ask_edit(file_path: str) -> bool:
    try:
        subprocess.run(["gedit", "--wait", file_path])
        return True
    except FileNotFoundError:
        return False
