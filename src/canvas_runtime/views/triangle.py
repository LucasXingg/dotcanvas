from PIL import ImageDraw

from ._base_view import _BaseView


class TriangleView(_BaseView):
    TYPE = "TriangleView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "direction": "Triangle direction: up, down, left, or right",
        "fill": "Fill color for the triangle",
        "outline": "Outline color for the triangle",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        x = config["location_x"]
        y = config["location_y"]
        width = config["width"]
        height = config["height"]
        direction = (config.get("direction") or "up").lower()

        if direction == "down":
            points = [(x, y), (x + width // 2, y + height), (x + width, y)]
        elif direction == "left":
            points = [(x + width, y), (x + width, y + height), (x, y + height // 2)]
        elif direction == "right":
            points = [(x, y), (x + width, y + height // 2), (x, y + height)]
        else:  # default to up
            points = [(x, y + height), (x + width // 2, y), (x + width, y + height)]

        draw.polygon(
            points,
            fill=config.get("fill", "#F59E0B"),
            outline=config.get("outline", "#92400E"),
        )
