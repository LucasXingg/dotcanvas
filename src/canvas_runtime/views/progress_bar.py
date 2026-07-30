from PIL import ImageDraw

from ._base_view import _BaseView


class ProgressBarView(_BaseView):
    TYPE = "ProgressBarView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "progress": "Progress value between 0 and 100",
        "background_fill": "Background color for the progress track",
        "progress_fill": "Color of the filled progress portion",
        "outline": "Outline color for the progress bar",
        "corner_radius": "Corner radius for a rounded progress bar",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        x1 = config["location_x"]
        y1 = config["location_y"]
        width = config["width"]
        height = config["height"]
        x2 = x1 + width
        y2 = y1 + height

        corner_radius = max(0, int(config.get("corner_radius", 0)))
        if corner_radius:
            corner_radius = min(corner_radius, min(width, height) // 2)

        track_color = config.get("background_fill", "#E5E7EB")
        fill_color = config.get("progress_fill", "#10B981")
        outline_color = config.get("outline", "#374151")

        progress_value = config.get("progress", 0)
        try:
            progress_value = float(progress_value)
        except (TypeError, ValueError):
            progress_value = 0

        # Allow both 0-1 and 0-100
        if progress_value > 1:
            progress_value = progress_value / 100
        progress_value = max(0.0, min(progress_value, 1.0))

        bar_width = int(width * progress_value)

        outline_kwargs = {
            "fill": track_color,
            "outline": outline_color,
            "width": 2,
        }

        if corner_radius > 0:
            draw.rounded_rectangle([x1, y1, x2, y2], radius=corner_radius, **outline_kwargs)
            if bar_width > 0:
                draw.rounded_rectangle(
                    [x1, y1, x1 + bar_width, y2],
                    radius=corner_radius,
                    fill=fill_color,
                    outline=None,
                )
        else:
            draw.rectangle([x1, y1, x2, y2], **outline_kwargs)
            if bar_width > 0:
                draw.rectangle([x1, y1, x1 + bar_width, y2], fill=fill_color, outline=None)
