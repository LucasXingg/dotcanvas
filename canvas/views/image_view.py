import base64
from io import BytesIO
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from socket import timeout as SocketTimeout

from PIL import Image, ImageDraw, UnidentifiedImageError

from ._base_view import _BaseView


class ImageView(_BaseView):
    TYPE = "ImageView"

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "source_type": "Source type: 'url' or 'base64'",
        "url": "Image URL when using source_type 'url'",
        "base64": "Base64 encoded image data when using source_type 'base64'",
        "maintain_aspect_ratio": "Whether to keep the image's aspect ratio",
        "background_fill": "Optional background fill when transparency exists",
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        image = ImageView._load_image(config)
        if image is None:
            return

        width = max(1, int(config.get("width", image.width)))
        height = max(1, int(config.get("height", image.height)))
        maintain_aspect_ratio = bool(config.get("maintain_aspect_ratio", True))

        try:
            resample_filter = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
        except AttributeError:  # Pillow < 9.1
            resample_filter = Image.LANCZOS

        if maintain_aspect_ratio:
            image = image.copy()
            image.thumbnail((width, height), resample_filter)
            offset_x = (width - image.width) // 2
            offset_y = (height - image.height) // 2
        else:
            image = image.resize((width, height), resample_filter)
            offset_x = 0
            offset_y = 0

        background = config.get("background_fill")
        target_box = (config["location_x"], config["location_y"], config["location_x"] + width, config["location_y"] + height)

        if background:
            draw.rectangle(target_box, fill=background)
            if image.mode in {"RGBA", "LA"}:
                bg = Image.new("RGBA", image.size, background)
                bg.alpha_composite(image)
                image = bg.convert("RGBA")

        x = config["location_x"]
        y = config["location_y"]
        paste_x = x + offset_x
        paste_y = y + offset_y

        base_image = getattr(draw, "_image", None) or getattr(draw, "im", None)

        if base_image is not None and hasattr(base_image, "paste"):
            mask = image if image.mode in {"RGBA", "LA"} else None
            base_image.paste(image, (paste_x, paste_y), mask)
        else:
            if image.mode not in {"1", "L"}:
                image = image.convert("L")
            draw.bitmap((paste_x, paste_y), image)

    @staticmethod
    def _load_image(config: dict) -> Optional[Image.Image]:
        source_type = (config.get("source_type") or "url").lower()

        try:
            if source_type == "base64":
                base64_data = config.get("base64")
                if not base64_data:
                    return None
                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]
                data = base64.b64decode(base64_data)
                with Image.open(BytesIO(data)) as img:
                    return img.convert("RGBA")

            # Default to URL
            url = config.get("url")
            if not url:
                return None
            request = Request(url, headers={"User-Agent": "dotcanvas/1.0"})
            with urlopen(request, timeout=5) as response:
                data = response.read()
            with Image.open(BytesIO(data)) as img:
                return img.convert("RGBA")
        except (HTTPError, URLError, TimeoutError, SocketTimeout, ValueError, OSError, UnidentifiedImageError):
            return None
