import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any, List

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from src.canvas_runtime.canvas_manager import (
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
from src.canvas_runtime.package_manager import ensure_user_site

ensure_user_site()

from src.daemon import DotDaemon, DotDaemonError
from src.log_buffer import get_logs, log_buffer_handler
from src.service_config import ServercConfig
from src.token_store import TokenStore, TokenStoreError


# MARK: - INIT

app = FastAPI()

FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

NO_BROWSER_MODE = os.getenv("DOTCANVAS_NO_BROWSER", "").strip().lower() in {"1", "true", "yes", "on"}


# logger
dot_logger = logging.getLogger("dot")
if log_buffer_handler not in dot_logger.handlers:
    log_buffer_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
    dot_logger.addHandler(log_buffer_handler)
dot_logger.setLevel(logging.INFO)

logger = logging.getLogger("dot.server")

# token

try:
    token_store = TokenStore()
except TokenStoreError as exc:  # pragma: no cover - startup validation
    logger.error("Failed to load API token store: %s", exc)
    token_store = None
else:
    if NO_BROWSER_MODE and not token_store.list_tokens():
        token, _ = token_store.create_token(name="auto")
        message = f"Generated API token for no-browser mode: {token}"
        logger.info(message)
        print(message, flush=True)

# daemon

daemon_boot_error: str | None = None

try:
    dot_daemon = DotDaemon()
except Exception as exc:  # noqa: BLE001 - surface boot problems in logs
    logger.warning("Failed to initialise DotDaemon: %s", exc)
    dot_daemon = None
    daemon_boot_error = str(exc)

# server mode

if not NO_BROWSER_MODE:
    if FRONTEND_ASSETS.exists():
        app.mount("/ui/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="ui-assets")
    else:
        logging.getLogger("dot.server").warning(
            "Frontend assets directory %s is missing. Run `npm run build` in the frontend folder.",
            FRONTEND_ASSETS,
        )
else:
    logging.getLogger("dot.server").info("Running in no-browser mode; frontend routes are disabled.")


# MARK: - Helpers

def frontend_index() -> FileResponse:
    if NO_BROWSER_MODE:
        raise HTTPException(status_code=404, detail="Frontend is disabled in no-browser mode")
    index_path = FRONTEND_DIST / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=503, detail="Frontend build is missing. Run npm run build in frontend/.")
    return FileResponse(index_path)


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


def get_token_store_or_503() -> TokenStore:
    if token_store is None:
        raise HTTPException(status_code=503, detail="Token store is unavailable")
    return token_store


def require_frontend_enabled() -> None:
    if NO_BROWSER_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint disabled in no-browser mode",
        )


def require_bearer_token(authorization: str = Header(default="")) -> str:
    store = get_token_store_or_503()
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not store.verify(credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials


def _parse_params_json(payload: str | None) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - input validation
        raise HTTPException(status_code=400, detail=f"Invalid params JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="params must be a JSON object")
    return data


# MARK: - Payload models

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
    disabled: bool = False


class DeviceConfigPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    device_id: str
    schedules: list[ScheduleConfigPayload] = Field(default_factory=list)


class ServiceConfigPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    api_key: str
    disabled: bool = False
    devices: list[DeviceConfigPayload] = Field(default_factory=list)


class TokenCreatePayload(BaseModel):
    name: str | None = ""


class ScheduleTriggerPayload(BaseModel):
    schedule_name: str = Field(min_length=1)
    params_override: dict[str, Any] | None = None


class DeviceCanvasPayload(BaseModel):
    device_name: str = Field(min_length=1)
    canvas_id: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ManualScheduleTriggerPayload(BaseModel):
    device_id: str = Field(min_length=1)
    schedule_name: str = Field(min_length=1)


# MARK: - Frontend routes

@app.get("/", include_in_schema=False)
def root():
    if NO_BROWSER_MODE:
        return {"message": "DotCanvas API is running in no-browser mode.", "documentation": "/docs"}
    return RedirectResponse(url="/ui/daemon")


@app.get("/ui", include_in_schema=False)
def ui_root():
    if NO_BROWSER_MODE:
        raise HTTPException(status_code=404, detail="Frontend is disabled in no-browser mode")
    return frontend_index()


@app.get("/ui/{full_path:path}", include_in_schema=False)
def ui_fallback(full_path: str):  # noqa: ARG001 - route param for matching
    if NO_BROWSER_MODE:
        raise HTTPException(status_code=404, detail="Frontend is disabled in no-browser mode")
    candidate = (FRONTEND_DIST / full_path).resolve()
    try:
        candidate.relative_to(FRONTEND_DIST)
    except ValueError as exc:  # path traversal attempt
        raise HTTPException(status_code=404, detail="Not found") from exc
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    return frontend_index()


# MARK: - Canvas editor

@app.get("/canvases")
def get_canvases(_: None = Depends(require_frontend_enabled)):
    return {"canvases": list_canvases()}


@app.get("/canvases/{canvas_id}")
def get_canvas(
    canvas_id: str,
    params: str | None = Query(default=None),
    _: None = Depends(require_frontend_enabled),
):
    try:
        definition = load_canvas(canvas_id)
        params_dict = _parse_params_json(params)
        view_configs = load_view_configs(canvas_id, params=params_dict)
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": definition.canvas_id,
        "name": definition.name,
        "views": [{"id": view.view_id, "code": view.code} for view in definition.views],
        "view_configs": view_configs,
    }


@app.post("/canvases")
def create_canvas_endpoint(
    payload: CanvasCreatePayload, _: None = Depends(require_frontend_enabled)
):
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
def update_canvas(
    canvas_id: str,
    payload: CanvasUpdatePayload,
    params: str | None = Query(default=None),
    _: None = Depends(require_frontend_enabled),
):
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

    params_dict = _parse_params_json(params)
    view_configs = load_view_configs(updated.canvas_id, params=params_dict)
    return {
        "id": updated.canvas_id,
        "name": updated.name,
        "views": [{"id": view.view_id, "code": view.code} for view in updated.views],
        "view_configs": view_configs,
    }


@app.get("/canvases/{canvas_id}/view-configs")
def get_canvas_view_configs(
    canvas_id: str,
    params: str | None = Query(default=None),
    _: None = Depends(require_frontend_enabled),
):
    try:
        configs = load_view_configs(canvas_id, params=_parse_params_json(params))
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"view_configs": configs}


@app.get("/canvases/{canvas_id}/preview")
def preview_canvas(
    canvas_id: str,
    params: str | None = Query(default=None),
    _: None = Depends(require_frontend_enabled),
):
    try:
        image = render_canvas(canvas_id, params=_parse_params_json(params))
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@app.get("/views")
def get_available_views(_: None = Depends(require_frontend_enabled)):
    return {"views": list_available_views()}

# MARK: - Daemon config

@app.get("/logs")
def get_recent_logs(
    since: int = Query(default=0, ge=0, description="Return entries with id greater than this value"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of entries to return"),
    _: None = Depends(require_frontend_enabled),
):
    logs = get_logs(since=since, limit=limit)
    return {"logs": logs}


@app.get("/daemon/status")
def get_daemon_status(_: None = Depends(require_frontend_enabled)):
    return build_daemon_payload(dot_daemon)


@app.post("/daemon/start")
def start_daemon(_: None = Depends(require_frontend_enabled)):
    try:
        daemon = get_daemon(allow_reinitialise=True)
        daemon.start()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_daemon_payload(daemon)


@app.post("/daemon/stop")
def stop_daemon(_: None = Depends(require_frontend_enabled)):
    try:
        daemon = get_daemon()
        daemon.stop()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_daemon_payload(daemon)


@app.post("/daemon/restart")
def restart_daemon(_: None = Depends(require_frontend_enabled)):
    try:
        daemon = get_daemon(allow_reinitialise=True)
        daemon.restart()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_daemon_payload(daemon)


# MARK: - Service config

@app.get("/config")
def get_service_config(_: None = Depends(require_frontend_enabled)):
    try:
        config = ServercConfig()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"config": config.as_dict()}


@app.put("/config")
def update_service_config(
    payload: ServiceConfigPayload, _: None = Depends(require_frontend_enabled)
):
    try:
        config = ServercConfig()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    incoming = payload.model_dump(mode="python")
    merged = config.as_dict()
    merged["api_key"] = incoming.get("api_key", "")
    merged["disabled"] = incoming.get("disabled", merged.get("disabled", False))
    merged["devices"] = incoming.get("devices", [])

    errors = config.update_and_save(merged)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    return {"config": config.as_dict()}


@app.post("/config/schedules/trigger")
def trigger_schedule_from_config(
    payload: ManualScheduleTriggerPayload,
    _: None = Depends(require_frontend_enabled),
):
    try:
        daemon = get_daemon()
        daemon.refresh_config()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    devices = daemon.config.cfg.get("devices", [])
    device = next((item for item in devices if item.get("device_id") == payload.device_id), None)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    schedule = next((sched for sched in device.get("schedules", []) if sched.get("name") == payload.schedule_name), None)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    canvas_id = schedule.get("canvas_id")
    if not canvas_id:
        raise HTTPException(status_code=400, detail="Schedule is missing a canvas_id")

    task = daemon.build_task_for_device(
        device=device,
        canvas_id=canvas_id,
        params=schedule.get("params", {}),
        name=schedule.get("name", "manual"),
    )
    results = daemon.run_tasks([task])
    return {"result": results[0] if results else None}


# MARK: - Token management

@app.get("/tokens")
def list_tokens(_: None = Depends(require_frontend_enabled)):
    store = get_token_store_or_503()
    return {"tokens": store.list_tokens()}


@app.post("/tokens", status_code=status.HTTP_201_CREATED)
def create_token(
    payload: TokenCreatePayload, _: None = Depends(require_frontend_enabled)
):
    store = get_token_store_or_503()
    token, record = store.create_token(name=(payload.name or ""))
    return {"token": token, "record": record}


@app.delete("/tokens/{token_id}")
def delete_token(token_id: str, _: None = Depends(require_frontend_enabled)):
    store = get_token_store_or_503()
    removed = store.delete_token(token_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"status": "deleted"}


# MARK: - API endpoints

@app.post("/api/schedules/trigger")
def trigger_schedules(payload: ScheduleTriggerPayload, _: str = Depends(require_bearer_token)):
    try:
        daemon = get_daemon()
        daemon.refresh_config()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not daemon.config.get_api_key():
        raise HTTPException(status_code=400, detail="API key is not configured")

    tasks = daemon.build_tasks_by_name(payload.schedule_name, payload.params_override)
    if not tasks:
        raise HTTPException(status_code=404, detail="No schedules found with that name")

    results = daemon.run_tasks(tasks)
    return {"triggered": len(results), "results": results}


@app.post("/api/devices/send-canvas")
def send_canvas_to_device(payload: DeviceCanvasPayload, _: str = Depends(require_bearer_token)):
    try:
        daemon = get_daemon()
        daemon.refresh_config()
    except DotDaemonError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not daemon.config.get_api_key():
        raise HTTPException(status_code=400, detail="API key is not configured")

    devices = daemon.config.cfg.get("devices", [])
    target = next((device for device in devices if device.get("name") == payload.device_name), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Device not found")

    task = daemon.build_task_for_device(
        device=target,
        canvas_id=payload.canvas_id,
        params=payload.params,
        name=f"manual:{payload.canvas_id}",
    )
    results = daemon.run_tasks([task])
    return {"result": results[0] if results else None}
