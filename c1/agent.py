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
        "action": {"type": "string", "enum": ["reply", "run_command", "done", "error"]},
        "target": {"type": ["string", "null"]},
        "reason": {"type": "string"},
    },
    "required": ["thought", "action", "target", "reason"],
}

SYSTEM_PROMPT = """You are the reasoning core of TrustEdge, a security-conscious agent \
running on Arch Linux. You remember the whole conversation, not just the latest message.

Respond with ONLY a single JSON object matching the given schema - thought, action, \
target, reason. No text outside the JSON.

Choose "action" based on what the operator actually wants:
- "reply": the operator is chatting, asking a question, clarifying something, or you \
need more information before proposing anything. target MUST be null. Put your answer \
in "reason" - this is the only field the operator sees printed back to them for a reply.
- "run_command": the operator clearly wants something done on the sandbox. target MUST \
be a complete, self-contained bash script. You do not run it yourself - it is sent for \
approval and only executes if a human accepts it.
- "done": a previously approved action fully satisfied the request. target null.
- "error": the request is unsafe, impossible, or too ambiguous even after asking. \
target null.

Never guess a missing detail (a path, a filename, which of several files) - use "reply" \
and ask instead of picking one.

The sandbox (where run_command scripts execute) is Arch Linux, NOT Debian or Ubuntu:
- Package manager is pacman. Install with: sudo pacman -Sy --noconfirm --needed <package>
- Never use apt, apt-get, dnf, yum, or snap - they do not exist here.
- You run as user "trustedge" with passwordless sudo.
- Desktop environment is XFCE4, already running on display :1.
- Already installed: chromium, thunar (file manager), xfce4-terminal, xfce4-appfinder, \
zenity (for building GUI dialogs - forms, message boxes, progress bars, menus - useful \
for anything the operator wants as an interactive on-screen tool), git, python.
- Launch every GUI app in the background and then exit immediately - do not use `wait`, \
these apps are meant to keep running after your script finishes. Correct pattern:
    chromium "https://example.com" >/dev/null 2>&1 &
    disown
    exit 0
- A script is judged as failed if it exits non-zero, so keep exit codes deliberate: end \
with `exit 0` once you've started what you meant to start, and do not chain background \
launches with && (a backgrounded command returns before you know if it worked).
"""


def ask_model(history: list):
    payload = {
        "model": MODEL_NAME,
        "messages": history,
        "stream": False,
        "format": SCHEMA,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    raw = data.get("message", {}).get("content", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def run_task(history: list, task: str):
    history.append({"role": "user", "content": task})

    decision = ask_model(history)
    if decision is None:
        print("model did not return a usable decision")
        history.pop()  # don't poison history with a turn that produced nothing
        return

    history.append({"role": "assistant", "content": json.dumps(decision)})

    if decision["action"] == "reply":
        print(decision["reason"])
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

    outcome = "unknown"
    try:
        async with websockets.connect(FRAMEWORK_WS) as ws:
            await ws.send(json.dumps({"target": script, "reasoning": decision["reason"]}))

            message = json.loads(await ws.recv())

            if message["type"] == "verdict":
                print(f"blocked: {message['reason']}")
                outcome = f"blocked: {message['reason']}"
            elif message["type"] == "confirm":
                print()
                print(message["script"])
                print()
                answer = (await asyncio.to_thread(input, "accept y/n: ")).strip().lower()
                decision_word = "ALLOW" if answer == "y" else "BLOCK"
                await ws.send(json.dumps({"decision": decision_word}))

                final = json.loads(await ws.recv())
                if final["type"] == "verdict":
                    print(f"blocked: {final['reason']}")
                    outcome = f"blocked: {final['reason']}"
                elif final["type"] == "result":
                    ok = final.get("ok")
                    print("task done" if ok else "task failed")
                    if final.get("output"):
                        print(final["output"])
                    outcome = ("succeeded" if ok else "failed") + f" - output: {final.get('output', '')[:500]}"
    except Exception as exc:  # noqa: BLE001
        print(f"could not reach trustedge-c3: {exc}")
        outcome = f"could not reach trustedge-c3: {exc}"

    # so the next turn knows what actually happened, not just what was proposed
    history.append({"role": "user", "content": f"[system: outcome of that script - {outcome}]"})


def main():
    print("")
    print("\033[0;97m888888\033[0;37m \033[0;97m88\"\"Yb\033[0;37m \033[0;97m88\033[0;37m \033[0;97m88\033[0;37m \033[0;97m.dP\"Y8\033[0;37m \033[0;97m888888\033[0;37m \033[0;97m888888\033[0;37m \033[0;97m8888b.\033[0;37m \033[0;97mdP\"\"b8\033[0;37m \033[0;97m888888\033[0;37m \033[0m")
    print("\033[0;37m \033[0;95m88\033[0;37m \033[0;95m88__dP\033[0;37m \033[0;95m88\033[0;37m \033[0;95m88\033[0;37m \033[0;95m`Ybo.\"\033[0;37m \033[0;95m88\033[0;37m \033[0;95m88__\033[0;37m \033[0;95m8I\033[0;37m \033[0;95mYb\033[0;37m \033[0;95mdP\033[0;37m \033[0;95m`\"\033[0;37m \033[0;95m88__\033[0;37m \033[0m")
    print("\033[0;37m \033[0;35m88\033[0;37m \033[0;35m88\"Yb\033[0;37m \033[0;35mY8\033[0;37m \033[0;35m8P\033[0;37m \033[0;35mo.`Y8b\033[0;37m \033[0;35m88\033[0;37m \033[0;35m88\"\"\033[0;37m \033[0;35m8I\033[0;37m \033[0;35mdY\033[0;37m \033[0;35mYb\033[0;37m \033[0;35m\"88\033[0;37m \033[0;35m88\"\"\033[0;37m \033[0m")
    print("\033[0;37m \033[0;90m88\033[0;37m \033[0;90m88\033[0;37m \033[0;90mYb\033[0;37m \033[0;90m`YbodP'\033[0;37m \033[0;90m8bodP'\033[0;37m \033[0;90m88\033[0;37m \033[0;90m888888\033[0;37m \033[0;90m8888Y\"\033[0;37m \033[0;90mYboodP\033[0;37m \033[0;90m888888\033[0;37m \033[0m")
    print("")
    print(" Trustedge - TPM-Assisted Secure Attestation Framework for AI Agents\n")
    print("Author: Surendra S")
    print("GitHub: github.com/SurendraS26/trustedge\n")
    print("trustedge-c1")
    print("type a task and press enter, or 'q' to quit")
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        task = input("> ").strip()
        if task.lower() in ("q", "quit", "exit"):
            break
        if not task:
            continue
        asyncio.run(run_task(history, task))


if __name__ == "__main__":
    main()
