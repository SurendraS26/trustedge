import asyncio
import json
import os
import urllib.request

import websockets

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
FRAMEWORK_WS = os.environ.get("FRAMEWORK_WS", "ws://trustedge-c3:8000/agent-link")

SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string"},
        "action": {"type": "string", "enum": ["run_command", "done", "error"]},
        "target": {"type": ["string", "null"]},
        "reason": {"type": "string"},
    },
    "required": ["thought", "action", "target", "reason"],
}

SYSTEM_PROMPT = (
    "You are the reasoning core of a security-conscious agent. Given the "
    "operator's request, decide the single next step. You do not execute "
    "anything yourself - you only propose. Respond with ONLY a single JSON "
    "object matching the given schema. If action is run_command, target "
    "MUST be a complete, self-contained bash script. If the task is already "
    "satisfied or impossible, use action done or error with target null.\n\n"
    "The script runs on a sandbox machine with these facts:\n"
    "- OS is Arch Linux. It is NOT Debian or Ubuntu. Never use apt, apt-get, dnf or yum.\n"
    "- Package manager is pacman. Install with: sudo pacman -Sy --noconfirm --needed <package>\n"
    "- Desktop is XFCE4. You run as user 'trustedge' with passwordless sudo.\n"
    "- Chromium, xfce4-terminal and Thunar (file manager) are already installed.\n"
    "- Launch GUI apps in the background so the script finishes, for example: "
    "chromium 'https://example.com' >/dev/null 2>&1 &\n"
    "- Scripts must never wait for keyboard input."
)


def ask_model(task: str):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ],
        "stream": False,
        "format": SCHEMA,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    raw = data.get("message", {}).get("content", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def run_task(task: str):
    print(f"task: {task}")

    decision = ask_model(task)
    if decision is None:
        print("model did not return a usable decision")
        return

    if decision["action"] == "done":
        print(f"done: {decision['reason']}")
        return
    if decision["action"] == "error":
        print(f"error: {decision['reason']}")
        return

    script = decision["target"]
    print(f"proposed script:\n{script}")
    print(f"reason: {decision['reason']}")
    print("sent to trustedge-c3 for evaluation")

    try:
        async with websockets.connect(FRAMEWORK_WS) as ws:
            await ws.send(json.dumps({"target": script, "reasoning": decision["reason"]}))

            message = json.loads(await ws.recv())

            if message["type"] == "verdict":
                print(f"blocked: {message['reason']}")
                return

            if message["type"] == "confirm":
                print()
                print(message["script"])
                print()
                answer = (await asyncio.to_thread(input, "accept y/n: ")).strip().lower()
                decision_word = "ALLOW" if answer == "y" else "BLOCK"
                await ws.send(json.dumps({"decision": decision_word}))

                final = json.loads(await ws.recv())
                if final["type"] == "verdict":
                    print(f"blocked: {final['reason']}")
                    return
                if final["type"] == "result":
                    print("task done" if final.get("ok") else "task failed")
                    if final.get("output"):
                        print(final["output"])
    except Exception as exc:  # noqa: BLE001
        print(f"could not reach trustedge-c3: {exc}")


def main():
    print("""
    [ ascii art space ]
    """)
    print("trustedge-c1")
    print("type a task and press enter, or 'q' to quit")
    while True:
        task = input("> ").strip()
        if task.lower() in ("q", "quit", "exit"):
            break
        if not task:
            continue
        asyncio.run(run_task(task))


if __name__ == "__main__":
    main()
