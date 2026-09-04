"""
TrustEdge c3 — Framework API
Receives action requests from the c1 AI agent and routes them
through the full TrustEdge security pipeline.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from policy_engine.policy_engine import is_sensitive
from integrity_monitor.integrity_monitor import run_integrity_check
from attestation_manager.attestation_manager import request_quote
from verifier.verifier import verify_quote
from alerts.alert_log import write_alert

app = FastAPI(title="TrustEdge Framework", version="1.0.0")


class ActionRequest(BaseModel):
    action: str          # e.g. "read", "delete", "execute", "query"
    target: str          # e.g. "/etc/passwd", "database:users"
    reasoning: str = ""  # justification from the agent


class ActionResponse(BaseModel):
    allowed: bool
    reason: str


@app.post("/evaluate", response_model=ActionResponse)
async def evaluate(request: ActionRequest):
    """
    Main pipeline entry point.
    c1 agent POSTs every action here before executing it.
    """

    # ── Step 1: Policy Engine ────────────────────────────────────────────
    sensitive = is_sensitive(request.action, request.target)

    if not sensitive:
        return ActionResponse(allowed=True, reason="non-sensitive action, directly allowed")

    # ── Step 2: Integrity Monitor ────────────────────────────────────────
    integrity_ok, failed_files = run_integrity_check()

    if not integrity_ok:
        reason = f"integrity check failed: {failed_files}"
        write_alert(
            action=request.action,
            target=request.target,
            reason=reason
        )
        return ActionResponse(allowed=False, reason=reason)

    # ── Step 3: Attestation Manager ──────────────────────────────────────
    quote_data = request_quote()

    if quote_data is None:
        reason = "attestation failed: could not obtain TPM quote"
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    # ── Step 4: Verifier ─────────────────────────────────────────────────
    verified, verify_reason = verify_quote(quote_data)

    if not verified:
        reason = f"quote verification failed: {verify_reason}"
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    return ActionResponse(allowed=True, reason="attestation passed")


@app.get("/health")
async def health():
    return {"status": "ok"}

