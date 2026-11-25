import asyncio
import hashlib
import json
import logging
import os
import time
import urllib.request

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import logstore
import dashboard
from interceptor import intercept
from verifier import Verifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [c3] %(message)s")
log = logging.getLogger("c3")

app = FastAPI(title="trustedge-c3")
logstore.init_db()
dashboard.render()

C4_EXEC_URL = os.environ.get("C4_EXEC_URL", "http://trustedge-c4:9000/execute")


def call_c4(script: str) -> dict:
    body = json.dumps({"script": script}).encode()
    req = urllib.request.Request(
        C4_EXEC_URL, data=body, headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/log")
def get_log(limit: int = 20):
    return logstore.recent(limit)


@app.websocket("/agent-link")
async def agent_link(websocket: WebSocket):
    await websocket.accept()
    log.info("agent connected")
    try:
        while True:
            payload = await websocket.receive_json()
            await _handle_proposal(websocket, payload)
    except WebSocketDisconnect:
        log.info("agent disconnected")


async def _handle_proposal(websocket: WebSocket, payload: dict):
    script = (payload.get("target") or "").strip()
    reasoning = payload.get("reasoning", "")

    result = intercept(script)

    if result["decision"] == "BLOCK":
        logstore.record(script, reasoning, "BLOCK", result["reason"])
        dashboard.render()
        log.info("blocked: %s", result["reason"])
        await websocket.send_json({"type": "verdict", "decision": "BLOCK", "reason": result["reason"]})
        return

    digest = hashlib.sha256(f"{script}:{time.time()}".encode()).hexdigest()
    attestation = await asyncio.to_thread(Verifier().attest, digest)
    if not attestation["attested"]:
        reason = f"attestation failed: {attestation['reason']}"
        logstore.record(script, reasoning, "BLOCK", reason)
        dashboard.render()
        log.warning(reason)
        await websocket.send_json({"type": "verdict", "decision": "BLOCK", "reason": reason})
        return

    await websocket.send_json({"type": "confirm", "script": script, "reason": result["reason"]})
    response = await websocket.receive_json()
    decision = response.get("decision", "BLOCK")

    if decision != "ALLOW":
        reason = "operator declined"
        logstore.record(script, reasoning, "BLOCK", reason)
        dashboard.render()
        log.info("operator declined: %s", script[:60])
        await websocket.send_json({"type": "verdict", "decision": "BLOCK", "reason": reason})
        return

    logstore.record(script, reasoning, "ALLOW", "operator approved")
    dashboard.render()
    log.info("approved, executing on c4: %s", script[:60])

    try:
        exec_result = await asyncio.to_thread(call_c4, script)
    except Exception as exc:  # noqa: BLE001
        await websocket.send_json({"type": "result", "ok": False, "output": f"could not reach c4: {exc}"})
        return

    await websocket.send_json({
        "type": "result", "ok": exec_result.get("ok", False), "output": exec_result.get("output", ""),
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("FRAMEWORK_PORT", 8000)))
