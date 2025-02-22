import tkinter as tk
from abc import ABC, abstractmethod
from itertools import repeat
from typing import Optional

from PIL.Image import Image
from PIL.ImageDraw import ImageDraw

from ...utils import get_half_line_distance, get_line_width, PressedType, Point


class DistanceInfo:
    def __init__(self):
        self.half_distance = 0.0

    def scale_distance(self, scale: float) -> None:
        self.half_distance = get_half_line_distance(scale)

class BorderInfo:
    def __init__(self, borders: str):
        self.borders = borders

        num_borders = len(borders)
        self.line_widths = list(repeat(0, num_borders))
        self.half_line_widths = list(repeat(0.0, num_borders))

    def scale_widths(self, scale: float) -> None:
        self.line_widths = [get_line_width(border, scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]


class Interactive(ABC):
    """Abstract base class representing an interactive character."""
    def __init__(self):
        self._distance_bias = 0.0
        self._position_bias = Point()
        self._pressed_type = PressedType.SELF

    @abstractmethod
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle a press event at a given point."""

    @abstractmethod
    def move(self, point: Point):
        """Handle a move event to a given point."""

    @abstractmethod
    def redraw(self, image: Image, draw: ImageDraw) -> None:
        """Redraw the component on the given image."""

    @abstractmethod
    def apply_color_changes(self) -> None:
        """Apply color changes to the component."""


class CanvasItem(Interactive):

    @abstractmethod
    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]) -> None:
        """Display the image on the canvas."""

    def paste_image(self, image: Image, position: Point):
        """Paste the image onto the given image for export."""