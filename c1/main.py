#!/usr/bin/env python3

import requests
import json
import sys
import os
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"
C3_URL = "http://c3:8000/evaluate"
MODEL = "trustedge-agent"

def ask_agent(task):
    payload = {
        "model": MODEL,
        "prompt": task,
        "format": "json",
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        return json.loads(raw)
    except Exception as e:
        print(f"[ERROR] Agent failed: {e}")
        return None

def evaluate(action, target, reasoning=""):
    payload = {
        "action": action,
        "target": target,
        "reasoning": reasoning
    }
    try:
        resp = requests.post(C3_URL, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] c3 failed: {e}")
        return None

def execute_command(target):
    try:
        print(f"[EXEC] Running: {target}")
        result = subprocess.run(target, shell=True, capture_output=True, text=True, timeout=30)
        print(f"[OUTPUT]\n{result.stdout}")
        if result.stderr:
            print(f"[ERROR]\n{result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("[ERROR] Command timed out.")
        return False
    except Exception as e:
        print(f"[ERROR] Execution failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("Enter task: ")

    print(f"[*] Task: {task}")

    decision = ask_agent(task)
    if not decision:
        print("[ERROR] No decision from agent.")
        sys.exit(1)

    print(f"[*] Agent decision: {json.dumps(decision, indent=2)}")

    action = decision.get("action", "unknown")
    target = decision.get("target", "unknown")
    reasoning = decision.get("reasoning", "")

    result = evaluate(action, target, reasoning)
    if not result:
        print("[ERROR] No response from c3.")
        sys.exit(1)

    if result.get("allowed"):
        print(f"[ALLOW] {action} -> {target}")
        if action == "execute":
            execute_command(target)
        else:
            print(f"[INFO] Action '{action}' allowed but not executed.")
    else:
        print(f"[BLOCK] {result.get('reason')}")
