import os
import sqlite3
import time
from flask import Flask, request, jsonify

from framework import policy_engine, popup_gate, integrity_monitor
from framework import attestation_manager, verifier, baseline_store

app = Flask(__name__)

AUDIT_DB = os.path.join(os.path.dirname(__file__), "..", "audit", "audit_log.db")
AUDIT_MODE = os.environ.get("AUDIT_LOG_MODE", "allow_and_deny")
POPUP_TIMEOUT = int(os.environ.get("POPUP_TIMEOUT_SECONDS", 30))
POPUP_TIMEOUT_ACTION = os.environ.get("POPUP_TIMEOUT_ACTION", "deny")


def _audit_log(action_type: str, decision: str, reason: str):
    if AUDIT_MODE == "deny_only" and decision == "allow":
        return
    os.makedirs(os.path.dirname(AUDIT_DB), exist_ok=True)
    conn = sqlite3.connect(AUDIT_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS audit (ts REAL, action_type TEXT, decision TEXT, reason TEXT)")
    conn.execute("INSERT INTO audit VALUES (?, ?, ?, ?)", (time.time(), action_type, decision, reason))
    conn.commit()
    conn.close()


@app.route("/evaluate", methods=["POST"])
def evaluate():
    body = request.get_json(force=True)
    action_type = body.get("action_type", "unknown")
    details = body.get("details", {})

    classification = policy_engine.classify(action_type)

    if not classification["sensitive"]:
        _audit_log(action_type, "allow", "non-sensitive, allowed directly")
        return jsonify({"decision": "allow", "reason": "non-sensitive"})

    urgency = classification["urgency"]
    human_decision = popup_gate.ask_popup(
        action_type, details, urgency,
        timeout_seconds=POPUP_TIMEOUT,
        timeout_action=POPUP_TIMEOUT_ACTION,
    )

    if human_decision != "allow":
        _audit_log(action_type, "deny", "blocked by human via popup")
        return jsonify({"decision": "deny", "reason": "blocked by user"})

    if not baseline_store.is_initialized():
        _audit_log(action_type, "deny", "baseline not initialized")
        return jsonify({"decision": "deny", "reason": "baseline not initialized"})

    fresh_measurements = integrity_monitor.measure_all()
    evidence = attestation_manager.run_attestation_cycle(fresh_measurements)
    result = verifier.verify(evidence, fresh_measurements)

    _audit_log(action_type, result["decision"], result["reason"])
    return jsonify(result)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
