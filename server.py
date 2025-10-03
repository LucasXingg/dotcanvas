from io import BytesIO
from typing import List

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


app = FastAPI()
app.mount("/ui", StaticFiles(directory="pages", html=True), name="pages")


class ViewPayload(BaseModel):
    id: str
    code: str


class CanvasUpdatePayload(BaseModel):
    name: str
    views: List[ViewPayload]


class CanvasCreatePayload(BaseModel):
    canvas_id: str
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
        definition = create_canvas(payload.canvas_id, payload.name)
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
        )
    except CanvasNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CanvasManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    view_configs = load_view_configs(canvas_id)
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

