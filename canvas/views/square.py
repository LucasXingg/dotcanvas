from PIL import ImageDraw

from ._base_view import _BaseView


class SquareView(_BaseView):
    TYPE = "SquareView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "fill": "Fill color for the square",
        "outline": "Outline color for the square",
        "corner_radius": "Optional corner radius for rounded corners",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        x1 = config["location_x"]
        y1 = config["location_y"]
        x2 = x1 + config["width"]
        y2 = y1 + config["height"]
        corner_radius = int(config.get("corner_radius", 0))
        draw_kwargs = {
            "fill": config.get("fill", "#D1E8FF"),
            "outline": config.get("outline", "#1E3A8A"),
            "width": 2,
        }

        if corner_radius > 0:
            draw.rounded_rectangle(
                [x1, y1, x2, y2],
                radius=corner_radius,
                **draw_kwargs,
            )
        else:
            draw.rectangle(
                [x1, y1, x2, y2],
                **draw_kwargs,
            )
