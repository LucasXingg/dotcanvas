from PIL import ImageDraw, ImageFont

from ._base_view import _BaseView


class TextView(_BaseView):
    TYPE = "TextView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "text": "Text to display",
        "fill": "Text color",
        "font_size": "Font size in points",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        text = config.get("text", "Hello")
        color = config.get("fill", "#111827")
        font_size = int(config.get("font_size", 18))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        x = config["location_x"]
        y = config["location_y"]
        draw.text((x, y), text, fill=color, font=font)
