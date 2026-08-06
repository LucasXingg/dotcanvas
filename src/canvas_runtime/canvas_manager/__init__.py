"""Utilities for creating, reading, and updating canvas modules."""
from __future__ import annotations

import ast
import importlib
import json
import keyword
import re
import textwrap
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

from PIL import Image

from ..base_canvas import _BaseCanvas


# canvas_manager/ -> canvas_runtime/ -> src/ -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
CANVAS_DIR = _PROJECT_ROOT / "canvas"
CANVAS_TEMPLATE = Path(__file__).resolve().parents[1] / "canvas_template.py"

_NON_IDENTIFIER_RE = re.compile(r"[^0-9A-Za-z_]+")
_MULTI_UNDERSCORE_RE = re.compile(r"_+")


def _ensure_identifier(value: str, *, label: str) -> str:
    """Require ``value`` to be a valid, non-keyword Python identifier."""

    trimmed = value.strip()
    if not trimmed:
        raise CanvasManagerError(f"{label} cannot be empty")
    if not trimmed.isidentifier() or keyword.iskeyword(trimmed):
        raise CanvasManagerError(
            f"'{label}' '{trimmed}' must be a valid Python identifier "
            "(e.g., letters, digits, underscores; cannot start with a digit; "
            "cannot be a reserved keyword). Note: Unicode characters are allowed." 
        )
    return trimmed


def slugify_identifier(value: str, *, label: str = "ID") -> str:
    """Convert a human label into a valid Python identifier."""

    cleaned = _MULTI_UNDERSCORE_RE.sub("_", _NON_IDENTIFIER_RE.sub("_", value.strip())).strip("_")
    if not cleaned:
        raise CanvasManagerError(
            f"{label} must contain letters or digits so a valid Python identifier can be derived"
        )
    if cleaned[0].isdigit():
        cleaned = f"canvas_{cleaned}"
    if keyword.iskeyword(cleaned):
        cleaned = f"{cleaned}_canvas"
    return _ensure_identifier(cleaned, label=label)


def _ensure_canvas_package() -> None:
    """Ensure ``canvas/`` exists and is importable as a package.

    Docker volume mounts may overlay an empty host directory that lacks
    ``__init__.py``; create a minimal one so ``import canvas.<id>`` works.
    """

    CANVAS_DIR.mkdir(parents=True, exist_ok=True)
    init_path = CANVAS_DIR / "__init__.py"
    if not init_path.exists():
        init_path.write_text(
            '"""User canvas modules. Framework code lives in src.canvas_runtime."""\n'
        )


_ensure_canvas_package()



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
    try:
        module_ast = ast.parse(source)
    except SyntaxError as exc:
        raise CanvasManagerError(
            f"Canvas '{canvas_id}' contains invalid Python syntax "
            f"(line {exc.lineno}): {exc.msg}"
        ) from exc

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
    """Create a new canvas module from the template.

    ``canvas_id`` is slugified into a valid Python identifier so human-readable
    names (e.g. ``"Agent Usage"``) still produce an importable module.
    """

    canvas_id = slugify_identifier(canvas_id, label="Canvas ID")
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

    try:
        existing = load_canvas(canvas_id)
    except CanvasManagerError as exc:
        # Recover canvases previously written with invalid syntax (e.g. spaced view IDs).
        if not isinstance(exc.__cause__, SyntaxError):
            raise
        path = CANVAS_DIR / f"{canvas_id}.py"
        if not path.exists():
            raise
        existing = CanvasDefinition(canvas_id=canvas_id, name=name, views=[])
    existing.name = name
    validated_views: List[ViewDefinition] = []
    for view in views:
        view_id = _ensure_identifier(str(view.get("id", "")), label="View ID")
        validated_views.append(ViewDefinition(view_id=view_id, code=view["code"]))
    existing.views = validated_views

    target_raw = new_canvas_id.strip() if new_canvas_id else canvas_id
    if not target_raw:
        raise CanvasManagerError("Canvas ID cannot be empty")
    if new_canvas_id is not None:
        # Explicit renames must already be valid identifiers.
        target_canvas_id = _ensure_identifier(target_raw, label="Canvas ID")
    else:
        # Migrate legacy canvas IDs that are not valid Python identifiers.
        try:
            target_canvas_id = _ensure_identifier(target_raw, label="Canvas ID")
        except CanvasManagerError:
            target_canvas_id = slugify_identifier(target_raw, label="Canvas ID")

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
        return importlib.reload(module)
    except ModuleNotFoundError as exc:
        raise CanvasNotFoundError(f"Canvas '{canvas_id}' cannot be imported") from exc
    except SyntaxError as exc:
        raise CanvasManagerError(
            f"Canvas '{canvas_id}' contains invalid Python syntax "
            f"(line {exc.lineno}): {exc.msg}"
        ) from exc


def _render_canvas_source(definition: CanvasDefinition, template_source: str) -> str:
    """Render a canvas module using the template as a baseline."""

    class_marker = "class Canvas(_BaseCanvas):"
    preamble, marker, _ = template_source.partition(class_marker)
    if not marker:
        raise CanvasManagerError("Invalid canvas template: missing Canvas class definition")

    canvas_id = _ensure_identifier(definition.canvas_id, label="Canvas ID")
    preamble = preamble.replace("new_canvas", canvas_id)
    preamble = preamble.rstrip() + "\n\n"
    header = f"{preamble}{marker}\n\n"

    name_literal = json.dumps(definition.name)

    view_sections = []
    for view in definition.views:
        view_id = _ensure_identifier(view.view_id, label="View ID")
        body = view.code.rstrip("\n") + "\n"
        indented_body = textwrap.indent(body, " " * 8)
        section = (
            f"    @staticmethod\n"
            f"    def {view_id}(params: dict | None = None) -> dict:\n"
            f"{indented_body}"
        )
        view_sections.append(section)

    if view_sections:
        rendered_views = "\n\n".join(view_sections) + "\n\n"
    else:
        rendered_views = ""

    config_view_lines = []
    for view in definition.views:
        view_id = _ensure_identifier(view.view_id, label="View ID")
        config_view_lines.append(f'        "{view_id}": Canvas.{view_id},')
    if config_view_lines:
        config_views = "\n" + "\n".join(config_view_lines) + "\n    "
    else:
        config_views = ""

    rendered = (
        f"{header}    ID = {json.dumps(canvas_id)}\n\n"
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
    try:
        ast.parse(rendered)
    except SyntaxError as exc:
        raise CanvasManagerError(
            f"Generated canvas source is invalid Python (line {exc.lineno}): {exc.msg}. "
            "Check that view builder bodies are valid Python."
        ) from exc
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
