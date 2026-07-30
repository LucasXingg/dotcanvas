from functools import lru_cache
from io import BytesIO
from typing import Optional
from urllib.error import HTTPError, URLError
import requests
from socket import timeout as SocketTimeout
import logging

import cairosvg
from PIL import Image, ImageDraw, UnidentifiedImageError

from ._base_view import _BaseView

logger = logging.getLogger("dot.views.lucide_icon")

class LucideIconView(_BaseView):
    TYPE = "LucideIconView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "icon": "Lucide icon name (e.g. 'sun', 'cloud')",
    }

    API_URL_TEMPLATE = "https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{icon}.svg"

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        icon_name = (config.get("icon") or "sun").strip()

        svg_byte = LucideIconView._fetch_icon_template(icon_name)

        if svg_byte is None:
            return

        width = max(1, int(config.get("width", 24)))
        height = max(1, int(config.get("height", 24)))

        try:
            png_data = cairosvg.svg2png(bytestring=svg_byte, output_width=width, output_height=height)
        except Exception as e:
            logger.error(f"Error converting SVG to PNG: {e}")
            return

        try:
            with Image.open(BytesIO(png_data)) as img:
                icon_image = img.convert("RGBA")
        except (OSError, UnidentifiedImageError) as e:
            logger.error(f"Error loading icon image: {e}")
            return

        x = config["location_x"]
        y = config["location_y"]

        base_image = getattr(draw, "_image", None) or getattr(draw, "im", None)

        if base_image is not None and hasattr(base_image, "paste"):
            base_image.paste(icon_image, (x, y), icon_image)
        else:
            draw.bitmap((x, y), icon_image.convert("L"))

    @staticmethod
    @lru_cache(maxsize=128)
    def _fetch_icon_template(icon_name: str) -> Optional[bytes]:
        url = LucideIconView.API_URL_TEMPLATE.format(icon=icon_name)
        
        try:
            responses = requests.get(url, timeout=5)
            return responses.content
        except (HTTPError, URLError, TimeoutError, SocketTimeout) as e:
            logger.error(f"Error fetching icon '{icon_name}': {e}")
            return None
