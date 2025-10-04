import sys
from pathlib import Path

try:
    # preferred when run as a package: python -m canvas.countdown_canvas
    from ._base_canvas import _BaseCanvas
except Exception:
    # fallback when running the file directly: python canvas/countdown_canvas.py
    # add project root to sys.path and import absolute package
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from canvas._base_canvas import _BaseCanvas

from PIL import Image, ImageDraw, ImageFont

class Canvas(_BaseCanvas):

    ID = "countdown_canvas"

    @classmethod
    def render(cls) -> Image.Image:
        return cls._render(CONFIG)

    @staticmethod
    def hero_square() -> dict:
        return {
            "type": "SquareView",
            "location_x": 30,
            "location_y": 35,
            "width": 165,
            "height": 35,
            "fill": "#D1E8FF",
            "outline": "#1E3A8A",
            "corner_radius": 6,
        }


    @staticmethod
    def count_down_text() -> dict:
        from datetime import datetime

        target_date_str = "2025-12-31"

        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        delta = target_date - today
        day_left_str = str(delta.days) if delta.days >= 0 else "0"

        return {
            "type": "TextView",
            "location_x": 41,
            "location_y": 43,
            "width": 120,
            "height": 40,
            "text": f"距离2025年结束还有 {day_left_str} 天",
            "fill": "#000000",
            "font_size": 12,
        }


    @staticmethod
    def countdown_bar() -> dict:
        from datetime import datetime

        target_date_str = "2025-12-31"

        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        delta = target_date - today
        progress = ( (365 - delta.days) / 365) * 100

        return {
            "type": "ProgressBarView",
            "location_x": 16,
            "location_y": 110,
            "width": 264,
            "height": 24,
            "progress": progress,
            "background_fill": "#EDEDED",
            "progress_fill": "#010101",
            "outline": "#000000",
            "corner_radius": 6,
        }


    @staticmethod
    def icon_view() -> dict:
        return {
            "type": "LucideIconView",
            "location_x": 210,
            "location_y": 20,
            "width": 64,
            "height": 64,
            "icon": "calendar-check",
        }


CONFIG = {
    "name": "countdown_canvas",
    "views": {
        "hero_square": Canvas.hero_square,
        "count_down_text": Canvas.count_down_text,
        "countdown_bar": Canvas.countdown_bar,
        "icon_view": Canvas.icon_view,
    }  # view_id -> view_builder
}

if __name__ == "__main__":
    img = Canvas.render()
    img.show()
