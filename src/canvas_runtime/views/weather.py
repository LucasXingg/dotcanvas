from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from PIL import ImageDraw, ImageFont

from ._base_view import _BaseView


class WeatherView(_BaseView):
    TYPE = "WeatherView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "location": "Location label to display",
        "temperature": "Temperature value (e.g. '21°C')",
        "condition": "Short textual description (e.g. 'Sunny')",
        "updated_at": "ISO timestamp for last update",
        "timezone": "IANA timezone for displaying update time",
        "fill": "Primary text color",
        "secondary_fill": "Secondary text color",
        "font_size": "Base font size for main text",
        "background_fill": "Background color for the weather card",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        location = config.get("location", "Weather")
        temperature = config.get("temperature", "--°")
        condition = config.get("condition", "Unknown")
        updated_at = config.get("updated_at")
        tz_name = config.get("timezone")
        fill = config.get("fill", "#111827")
        secondary_fill = config.get("secondary_fill", "#6B7280")
        base_font_size = int(config.get("font_size", 20))

        try:
            title_font = ImageFont.truetype("arial.ttf", base_font_size)
            subtitle_font = ImageFont.truetype("arial.ttf", max(10, base_font_size - 6))
        except OSError:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        x = config["location_x"]
        y = config["location_y"]
        width = config["width"]
        height = config["height"]

        draw.rectangle([x, y, x + width, y + height], fill=config.get("background_fill", "#F3F4F6"))

        padding = 6
        current_y = y + padding

        def text_height(text: str, font: ImageFont.ImageFont) -> int:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[3] - bbox[1]

        draw.text((x + padding, current_y), location, fill=secondary_fill, font=subtitle_font)
        current_y += text_height(location, subtitle_font) + 2

        temp_text = str(temperature)
        draw.text((x + padding, current_y), temp_text, fill=fill, font=title_font)
        current_y += text_height(temp_text, title_font) + 2

        draw.text((x + padding, current_y), condition, fill=secondary_fill, font=subtitle_font)
        current_y += text_height(condition, subtitle_font) + 2

        if updated_at:
            tzinfo = None
            if tz_name:
                try:
                    tzinfo = ZoneInfo(tz_name)
                except ZoneInfoNotFoundError:
                    tzinfo = None
            try:
                timestamp = updated_at.strip()
                if timestamp.endswith("Z"):
                    timestamp = timestamp[:-1] + "+00:00"
                parsed = datetime.fromisoformat(timestamp)
                if tzinfo is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=tzinfo)
                    else:
                        parsed = parsed.astimezone(tzinfo)
                updated_text = parsed.strftime("Updated %H:%M")
                text_h = text_height(updated_text, subtitle_font)
                draw.text((x + padding, y + height - padding - text_h), updated_text, fill=secondary_fill, font=subtitle_font)
            except ValueError:
                pass
