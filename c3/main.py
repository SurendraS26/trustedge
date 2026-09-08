#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI
from modules import interceptor, verifier, policy_engine, baseline_store, alert_log

app = FastAPI(title="trustedge framework", version="1.0")

@app.get("/")
def root():
    return {"message": "trustedge framework running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/evaluate")
def evaluate(request: dict):
    action = request.get("action")
    target = request.get("target")
    reasoning = request.get("reasoning", "")

    if not action or not target:
        return {"allowed": False, "reason": "missing action or target"}

    policy_decision = policy_engine.check(action, target)
    if not policy_decision["allowed"]:
        alert_log.log(action, target, policy_decision["reason"])
        return policy_decision

    intercept_result = interceptor.capture(action, target)
    if not intercept_result["allowed"]:
        alert_log.log(action, target, intercept_result["reason"])
        return intercept_result

    verify_result = verifier.verify(target)
    if not verify_result["allowed"]:
        alert_log.log(action, target, verify_result["reason"])
        return verify_result

    return {"allowed": True, "reason": "all checks passed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
