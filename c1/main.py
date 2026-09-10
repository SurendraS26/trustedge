import json
import logging
import os
import sys
import time

import requests

from executor import execute
from rag import build_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [c1] %(levelname)s %(message)s",
)
log = logging.getLogger("agent")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = "trustedge-agent"
FRAMEWORK_URL = os.environ.get("FRAMEWORK_URL", "http://c3-framework:8000/evaluate")
REQUEST_TIMEOUT = 60


def wait_for_ollama(max_wait_seconds=60):
    """Block until the local Ollama server responds, or give up."""
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/version", timeout=3)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def get_agent_decision(task_description):
    """Call Ollama and parse the model's JSON action proposal."""
    payload = {
        "model": MODEL_NAME,
        "prompt": task_description,
        "stream": False,
        "format": "json",
    }
    resp = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    raw_text = resp.json().get("response", "").strip()

    try:
        decision = json.loads(raw_text)
    except json.JSONDecodeError:
        log.error("model did not return valid JSON: %s", raw_text)
        return None

    if "action" not in decision or not str(decision["action"]).strip():
        log.error("model response missing required field: action (raw: %s)", raw_text)
        return None

    decision.setdefault("target", "")
    decision.setdefault("reasoning", "")

    return decision


def submit_for_evaluation(decision):
    """Send the proposed action to the c3 framework and return its verdict."""
    try:
        resp = requests.post(FRAMEWORK_URL, json=decision, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.error("could not reach framework at %s: %s", FRAMEWORK_URL, exc)
        return {"decision": "ERROR", "reason": str(exc)}


def print_result(decision, verdict, execution=None):
    print("-" * 60)
    print(f"action    : {decision.get('action')}")
    print(f"target    : {decision.get('target')}")
    print(f"reasoning : {decision.get('reasoning')}")
    print(f"verdict   : {verdict.get('decision')}")
    print(f"reason    : {verdict.get('reason', '')}")
    if execution is not None:
        status = "succeeded" if execution.get("ok") else "failed"
        print(f"executed  : {status}")
        print(f"output    : {execution.get('output', '')}")
    print("-" * 60)


def main():
    print("TrustEdge Agent")
    print("Type a task for the agent, or 'exit' to quit.")

    if not wait_for_ollama():
        log.error("ollama server did not become ready in time")
        sys.exit(1)

    while True:
        try:
            task = input("\ntask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nexiting")
            break

        if not task:
            continue
        if task.lower() in ("exit", "quit"):
            break

        grounded_task = build_prompt(task)
        decision = get_agent_decision(grounded_task)
        if decision is None:
            print("agent failed to produce a valid decision, try rephrasing the task")
            continue

        if decision.get("action") == "none":
            print(f"agent: no action needed - {decision.get('reasoning')}")
            continue

        verdict = submit_for_evaluation(decision)

        execution = None
        if verdict.get("decision") == "ALLOW":
            execution = execute(decision)
        else:
            log.info("action blocked, not executing: %s", verdict.get("reason"))

        print_result(decision, verdict, execution)


if __name__ == "__main__":
    main()
