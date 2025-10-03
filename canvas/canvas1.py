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

    ID = "canvas1"

    @classmethod
    def render(cls) -> Image.Image:
        return cls._render(CONFIG)

    @staticmethod
    def hero_square() -> dict:
        return {
            "type": "SquareView",
            "location_x": 16,
            "location_y": 16,
            "width": 120,
            "height": 120,
            "fill": "#BFDBFE",
            "outline": "#1D4ED8",
        }

    @staticmethod
    def spotlight_circle() -> dict:
        return {
            "type": "CircleView",
            "location_x": 156,
            "location_y": 24,
            "width": 96,
            "height": 96,
            "fill": "#FDE68A",
            "outline": "#92400E",
        }

    @staticmethod
    def headline_text() -> dict:
        return {
            "type": "TextView",
            "location_x": 24,
            "location_y": 40,
            "width": 200,
            "height": 40,
            "text": "Canvas 1",
            "fill": "#111827",
            "font_size": 24,
        }


CONFIG = {
    "name": "Canvas 1",
    "views": {
        "hero_square": Canvas.hero_square,
        "spotlight_circle": Canvas.spotlight_circle,
        "headline_text": Canvas.headline_text,
    }  # view_id -> view_builder
}

if __name__ == "__main__":
    img = Canvas.render()
    img.show()
