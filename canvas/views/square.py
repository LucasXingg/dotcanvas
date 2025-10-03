from PIL import ImageDraw

from ._base_view import _BaseView


class SquareView(_BaseView):
    TYPE = "SquareView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "fill": "Fill color for the square",
        "outline": "Outline color for the square",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        x1 = config["location_x"]
        y1 = config["location_y"]
        x2 = x1 + config["width"]
        y2 = y1 + config["height"]
        draw.rectangle(
            [x1, y1, x2, y2],
            fill=config.get("fill", "#D1E8FF"),
            outline=config.get("outline", "#1E3A8A"),
            width=2,
        )
