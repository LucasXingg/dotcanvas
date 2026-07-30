import math
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from PIL import ImageDraw

from ._base_view import _BaseView


class AnalogClockView(_BaseView):
    TYPE = "AnalogClockView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "timezone": "IANA timezone (e.g. 'UTC' or 'Europe/Berlin')",
        "face_fill": "Clock face fill color",
        "outline": "Clock outline color",
        "hand_color": "Color for hour and minute hands",
        "second_hand_color": "Color for the second hand",
        "tick_color": "Color for hour ticks",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        tz_name = config.get("timezone")
        face_fill = config.get("face_fill", "#F9FAFB")
        outline_color = config.get("outline", "#111827")
        hand_color = config.get("hand_color", "#111827")
        second_hand_color = config.get("second_hand_color", "#EF4444")
        tick_color = config.get("tick_color", "#4B5563")

        tzinfo = None
        if tz_name:
            try:
                tzinfo = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                tzinfo = None

        now = datetime.now(tz=tzinfo)

        x = config["location_x"]
        y = config["location_y"]
        width = config["width"]
        height = config["height"]

        radius = min(width, height) // 2
        center_x = x + width // 2
        center_y = y + height // 2

        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            fill=face_fill,
            outline=outline_color,
            width=2,
        )

        # Draw hour ticks
        for hour in range(12):
            angle = math.radians(hour * 30)
            outer_x = center_x + int(math.sin(angle) * (radius - 4))
            outer_y = center_y - int(math.cos(angle) * (radius - 4))
            inner_x = center_x + int(math.sin(angle) * (radius - 12))
            inner_y = center_y - int(math.cos(angle) * (radius - 12))
            draw.line([(inner_x, inner_y), (outer_x, outer_y)], fill=tick_color, width=2)

        hour = now.hour % 12
        minute = now.minute
        second = now.second

        hour_angle = math.radians((hour + minute / 60) * 30)
        minute_angle = math.radians((minute + second / 60) * 6)
        second_angle = math.radians(second * 6)

        def hand_endpoint(angle: float, length: float) -> tuple[int, int]:
            return (
                center_x + int(math.sin(angle) * length),
                center_y - int(math.cos(angle) * length),
            )

        hour_end = hand_endpoint(hour_angle, radius * 0.5)
        minute_end = hand_endpoint(minute_angle, radius * 0.75)
        second_end = hand_endpoint(second_angle, radius * 0.85)

        draw.line([(center_x, center_y), hour_end], fill=hand_color, width=4)
        draw.line([(center_x, center_y), minute_end], fill=hand_color, width=3)
        draw.line([(center_x, center_y), second_end], fill=second_hand_color, width=2)

        draw.ellipse(
            [center_x - 4, center_y - 4, center_x + 4, center_y + 4],
            fill=hand_color,
            outline=None,
        )
