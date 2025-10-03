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

    ID = ""

    @classmethod
    def render(cls) -> Image.Image:
        return cls._render(CONFIG)


CONFIG = {
        "name": "MyCanvas",
        "views": {}  # view_id -> view_builder
    }