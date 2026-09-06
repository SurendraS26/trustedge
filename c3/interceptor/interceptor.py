import os
import re
import signal
import time

from interceptor.hash_reader import hash_file
from policy_engine.policy_engine import is_sensitive
from alerts.alert_log import write_alert

AUDIT_LOG = os.environ.get("AUDIT_LOG", "/var/log/audit/audit.log")
PATTERN   = re.compile(
    r'type=SYSCALL.*?pid=(?P<pid>\d+).*?exe="(?P<exe>[^"]+)".*?key="(?P<key>[^"]+)"'
)


def kill(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except Exception:
        pass


def handle(pid, exe):
    if not is_sensitive("execute", exe):
        return
    h = hash_file(exe)
    print(f"[BLOCK] {exe} pid={pid}")
    kill(pid)
    write_alert("execute", exe, f"blocked by interceptor hash={h}")


def main():
    print(f"[*] Interceptor watching {AUDIT_LOG}")
    try:
        with open(AUDIT_LOG) as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                m = PATTERN.search(line)
                if m and m.group("key") == "trustedge_exec":
                    handle(int(m.group("pid")), m.group("exe"))
    except FileNotFoundError:
        print(f"[WARN] {AUDIT_LOG} not found — interceptor inactive")


if __name__ == "__main__":
    main()
