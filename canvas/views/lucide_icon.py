from functools import lru_cache
from io import BytesIO
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from socket import timeout as SocketTimeout

import cairosvg
from PIL import Image, ImageDraw, UnidentifiedImageError

from ._base_view import _BaseView


class LucideIconView(_BaseView):
    TYPE = "LucideIconView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "icon": "Lucide icon name (e.g. 'sun', 'cloud')",
        "color": "Stroke color for the icon",
        "background_fill": "Optional background color behind the icon",
    }

    API_URL_TEMPLATE = "https://lucide.dev/icons/{icon}.svg"

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        icon_name = (config.get("icon") or "sun").strip()
        color = config.get("color", "#111827")
        background = config.get("background_fill")

        svg_template = LucideIconView._fetch_icon_template(icon_name)
        if svg_template is None:
            return

        svg_text = svg_template.replace("stroke=\"currentColor\"", f"stroke=\"{color}\"")
        svg_data = svg_text.encode("utf-8")

        width = max(1, int(config.get("width", 24)))
        height = max(1, int(config.get("height", 24)))

        try:
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=width, output_height=height)
        except Exception:
            return

        try:
            with Image.open(BytesIO(png_data)) as img:
                icon_image = img.convert("RGBA")
        except (OSError, UnidentifiedImageError):
            return

        x = config["location_x"]
        y = config["location_y"]

        if background:
            draw.rectangle((x, y, x + width, y + height), fill=background)

        base_image = getattr(draw, "_image", None) or getattr(draw, "im", None)

        if base_image is not None and hasattr(base_image, "paste"):
            base_image.paste(icon_image, (x, y), icon_image)
        else:
            draw.bitmap((x, y), icon_image.convert("L"))

    @staticmethod
    @lru_cache(maxsize=128)
    def _fetch_icon_template(icon_name: str) -> Optional[str]:
        url = LucideIconView.API_URL_TEMPLATE.format(icon=icon_name)
        request = Request(url, headers={"User-Agent": "dotcanvas/1.0"})
        try:
            with urlopen(request, timeout=5) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, SocketTimeout):
            return None
