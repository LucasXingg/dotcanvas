from PIL import Image, ImageDraw

from ._base_view import _BaseView

class _NewViewTemplate(_BaseView):
    TYPE = "_NewViewTemplate" # TODO: change this to your unique view type identifier

    PARAMS = {
        **_BaseView.DEFAULT_PARAMS,
        "custom_param": "Custom Parameter Description", # TODO: Add your custom parameters here
    }

    @staticmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        # TODO: write your rendering logic here
        # Example drawing logic
        draw.rectangle([config["location_x"], config["location_y"], config["location_x"] + config["width"], config["location_y"] + config["height"]], outline="black")
        draw.text((config["location_x"] + 10, config["location_y"] + 10), f"Custom: {config["custom_param"]}", fill="black")