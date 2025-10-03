import logging
from io import BytesIO
from typing import Any, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from canvas.canvas_manager import (
    CanvasManagerError,
    CanvasNotFoundError,
    create_canvas,
    list_available_views,
    list_canvases,
    load_canvas,
    load_view_configs,
    render_canvas,
    save_canvas,
)

from src.daemon import DotDaemon, DotDaemonError


app = FastAPI()
app.mount("/ui", StaticFiles(directory="pages", html=True), name="pages")


logger = logging.getLogger(__name__)


daemon_boot_error: str | None = None

try:
    dot_daemon = DotDaemon()
except Exception as exc:  # noqa: BLE001 - surface boot problems in logs
    logger.warning("Failed to initialise DotDaemon: %s", exc)
    dot_daemon = None
    daemon_boot_error = str(exc)


def get_daemon(allow_reinitialise: bool = False) -> DotDaemon:
    global dot_daemon
    global daemon_boot_error

    if dot_daemon is None and allow_reinitialise:
        try:
            dot_daemon = DotDaemon()
            daemon_boot_error = None
        except Exception as exc:  # noqa: BLE001
            daemon_boot_error = str(exc)
            raise DotDaemonError(daemon_boot_error) from exc

    if dot_daemon is None:
        raise DotDaemonError(daemon_boot_error or "Daemon is unavailable")

    return dot_daemon


def build_daemon_payload(daemon: DotDaemon | None) -> dict[str, Any]:
    if daemon is None:
        return {
            "running": False,
            "started_at": None,
            "task_count": 0,
            "tasks": [],
            "error": daemon_boot_error,
        }

    status = daemon.status()
    status["error"] = daemon_boot_error
    return status


class ViewPayload(BaseModel):
    id: str
    code: str


class CanvasUpdatePayload(BaseModel):
    name: str
    views: List[ViewPayload]
    new_id: str | None = None


class CanvasCreatePayload(BaseModel):
    # canvas_id: str
    name: str


@app.get("/canvases")
def get_canvases():
    return {"canvases": list_canvases()}


@app.get("/canvases/{canvas_id}")
def get_canvas(canvas_id: str):
    try:
        definition = load_canvas(canvas_id)
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    view_configs = load_view_configs(canvas_id)
    return {
        "id": definition.canvas_id,
        "name": definition.name,
        "views": [{"id": view.view_id, "code": view.code} for view in definition.views],
        "view_configs": view_configs,
    }


@app.post("/canvases")
def create_canvas_endpoint(payload: CanvasCreatePayload):
    try:
        definition = create_canvas(payload.name, payload.name)
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": definition.canvas_id,
        "name": definition.name,
        "views": [],
    }


@app.put("/canvases/{canvas_id}")
def update_canvas(canvas_id: str, payload: CanvasUpdatePayload):
    try:
        updated = save_canvas(
            canvas_id,
            payload.name,
            [{"id": view.id, "code": view.code} for view in payload.views],
            payload.new_id,
        )
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    view_configs = load_view_configs(updated.canvas_id)
    return {
        "id": updated.canvas_id,
        "name": updated.name,
        "views": [{"id": view.view_id, "code": view.code} for view in updated.views],
        "view_configs": view_configs,
    }


@app.get("/canvases/{canvas_id}/preview")
def preview_canvas(canvas_id: str):
    try:
        image = render_canvas(canvas_id)
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@app.get("/views")
def get_available_views():
    return {"views": list_available_views()}


@app.get("/daemon/status")
def get_daemon_status():
    return build_daemon_payload(dot_daemon)


@app.post("/daemon/start")
def start_daemon():
    try:
        daemon = get_daemon(allow_reinitialise=True)
        daemon.start()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_daemon_payload(daemon)


@app.post("/daemon/stop")
def stop_daemon():
    try:
        daemon = get_daemon()
        daemon.stop()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_daemon_payload(daemon)


@app.post("/daemon/restart")
def restart_daemon():
    try:
        daemon = get_daemon(allow_reinitialise=True)
        daemon.restart()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_daemon_payload(daemon)
