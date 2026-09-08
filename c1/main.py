import sys
from agent.ollama_client import OllamaClient
from agent.tool_router import request_action, ActionDenied


def run_shell_command(command: str):
    try:
        request_action("run_shell_command", {"command": command})
    except ActionDenied as e:
        print(f"[DENIED] {e.reason}")
        return
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout or result.stderr)


def read_file(path: str):
    try:
        request_action("read_file", {"path": path})
    except ActionDenied as e:
        print(f"[DENIED] {e.reason}")
        return
    with open(path, "r") as f:
        print(f.read())


def main():
    print("TrustEdge Agent (c1) -- CLI mode. Type a task, or 'exit'.")
    client = OllamaClient()

    while True:
        try:
            task = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if task.lower() in ("exit", "quit"):
            break
        if not task:
            continue

        response = client.chat(messages=[{"role": "user", "content": task}])
        print(response.get("message", {}).get("content", ""))

        # NOTE: wiring the model's tool-call output to run_shell_command /
        # read_file (via tool_router) is the next integration step once a
        # specific tool-calling schema is chosen for the selected model.


if __name__ == "__main__":
    sys.exit(main())
