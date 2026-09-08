"""
TrustEdge - Container 1: AI Agent, web edition

Same pipeline as main.py's `task>` loop (ask Ollama for one JSON action,
submit it to c3's /evaluate, execute only on ALLOW) exposed as a small
Flask app instead of a terminal prompt. main.py / the CLI is untouched and
keeps working exactly as before - this just gives the same agent a browser
front end on a different port.
"""

import logging
import os

from flask import Flask, jsonify, render_template_string, request
import requests

from executor import execute

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [c1-web] %(levelname)s %(message)s",
)
log = logging.getLogger("agent-web")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = "trustedge-agent"
FRAMEWORK_URL = os.environ.get("FRAMEWORK_URL", "http://c3-framework:8000/evaluate")
REQUEST_TIMEOUT = 60
WEB_PORT = int(os.environ.get("AGENT_WEB_PORT", 5000))

app = Flask(__name__)


def get_agent_decision(task_description):
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
        decision = __import__("json").loads(raw_text)
    except ValueError:
        log.error("model did not return valid JSON: %s", raw_text)
        return None

    if "action" not in decision or not str(decision["action"]).strip():
        log.error("model response missing required field: action (raw: %s)", raw_text)
        return None

    decision.setdefault("target", "")
    decision.setdefault("reasoning", "")
    return decision


def submit_for_evaluation(decision):
    try:
        resp = requests.post(FRAMEWORK_URL, json=decision, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.error("could not reach framework at %s: %s", FRAMEWORK_URL, exc)
        return {"decision": "ERROR", "reason": str(exc)}


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/task", methods=["POST"])
def api_task():
    task = (request.get_json(silent=True) or {}).get("task", "").strip()
    if not task:
        return jsonify({"error": "empty task"}), 400

    decision = get_agent_decision(task)
    if decision is None:
        return jsonify({"error": "agent failed to produce a valid decision, try rephrasing"}), 200

    if decision.get("action") == "none":
        return jsonify({"decision": decision, "verdict": None, "execution": None})

    verdict = submit_for_evaluation(decision)

    execution = None
    if verdict.get("decision") == "ALLOW":
        execution = execute(decision)

    return jsonify({"decision": decision, "verdict": verdict, "execution": execution})


PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>TrustEdge Agent</title>
  <style>
    body { font-family: ui-monospace, monospace; max-width: 720px; margin: 40px auto; background:#111; color:#ddd; }
    h1 { font-size: 18px; }
    #task { width: 100%; padding: 10px; font-family: inherit; font-size: 14px; box-sizing: border-box; }
    button { padding: 8px 16px; margin-top: 8px; cursor: pointer; }
    .entry { border: 1px solid #444; border-radius: 6px; padding: 12px; margin-top: 16px; white-space: pre-wrap; }
    .ALLOW { border-color: #3c3; } .BLOCK { border-color: #c33; } .ERROR { border-color: #c93; }
    .row { color: #999; }
  </style>
</head>
<body>
  <h1>TrustEdge Agent (web)</h1>
  <textarea id="task" rows="2" placeholder="e.g. write 'hello' to /app/scratch/output.txt"></textarea><br>
  <button onclick="send()">Send</button>
  <div id="log"></div>

<script>
async function send() {
  const taskEl = document.getElementById("task");
  const task = taskEl.value.trim();
  if (!task) return;
  taskEl.value = "";

  const res = await fetch("/api/task", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({task})
  });
  const data = await res.json();
  const logEl = document.getElementById("log");
  const div = document.createElement("div");

  if (data.error) {
    div.className = "entry ERROR";
    div.textContent = "error: " + data.error;
  } else {
    const d = data.decision, v = data.verdict, e = data.execution;
    const cls = v ? v.decision : "ALLOW";
    div.className = "entry " + cls;
    let text = `action    : ${d.action}\\ntarget    : ${d.target}\\nreasoning : ${d.reasoning}`;
    if (v) text += `\\nverdict   : ${v.decision}\\nreason    : ${v.reason || ""}`;
    if (e) text += `\\nexecuted  : ${e.ok ? "succeeded" : "failed"}\\noutput    : ${e.output}`;
    div.textContent = text;
  }
  logEl.prepend(div);
}
document.getElementById("task").addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); send(); }
});
</script>
</body>
</html>
"""


def main():
    log.info("starting TrustEdge web agent on :%d", WEB_PORT)
    app.run(host="0.0.0.0", port=WEB_PORT)


if __name__ == "__main__":
    main()
