"""
TrustEdge c3 — Framework API
Receives action requests from c1 and routes them through the full pipeline.
"""

import logging

from fastapi import FastAPI
from pydantic import BaseModel

from policy_engine.policy_engine import is_sensitive
from integrity_monitor.integrity_monitor import run_integrity_check
from attestation_manager.attestation_manager import request_quote
from verifier.verifier import verify_quote
from alerts.alert_log import write_alert

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("trustedge")

app = FastAPI(title="TrustEdge Framework", version="1.0.0")


class ActionRequest(BaseModel):
    action:    str
    target:    str
    reasoning: str = ""


class ActionResponse(BaseModel):
    allowed: bool
    reason:  str


@app.post("/evaluate", response_model=ActionResponse)
async def evaluate(request: ActionRequest):
    log.info(f"Evaluating: action={request.action} target={request.target}")

    # ── Step 1: Policy Engine ────────────────────────────────────────────
    try:
        sensitive = is_sensitive(request.action, request.target)
    except Exception as e:
        log.error(f"Policy engine error: {e}")
        return ActionResponse(allowed=False, reason=f"policy engine error: {e}")

    if not sensitive:
        log.info("Non-sensitive — directly allowed")
        return ActionResponse(allowed=True, reason="non-sensitive action, directly allowed")

    log.info("Sensitive action detected — running integrity check")

    # ── Step 2: Integrity Monitor ────────────────────────────────────────
    try:
        integrity_ok, failed_files = run_integrity_check()
    except Exception as e:
        log.error(f"Integrity monitor error: {e}")
        reason = f"integrity monitor error: {e}"
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    if not integrity_ok:
        reason = f"integrity check failed — modified files: {', '.join(failed_files)}"
        log.warning(reason)
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    log.info("Integrity check passed — requesting TPM quote")

    # ── Step 3: Attestation Manager ──────────────────────────────────────
    try:
        quote_data = request_quote()
    except Exception as e:
        log.error(f"Attestation manager error: {e}")
        reason = f"attestation error: {e}"
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    if quote_data is None:
        reason = "attestation failed — could not obtain TPM quote"
        log.warning(reason)
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    log.info("Quote obtained — verifying")

    # ── Step 4: Verifier ─────────────────────────────────────────────────
    try:
        verified, verify_reason = verify_quote(quote_data)
    except Exception as e:
        log.error(f"Verifier error: {e}")
        reason = f"verifier error: {e}"
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    if not verified:
        reason = f"quote verification failed: {verify_reason}"
        log.warning(reason)
        write_alert(action=request.action, target=request.target, reason=reason)
        return ActionResponse(allowed=False, reason=reason)

    log.info(f"ALLOW: action={request.action} target={request.target}")
    return ActionResponse(allowed=True, reason="attestation passed")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/policy/check")
async def policy_check(action: str, target: str):
    """Quick endpoint to test the policy engine standalone."""
    return {"sensitive": is_sensitive(action, target)}
