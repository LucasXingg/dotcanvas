import sys
from pathlib import Path

try:
    # preferred when run as a package: python -m canvas.new_canvas
    from ._base_canvas import _BaseCanvas
except Exception:
    # fallback when running the file directly: python canvas/new_canvas.py
    # add project root to sys.path and import absolute package
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from canvas._base_canvas import _BaseCanvas

from PIL import Image, ImageDraw, ImageFont


class Canvas(_BaseCanvas):

    ID = "new_canvas"

    @classmethod
    def render(cls) -> Image.Image:
        return cls._render(CONFIG)

    # Add view builder functions here. For example:
    # @staticmethod
    # def example_view() -> dict:
    #     return {
    #         "type": "SquareView",
    #         "location_x": 16,
    #         "location_y": 16,
    #         "width": 100,
    #         "height": 100,
    #     }


CONFIG = {
    "name": "New Canvas",
    "views": {
        # "example_view": Canvas.example_view,
    }  # view_id -> view_builder
}

if __name__ == "__main__":
    img = Canvas.render()
    img.show()
