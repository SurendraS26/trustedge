import json
import sys

import requests

OLLAMA_URL  = "http://localhost:11434/api/generate"
C3_EVAL_URL = "http://trustedge-c3:8000/evaluate"
MODEL       = "trustedge-agent"


def ask_agent(task: str) -> dict | None:
    """Send a task to the Ollama agent and return parsed JSON response."""
    payload = {
        "model":  MODEL,
        "prompt": task,
        "format": "json",
        "stream": False
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        return json.loads(raw)
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"[ERROR] Agent call failed: {e}")
        return None


def evaluate_with_framework(action: str, target: str, reasoning: str) -> dict | None:
    """Forward the agent's action decision to c3 for security evaluation."""
    payload = {
        "action":    action,
        "target":    target,
        "reasoning": reasoning
    }

    try:
        resp = requests.post(C3_EVAL_URL, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[ERROR] c3 framework call failed: {e}")
        return None


def run(task: str) -> None:
    print(f"\n[*] Task: {task}")

    # Step 1 — Ask the agent what to do
    decision = ask_agent(task)
    if decision is None:
        print("[ERROR] No decision from agent.")
        return

    print(f"[*] Agent decision: {json.dumps(decision, indent=2)}")

    action    = decision.get("action", "unknown")
    target    = decision.get("target", "unknown")
    reasoning = decision.get("reasoning", "")

    # Step 2 — Forward to c3 for security evaluation
    result = evaluate_with_framework(action, target, reasoning)
    if result is None:
        print("[ERROR] No response from c3 framework.")
        return

    if result.get("allowed"):
        print(f"[ALLOW] Action permitted: {action} -> {target}")
        # Execute the action here in the real implementation
    else:
        print(f"[BLOCK] Action denied: {result.get('reason')}")


if __name__ == "__main__":
    # Accept task from stdin or command line for testing
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("Enter task: ")

    run(task)

