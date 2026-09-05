"""
TrustEdge — Interceptor (auditd-based)
Tails the Linux audit log for execve() events tagged "trustedge_exec",
extracts executable path + PID, checks policy, kills + alerts if blocked.
Requires:
  - auditd running (host or container with CAP_AUDIT_CONTROL)
  - audit_rules.sh applied
  - /var/log/audit/audit.log accessible
"""

import logging
import os
import re
import signal
import time

log = logging.getLogger("trustedge.interceptor")

AUDIT_LOG = os.environ.get("AUDIT_LOG", "/var/log/audit/audit.log")
AUDIT_KEY = "trustedge_exec"

# tpm2_pcrread output line:  16: 0x9851...
# awk field 1 = "16:", field 2 = "0x9851..."
SYSCALL_RE = re.compile(
    r'type=SYSCALL.*?pid=(?P<pid>\d+).*?exe="(?P<exe>[^"]+)".*?key="(?P<key>[^"]+)"'
)


def kill_process(pid: int) -> bool:
    try:
        os.kill(pid, signal.SIGKILL)
        log.info(f"Killed pid={pid}")
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        log.warning(f"No permission to kill pid={pid} — run interceptor as root")
        return False


def handle_exec(pid: int, exe_path: str) -> None:
    from interceptor.hash_reader import hash_file
    from policy_engine.policy_engine import is_sensitive
    from alerts.alert_log import write_alert

    file_hash = hash_file(exe_path)

    if file_hash is None:
        log.warning(f"Unreadable executable: {exe_path} (pid={pid})")
        return

    try:
        sensitive = is_sensitive("execute", exe_path)
    except Exception as e:
        log.error(f"Policy engine error: {e} — failing closed")
        sensitive = True

    if not sensitive:
        log.info(f"[ALLOW] {exe_path} (pid={pid}) — non-sensitive")
        return

    log.warning(f"[BLOCK] {exe_path} (pid={pid}) hash={file_hash}")
    kill_process(pid)
    write_alert(
        action="execute",
        target=exe_path,
        reason=f"sensitive executable intercepted (hash={file_hash})"
    )


def tail_log(path: str):
    try:
        with open(path, "r") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                yield line
    except FileNotFoundError:
        log.error(f"Audit log not found at {path} — is auditd running and the log mounted?")


def main():
    log.info(f"Interceptor started — watching {AUDIT_LOG}")
    for line in tail_log(AUDIT_LOG):
        match = SYSCALL_RE.search(line)
        if not match or match.group("key") != AUDIT_KEY:
            continue
        handle_exec(int(match.group("pid")), match.group("exe"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
