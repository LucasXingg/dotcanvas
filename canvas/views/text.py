from PIL import ImageDraw, ImageFont

from ._base_view import _BaseView
from assets.font_manager import FontManager


class TextView(_BaseView):
    TYPE = "TextView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "text": "Text to display",
        "fill": "Text color",
        "font_size": "Font size in points",
        "font_name": "Font name (optional)",
    }


    font_manager = FontManager()

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        text = config.get("text", "Hello")
        color = config.get("fill", "#111827")
        font_size = int(config.get("font_size", 18))
        font_name = config.get("font_name")

        # Load font (auto-detects bundled CJK fonts or system fallback)
        font = TextView.font_manager.get_font(font_size, font_name)

        # Coordinates
        x = config.get("location_x", 0)
        y = config.get("location_y", 0)

        # Draw text
        draw.text((x, y), text, fill=color, font=font)
