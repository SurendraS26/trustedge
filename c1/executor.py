"""
Executor

Performs the action the model proposed - but only ever called after the c3
framework has returned an ALLOW verdict for it. This module has no
knowledge of policy, attestation, or the operator popup; it trusts that the
caller (main.py) has already gated the call correctly. It never runs
anything on its own initiative.
"""

import logging
import os
import subprocess

import requests

log = logging.getLogger("executor")

COMMAND_TIMEOUT_SECONDS = 30
NETWORK_TIMEOUT_SECONDS = 15
MAX_PRINTED_CHARS = 2000


def _truncate(text):
    if text is None:
        return ""
    if len(text) > MAX_PRINTED_CHARS:
        return text[:MAX_PRINTED_CHARS] + f"\n... [truncated, {len(text)} chars total]"
    return text


def execute(decision):
    """
    Execute one approved action.

    Returns a dict: { "ok": bool, "output": str }
    Never raises - all errors are caught and reported in "output".
    """
    action = decision.get("action")
    target = decision.get("target", "")
    content = decision.get("content", "")

    handlers = {
        "read_file": _read_file,
        "write_file": _write_file,
        "delete_file": _delete_file,
        "run_command": _run_command,
        "network_call": _network_call,
    }

    handler = handlers.get(action)
    if handler is None:
        return {"ok": False, "output": f"no executor for action '{action}'"}

    try:
        return handler(target, content)
    except Exception as exc:  # noqa: BLE001 - executor must never crash the agent loop
        log.error("execution of %s on %s failed: %s", action, target, exc)
        return {"ok": False, "output": f"execution error: {exc}"}


def _read_file(target, _content):
    if not os.path.isfile(target):
        return {"ok": False, "output": f"file not found: {target}"}
    with open(target, "r", errors="replace") as f:
        data = f.read()
    log.info("read %d bytes from %s", len(data), target)
    return {"ok": True, "output": _truncate(data)}


def _write_file(target, content):
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w") as f:
        f.write(content or "")
    log.info("wrote %d bytes to %s", len(content or ""), target)
    return {"ok": True, "output": f"wrote {len(content or '')} bytes to {target}"}


def _delete_file(target, _content):
    if not os.path.exists(target):
        return {"ok": False, "output": f"nothing to delete at: {target}"}
    os.remove(target)
    log.info("deleted %s", target)
    return {"ok": True, "output": f"deleted {target}"}


def _run_command(target, _content):
    result = subprocess.run(
        target,
        shell=True,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    output = f"exit code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    log.info("ran command '%s' (exit %d)", target, result.returncode)
    return {"ok": result.returncode == 0, "output": _truncate(output)}


def _network_call(target, _content):
    resp = requests.get(target, timeout=NETWORK_TIMEOUT_SECONDS)
    output = f"status: {resp.status_code}\nbody:\n{resp.text}"
    log.info("network call to %s returned %d", target, resp.status_code)
    return {"ok": resp.ok, "output": _truncate(output)}
