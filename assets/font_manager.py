"""
FontManager — Reliable cross-platform font loader with Chinese support.
"""
import os
import platform
from typing import Dict, List, Optional, Union, Tuple
from PIL import ImageFont


class FontManager:
    """
    FontManager automatically finds or falls back to a bundled Chinese-capable font.

    - Prefers bundled fonts in ./fonts/ (like LXGWWenKai-Regular.ttf or NotoSansCJK-Regular.ttc)
    - Falls back to known system Chinese fonts (PingFang, SimSun, etc.)
    - Caches loaded fonts for efficiency.
    """

    def __init__(self) -> None:
        self._font_cache: Dict[Tuple, Union[ImageFont.ImageFont, ImageFont.FreeTypeFont]] = {}
        self._system_fonts: Optional[Dict[str, List[str]]] = None
        self._resource_dir = os.path.join(os.path.dirname(__file__), "fonts")

    # ------------------------------
    # Public API
    # ------------------------------

    def get_font(
        self,
        size: int,
        font_name: Optional[str] = None,
        font_weight: Optional[int] = None
    ) -> Union[ImageFont.ImageFont, ImageFont.FreeTypeFont]:
        """Return a PIL ImageFont object that supports Chinese text."""
        cache_key = (size, font_name, font_weight)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        # Try explicit font name (if provided)
        if font_name:
            font = self._load_specific_font(font_name, size)
        else:
            # Try bundled fonts
            font = self._load_bundled_font(size)

        # If still not found, try system fonts
        if font is None:
            font = self._load_system_font(size)

        # Final fallback
        if font is None:
            font = ImageFont.load_default()

        # Cache result
        self._font_cache[cache_key] = font
        return font

    def clear_cache(self):
        """Clear internal font cache."""
        self._font_cache.clear()

    # ------------------------------
    # Internal helpers
    # ------------------------------

    def _load_bundled_font(self, size: int):
        """Try loading a bundled CJK font in ./fonts/."""
        if not os.path.exists(self._resource_dir):
            return None

        bundled_fonts = [
            "NotoSansSC-Bold.ttf",
        ]
        for fname in bundled_fonts:
            fpath = os.path.join(self._resource_dir, fname)
            if os.path.exists(fpath):
                try:
                    return ImageFont.truetype(fpath, size)
                except Exception:
                    continue
        return None

    def _load_system_font(self, size: int):
        """Try to find Chinese-capable system fonts."""
        system = platform.system().lower()
        candidates = []

        if system == "darwin":
            candidates = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/Library/Fonts/NotoSansCJK-Regular.ttc",
            ]
        elif system == "windows":
            candidates = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
            ]
        elif system == "linux":
            candidates = [
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
            ]

        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return None

    def _load_specific_font(self, font_name: str, size: int):
        """Try to load a specific font by name from ./fonts/."""
        for ext in [".ttf", ".ttc", ".otf"]:
            fpath = os.path.join(self._resource_dir, f"{font_name}{ext}")
            if os.path.exists(fpath):
                try:
                    return ImageFont.truetype(fpath, size)
                except Exception:
                    pass
        return None

    def is_default_font(self, font):
        """Check if a given font is PIL's built-in fallback font."""
        return not isinstance(font, ImageFont.FreeTypeFont)
