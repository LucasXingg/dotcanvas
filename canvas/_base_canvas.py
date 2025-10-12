import logging
import importlib
import inspect
import pkgutil
from typing import Any, Callable


from PIL import Image, ImageDraw, ImageFont

from . import views

logger = logging.getLogger("dot.canvas")

class _BaseCanvas():

    ID = "BaseCanvas"

    WIDTH = 296
    HEIGHT = 152

    @classmethod
    def _render(cls, config: dict, params: dict[str, Any] | None = None) -> Image.Image:
        available_views = cls.find_available_views()
        canvas_img = Image.new("RGB", (cls.WIDTH, cls.HEIGHT), "white")
        draw = ImageDraw.Draw(canvas_img)
        params_dict: dict[str, Any] = params or {}

        for view_builder in config["views"].values():
            try:
                view_config = cls._invoke_view_builder(view_builder, params_dict)
                view_cls = available_views.get(view_config["type"])
                if view_cls:
                    view_cls.draw(draw, view_config)
            except Exception as e:
                view_type = view_config.get("type") if isinstance(view_config, dict) else "unknown"
                logger.error(f"Error rendering view {view_type}: {e}")
        return canvas_img

    @staticmethod
    def view_builder_validator(view_builder: Callable) -> bool:
        required_keys = ["location_x", "location_y", "width", "height"]
        try:
            view_config = _BaseCanvas._invoke_view_builder(view_builder, {})
            # Use find_available_views() instead of a non-existent attribute
            available = _BaseCanvas.find_available_views()
            if view_config.get("type") not in available.keys():
                raise ValueError(f"Unknown view type: {view_config.get('type')}")
            for key in required_keys:
                if key not in view_config:
                    raise ValueError(f"Missing required key: {key}")
        except Exception as e:
            logger.error(f"View builder validation error: {e}")
            return False
        return True

    @staticmethod
    def find_available_views(package=views) -> dict[str, type]:
        """
        Discover all classes with a `.type` attribute inside a package's submodules.

        Args:
            package (module): The package (already imported) to search in.

        Returns:
            dict[str, type]: Mapping of `obj.type` -> class
        """
        view_classes = {}

        # Iterate over all submodules in the package
        for finder, module_name, ispkg in pkgutil.iter_modules(package.__path__):
            full_name = f"{package.__name__}.{module_name}"
            module = importlib.import_module(full_name)

            # Inspect classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Ensure class is actually defined in this module (not imported)
                if obj.__module__ == module.__name__:
                    if hasattr(obj, "TYPE"):
                        view_classes[obj.TYPE] = obj

        return view_classes

    @staticmethod
    def _invoke_view_builder(view_builder: Callable, params: dict[str, Any]) -> dict:
        """Call a view builder, supplying params when supported."""
        try:
            signature = inspect.signature(view_builder)
        except (TypeError, ValueError):
            signature = None

        if signature:
            parameters = signature.parameters
            if "params" in parameters:
                return view_builder(params=params)

            ordered_params = list(parameters.values())
            if ordered_params:
                first_param = ordered_params[0]

                if first_param.kind == inspect.Parameter.KEYWORD_ONLY:
                    return view_builder(**{first_param.name: params})

                if first_param.kind == inspect.Parameter.VAR_KEYWORD:
                    return view_builder(params=params)

                # Covers positional-only, positional-or-keyword, and var-positional
                return view_builder(params)

        return view_builder(params={})

if __name__ == "__main__":
    print("Available views:", _BaseCanvas.find_available_views())
