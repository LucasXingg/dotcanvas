from src.canvas_runtime.base_canvas import _BaseCanvas
from src.canvas_runtime.package_manager import install_package

from PIL import Image, ImageDraw, ImageFont


class Canvas(_BaseCanvas):

    ID = "new_canvas"

    @classmethod
    def render(cls, params: dict | None = None) -> Image.Image:
        return cls._render(CONFIG, params=params)

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
