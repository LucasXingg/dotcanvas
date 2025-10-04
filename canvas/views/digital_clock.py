from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from PIL import ImageDraw, ImageFont

from ._base_view import _BaseView


class DigitalClockView(_BaseView):
    TYPE = "DigitalClockView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "format": "strftime format string",
        "timezone": "IANA timezone (e.g. 'UTC' or 'Europe/London')",
        "fill": "Text color",
        "background_fill": "Optional background color behind the clock",
        "font_size": "Font size in points",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        fmt = config.get("format", "%H:%M:%S")
        tz_name = config.get("timezone")
        fill = config.get("fill", "#111827")
        background = config.get("background_fill")
        font_size = int(config.get("font_size", 24))

        tzinfo = None
        if tz_name:
            try:
                tzinfo = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                tzinfo = None

        now = datetime.now(tz=tzinfo)
        time_text = now.strftime(fmt)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        x = config["location_x"]
        y = config["location_y"]
        width = config["width"]
        height = config["height"]

        if background:
            draw.rectangle([x, y, x + width, y + height], fill=background)

        bbox = draw.textbbox((0, 0), time_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2

        draw.text((text_x, text_y), time_text, fill=fill, font=font)
