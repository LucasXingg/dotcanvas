import logging
from io import BytesIO
from typing import Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

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
from src.log_buffer import get_logs, log_buffer_handler
from src.service_config import ServercConfig


app = FastAPI()
app.mount("/ui", StaticFiles(directory="pages", html=True), name="pages")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/daemon.html")

# config loggers
dot_logger = logging.getLogger("dot")
if log_buffer_handler not in dot_logger.handlers:
    log_buffer_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
    dot_logger.addHandler(log_buffer_handler)
dot_logger.setLevel(logging.INFO)

logger = logging.getLogger("dot.server")

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

    status = daemon.get_status()
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


class ScheduleConfigPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    canvas_id: str
    cron: str
    params: dict[str, Any] = Field(default_factory=dict)


class DeviceConfigPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    device_id: str
    schedules: list[ScheduleConfigPayload] = Field(default_factory=list)


class ServiceConfigPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    api_key: str
    devices: list[DeviceConfigPayload] = Field(default_factory=list)


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


@app.get("/logs")
def get_recent_logs(
    since: int = Query(default=0, ge=0, description="Return entries with id greater than this value"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of entries to return"),
):
    logs = get_logs(since=since, limit=limit)
    return {"logs": logs}


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


@app.get("/config")
def get_service_config():
    try:
        config = ServercConfig()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"config": config.as_dict()}


@app.put("/config")
def update_service_config(payload: ServiceConfigPayload):
    try:
        config = ServercConfig()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    incoming = payload.model_dump(mode="python")
    merged = config.as_dict()
    merged["api_key"] = incoming.get("api_key", "")
    merged["devices"] = incoming.get("devices", [])

    errors = config.update_and_save(merged)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    return {"config": config.as_dict()}
