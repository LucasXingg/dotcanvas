"""Utilities for creating, reading, and updating canvas modules."""
from __future__ import annotations

import ast
import importlib
import json
import textwrap
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

from PIL import Image

from .._base_canvas import _BaseCanvas


CANVAS_DIR = Path(__file__).resolve().parents[1]
CANVAS_TEMPLATE = CANVAS_DIR / "_canvas_template.py"


class CanvasManagerError(RuntimeError):
    """Base error for canvas manager operations."""


class CanvasNotFoundError(CanvasManagerError):
    """Raised when a requested canvas file cannot be located."""


@dataclass
class ViewDefinition:
    """Represents the editable portion of a view builder."""

    view_id: str
    code: str  # Body of the staticmethod (indented with 8 spaces when written)


@dataclass
class CanvasDefinition:
    """Serializable representation of a canvas module."""

    canvas_id: str
    name: str
    views: List[ViewDefinition]


def _canvas_file(canvas_id: str) -> Path:
    """Return the path to the canvas module for ``canvas_id``."""

    path = CANVAS_DIR / f"{canvas_id}.py"
    if not path.exists():
        raise CanvasNotFoundError(f"Canvas '{canvas_id}' does not exist")
    return path


def list_canvases() -> List[Dict[str, str]]:
    """Return a summary of all available canvases."""

    canvases: List[Dict[str, str]] = []
    for file in sorted(CANVAS_DIR.glob("*.py")):
        if file.name.startswith("_") or file.name == "__init__.py":
            continue
        try:
            definition = load_canvas(file.stem)
        except CanvasManagerError:
            continue
        canvases.append({
            "id": definition.canvas_id,
            "name": definition.name,
        })
    return canvases


def load_canvas(canvas_id: str) -> CanvasDefinition:
    """Parse a canvas file and return its editable representation."""

    path = _canvas_file(canvas_id)
    source = path.read_text()
    module_ast = ast.parse(source)

    canvas_class = _find_canvas_class(module_ast)
    class_id = _extract_class_id(canvas_class)

    config_assign = _find_config_assignment(module_ast)
    name, ordered_view_ids = _extract_config_metadata(config_assign)

    view_code_map = _extract_view_bodies(canvas_class, source.splitlines())

    views: List[ViewDefinition] = []
    seen: set[str] = set()
    for view_id in ordered_view_ids:
        code = view_code_map.get(view_id, "return {}\n")
        views.append(ViewDefinition(view_id=view_id, code=code))
        seen.add(view_id)

    for extra_id, code in view_code_map.items():
        if extra_id not in seen:
            views.append(ViewDefinition(view_id=extra_id, code=code))

    return CanvasDefinition(canvas_id=class_id, name=name, views=views)


def create_canvas(canvas_id: str, name: str) -> CanvasDefinition:
    """Create a new canvas module from the template."""

    destination = CANVAS_DIR / f"{canvas_id}.py"
    if destination.exists():
        raise CanvasManagerError(f"Canvas '{canvas_id}' already exists")

    template_source = CANVAS_TEMPLATE.read_text()
    base_definition = CanvasDefinition(canvas_id=canvas_id, name=name, views=[])
    rendered = _render_canvas_source(base_definition, template_source)
    destination.write_text(rendered)
    importlib.invalidate_caches()
    return base_definition


def save_canvas(
    canvas_id: str,
    name: str,
    views: List[Dict[str, Any]],
    new_canvas_id: str | None = None,
) -> CanvasDefinition:
    """Persist updates to a canvas module."""

    existing = load_canvas(canvas_id)
    existing.name = name
    existing.views = [ViewDefinition(view_id=v["id"], code=v["code"]) for v in views]

    target_canvas_id = new_canvas_id.strip() if new_canvas_id else canvas_id
    if not target_canvas_id:
        raise CanvasManagerError("Canvas ID cannot be empty")

    rename_required = target_canvas_id != canvas_id
    if rename_required:
        new_path = CANVAS_DIR / f"{target_canvas_id}.py"
        if new_path.exists():
            raise CanvasManagerError(f"Canvas '{target_canvas_id}' already exists")
    else:
        new_path = _canvas_file(canvas_id)

    existing.canvas_id = target_canvas_id
    old_path = _canvas_file(canvas_id)

    template_source = CANVAS_TEMPLATE.read_text()
    rendered = _render_canvas_source(existing, template_source)
    new_path.write_text(rendered)
    if rename_required:
        old_path.unlink(missing_ok=True)
        sys.modules.pop(f"canvas.{canvas_id}", None)
    importlib.invalidate_caches()
    return existing


def render_canvas(canvas_id: str, params: Dict[str, Any] | None = None) -> "Image.Image":
    """Render a canvas image using its Canvas class."""

    importlib.invalidate_caches()
    module = _load_canvas_module(canvas_id)
    canvas_cls = getattr(module, "Canvas")
    return canvas_cls.render(params=params)


def load_view_configs(canvas_id: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Evaluate the view builder functions and return their configs."""

    module = _load_canvas_module(canvas_id)

    configs: List[Dict[str, Any]] = []
    params_dict: Dict[str, Any] = params or {}

    for view_id, builder in module.CONFIG.get("views", {}).items():
        try:
            configs.append({
                "id": view_id,
                "config": _BaseCanvas._invoke_view_builder(builder, params_dict),
                "error": None,
            })
        except Exception as exc:  # pragma: no cover - runtime feedback for UI
            configs.append({
                "id": view_id,
                "config": None,
                "error": str(exc),
            })
    return configs


def list_available_views() -> List[Dict[str, Any]]:
    """Return the available view classes discovered by :class:`_BaseCanvas`."""

    views = []
    for view_type, cls in _BaseCanvas.find_available_views().items():
        views.append({
            "type": view_type,
            "params": cls.PARAMS,
        })
    return views


def _load_canvas_module(canvas_id: str) -> ModuleType:
    module_name = f"canvas.{canvas_id}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise CanvasNotFoundError(f"Canvas '{canvas_id}' cannot be imported") from exc
    return importlib.reload(module)


def _render_canvas_source(definition: CanvasDefinition, template_source: str) -> str:
    """Render a canvas module using the template as a baseline."""

    class_marker = "class Canvas(_BaseCanvas):"
    preamble, marker, _ = template_source.partition(class_marker)
    if not marker:
        raise CanvasManagerError("Invalid canvas template: missing Canvas class definition")

    preamble = preamble.replace("new_canvas", definition.canvas_id)
    preamble = preamble.rstrip() + "\n\n"
    header = f"{preamble}{marker}\n\n"

    name_literal = json.dumps(definition.name)

    view_sections = []
    for view in definition.views:
        body = view.code.rstrip("\n") + "\n"
        indented_body = textwrap.indent(body, " " * 8)
        section = (
            f"    @staticmethod\n"
            f"    def {view.view_id}(params: dict | None = None) -> dict:\n"
            f"{indented_body}"
        )
        view_sections.append(section)

    if view_sections:
        rendered_views = "\n\n".join(view_sections) + "\n\n"
    else:
        rendered_views = ""

    config_view_lines = []
    for view in definition.views:
        config_view_lines.append(f'        "{view.view_id}": Canvas.{view.view_id},')
    if config_view_lines:
        config_views = "\n" + "\n".join(config_view_lines) + "\n    "
    else:
        config_views = ""

    rendered = (
        f"{header}    ID = {json.dumps(definition.canvas_id)}\n\n"
        "    @classmethod\n"
        "    def render(cls, params: dict | None = None) -> Image.Image:\n"
        "        return cls._render(CONFIG, params=params)\n\n"
        f"{rendered_views}CONFIG = {{\n"
        f"    \"name\": {name_literal},\n"
        f"    \"views\": {{{config_views}}}  # view_id -> view_builder\n"
        "}\n\n"
        "if __name__ == \"__main__\":\n"
        "    img = Canvas.render()\n"
        "    img.show()\n"
    )
    return rendered


def _find_canvas_class(module_ast: ast.Module) -> ast.ClassDef:
    for node in module_ast.body:
        if isinstance(node, ast.ClassDef) and node.name == "Canvas":
            return node
    raise CanvasManagerError("Canvas class not found in module")


def _extract_class_id(canvas_class: ast.ClassDef) -> str:
    for node in canvas_class.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ID":
                    if isinstance(node.value, ast.Constant):
                        return str(node.value.value)
    raise CanvasManagerError("Canvas ID not defined")


def _find_config_assignment(module_ast: ast.Module) -> ast.Assign:
    for node in module_ast.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CONFIG":
                    return node
    raise CanvasManagerError("CONFIG assignment not found")


def _extract_config_metadata(config_assign: ast.Assign) -> tuple[str, List[str]]:
    if not isinstance(config_assign.value, ast.Dict):
        raise CanvasManagerError("CONFIG must be a dictionary")

    name = ""
    view_ids: List[str] = []

    for key_node, value_node in zip(config_assign.value.keys, config_assign.value.values):
        if isinstance(key_node, ast.Constant) and key_node.value == "name":
            if isinstance(value_node, ast.Constant):
                name = str(value_node.value)
        if isinstance(key_node, ast.Constant) and key_node.value == "views":
            if isinstance(value_node, ast.Dict):
                for k in value_node.keys:
                    if isinstance(k, ast.Constant):
                        view_ids.append(str(k.value))
    return name, view_ids


def _extract_view_bodies(canvas_class: ast.ClassDef, lines: List[str]) -> Dict[str, str]:
    view_code: Dict[str, str] = {}
    for node in canvas_class.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not any(isinstance(dec, ast.Name) and dec.id == "staticmethod" for dec in node.decorator_list):
            continue
        if not node.body:
            view_code[node.name] = ""
            continue
        start = node.body[0].lineno
        end = node.body[-1].end_lineno
        body_lines = lines[start - 1:end]
        code = textwrap.dedent("\n".join(body_lines))
        if not code.endswith("\n"):
            code += "\n"
        view_code[node.name] = code
    return view_code
