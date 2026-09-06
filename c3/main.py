from fastapi import FastAPI
from pydantic import BaseModel

from policy_engine.policy_engine import is_sensitive
from integrity_monitor.integrity_monitor import run_integrity_check
from attestation_manager.attestation_manager import request_quote
from verifier.verifier import verify_quote
from alerts.alert_log import write_alert

app = FastAPI(title="TrustEdge c3")


class Action(BaseModel):
    action: str
    target: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/policy/check")
def policy_check(action: str, target: str):
    return {"action": action, "target": target, "sensitive": is_sensitive(action, target)}


@app.post("/evaluate")
def evaluate(req: Action):
    # Step 1: policy check
    if not is_sensitive(req.action, req.target):
        return {"allowed": True, "reason": "non-sensitive"}

    # Step 2: integrity check
    ok, failed = run_integrity_check()
    if not ok:
        reason = f"integrity failed: {failed}"
        write_alert(req.action, req.target, reason)
        return {"allowed": False, "reason": reason}

    # Step 3: get TPM quote
    quote = request_quote()
    if quote is None:
        reason = "attestation failed"
        write_alert(req.action, req.target, reason)
        return {"allowed": False, "reason": reason}

    # Step 4: verify quote
    verified, why = verify_quote(quote)
    if not verified:
        reason = f"quote failed: {why}"
        write_alert(req.action, req.target, reason)
        return {"allowed": False, "reason": reason}

    return {"allowed": True, "reason": "attestation passed"}
