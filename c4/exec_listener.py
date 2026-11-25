import os
import subprocess

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ExecRequest(BaseModel):
    script: str


@app.post("/execute")
def execute(req: ExecRequest):
    env = os.environ.copy()
    env.setdefault("DISPLAY", ":1")
    try:
        result = subprocess.run(["bash", "-c", req.script], capture_output=True,
                                text=True, timeout=300, env=env)
        return {"ok": result.returncode == 0, "output": (result.stdout + result.stderr)[-4000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "script timed out after 300s"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "output": str(exc)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
