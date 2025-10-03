import sys
from pathlib import Path

try:
    # preferred when run as a package: python -m canvas.canvas1
    from ._base_canvas import _BaseCanvas
except Exception:
    # fallback when running the file directly: python canvas/canvas1.py
    # add project root to sys.path and import absolute package
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from canvas._base_canvas import _BaseCanvas

from PIL import Image, ImageDraw, ImageFont




class Canvas(_BaseCanvas):

    ID = "Canvas1"

    @classmethod
    def render(cls) -> Image.Image:
        return cls._render(CONFIG)

    @staticmethod
    def v1() -> None:
        config = {
            "type": "_NewViewTemplate",
            "location_x": 0,
            "location_y": 0,
            "width": 296,
            "height": 152,
            "custom_param": "Example Parameter Value"
        }
        return config


CONFIG = {
        "name": "Canvas1",
        "views": {
            "v1": Canvas.v1
        }  # view_id -> view_builder
    }

if __name__ == "__main__":
    img = Canvas.render()
    img.show()