"""
TrustEdge - Container 3: Framework

FastAPI service exposing /evaluate. Every action proposed by the agent in
c1 flows through, in order:

    Interceptor -> Policy Engine -> Baseline Store -> Verifier (TPM) -> Alert Log

Non-sensitive actions are allowed immediately by the Policy Engine.
Sensitive actions must pass integrity verification (baseline hash check)
and TPM attestation before the operator is given a final ALLOW/BLOCK
prompt (with a 30s timeout, after which the automated decision stands).
Every outcome, allowed or blocked, is written to the audit log.
"""

import logging
import os

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from modules.interceptor import Interceptor
from modules.policy_engine import PolicyEngine
from modules.baseline_store import BaselineStore
from modules.verifier import Verifier
from modules.alert_log import AlertLog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [c3] %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("main")

app = FastAPI(title="TrustEdge Framework")

interceptor = Interceptor()
policy_engine = PolicyEngine()
baseline_store = BaselineStore()
alert_log = AlertLog()

baseline_store.establish_baseline_if_empty()


class ActionRequest(BaseModel):
    action: str
    target: str
    reasoning: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/evaluate")
def evaluate(request: ActionRequest):
    try:
        intercepted = interceptor.capture(request.model_dump())
    except ValueError as exc:
        log.warning("rejected malformed request: %s", exc)
        return {"decision": "BLOCK", "reason": f"malformed request: {exc}"}

    action = intercepted.action
    target = intercepted.target
    reasoning = intercepted.reasoning

    policy_result = policy_engine.evaluate(action, target)
    classification = policy_result["classification"]

    # Non-sensitive allow, or an outright policy block, needs no attestation.
    if policy_result["decision"] in ("ALLOW", "BLOCK"):
        alert_log.record(
            action, target, reasoning, classification,
            attested="n/a", final_decision=policy_result["decision"],
            reason=policy_result["reason"],
        )
        return {"decision": policy_result["decision"], "reason": policy_result["reason"]}

    # Sensitive action: verify framework integrity, then attest via TPM.
    is_intact, mismatched, combined_digest = baseline_store.check_integrity()

    if not is_intact:
        reason = f"integrity check failed, tampered files: {mismatched}"
        log.error(reason)
        alert_log.record(
            action, target, reasoning, classification,
            attested=False, final_decision="BLOCK", reason=reason,
        )
        return {"decision": "BLOCK", "reason": reason}

    attestation = Verifier().attest(combined_digest)

    if not attestation["attested"]:
        reason = f"attestation failed: {attestation['reason']}"
        log.error(reason)
        alert_log.record(
            action, target, reasoning, classification,
            attested=False, final_decision="BLOCK", reason=reason,
        )
        return {"decision": "BLOCK", "reason": reason}

    # Integrity and attestation passed. Give the operator the final call,
    # with the attested-safe automated decision (ALLOW) as the default if
    # the popup times out or no display is available.
    operator_choice = alert_log.prompt_operator(action, target, reasoning)
    final_decision = operator_choice or "ALLOW"
    reason = (
        f"operator chose {operator_choice}"
        if operator_choice
        else "attestation succeeded, no operator response, defaulted to ALLOW"
    )

    alert_log.record(
        action, target, reasoning, classification,
        attested=True, final_decision=final_decision, reason=reason,
    )
    return {"decision": final_decision, "reason": reason}


if __name__ == "__main__":
    port = int(os.environ.get("FRAMEWORK_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
