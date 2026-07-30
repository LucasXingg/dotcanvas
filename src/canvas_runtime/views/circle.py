from PIL import ImageDraw

from ._base_view import _BaseView


class CircleView(_BaseView):
    TYPE = "CircleView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "fill": "Fill color for the circle",
        "outline": "Outline color for the circle",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        radius_w = config["width"]
        radius_h = config["height"]
        x1 = config["location_x"]
        y1 = config["location_y"]
        x2 = x1 + radius_w
        y2 = y1 + radius_h
        draw.ellipse(
            [x1, y1, x2, y2],
            fill=config.get("fill", "#FDE68A"),
            outline=config.get("outline", "#92400E"),
            width=2,
        )
