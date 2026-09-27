import os
import subprocess

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()


class ExecRequest(BaseModel):
    script: str


@app.post("/execute")
def execute(req: ExecRequest):
    env = os.environ.copy()
    env.setdefault("WAYLAND_DISPLAY", "wayland-1")
    env.setdefault("XDG_RUNTIME_DIR", "/tmp/xdg-runtime")
    env.setdefault("DISPLAY", ":0")  # Xwayland, started lazily by Hyprland for X11 apps

    try:
        result = subprocess.run(
            ["bash", "-c", req.script],
            capture_output=True, text=True, timeout=60, env=env,
        )
        return {"ok": result.returncode == 0, "output": (result.stdout + result.stderr)[:4000]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "script timed out after 60s"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "output": str(exc)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

