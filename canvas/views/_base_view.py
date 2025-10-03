from abc import ABC, abstractmethod

from PIL import ImageDraw

class _BaseView(ABC):
    TYPE = "_BaseView"
    DEFAULT_PARAMS = {
        "location_x": "View X Position",
        "location_y": "View Y Position",
        "width": "View Width",
        "height": "View Height",
    }
    

    @staticmethod
    @abstractmethod
    def draw(draw: ImageDraw.ImageDraw, config: dict) -> None:
        pass

if __name__ == "__main__":
    print(_BaseView.TYPE)