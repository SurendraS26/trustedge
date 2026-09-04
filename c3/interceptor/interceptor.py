"""
TrustEdge — Interceptor (auditd-based)
Tails the Linux audit log for execve() events tagged with "trustedge_exec",
extracts the executable path and PID, hashes the binary, checks it against
the policy engine, and kills + alerts if not allowed.
Requires:
  - auditd running on host
  - audit_rules.sh already applied
  - /var/log/audit/audit.log mounted into the container (read-only)
"""

import os
import re
import signal
import time

from interceptor.hash_reader import hash_file
from policy_engine.policy_engine import is_sensitive
from alerts.alert_log import write_alert

AUDIT_LOG = os.environ.get("AUDIT_LOG", "/var/log/audit/audit.log")
AUDIT_KEY = "trustedge_exec"

SYSCALL_RE = re.compile(
    r'type=SYSCALL.*?pid=(?P<pid>\d+).*?exe="(?P<exe>[^"]+)".*?key="(?P<key>[^"]+)"'
)


def kill_process(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGKILL)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        print(f"[WARN] No permission to kill pid={pid}")
        return False


def handle_exec(pid: int, exe_path: str) -> None:
    file_hash = hash_file(exe_path)

    if file_hash is None:
        write_alert(action="execute", target=exe_path, reason="unreadable executable")
        kill_process(pid)
        return

    # Route through the policy engine
    sensitive = is_sensitive("execute", exe_path)

    if not sensitive:
        print(f"[ALLOW] {exe_path} (pid={pid}) — non-sensitive")
        return

    # Sensitive execution — block immediately, alert
    print(f"[BLOCK] {exe_path} (pid={pid}, hash={file_hash})")
    kill_process(pid)
    write_alert(
        action="execute",
        target=exe_path,
        reason=f"sensitive executable blocked by interceptor (hash={file_hash})"
    )


def tail_log(path: str):
    with open(path, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line


def main():
    print(f"[*] TrustEdge interceptor started. Watching {AUDIT_LOG}")
    for line in tail_log(AUDIT_LOG):
        match = SYSCALL_RE.search(line)
        if not match or match.group("key") != AUDIT_KEY:
            continue
        handle_exec(int(match.group("pid")), match.group("exe"))


if __name__ == "__main__":
    main()

