from __future__ import annotations

import copy
import math
from enum import Enum, auto

from PIL import Image, ImageDraw

from ..config import (LINE_WIDTHS, MIN_LINE_WIDTH, DEFAULT_HALF_LINE_DISTANCE, MIN_HALF_LINE_DISTANCE,
                      CANVAS_BG, WORD_BG, SYLLABLE_BG, WORD_COLOR, SYLLABLE_COLOR, VOWEL_COLOR, DOT_COLOR, MIN_RADIUS)


# =============================================
# Enum for Pressed Types
# =============================================
class PressedType(Enum):
    """Enumeration for different types of pressed elements."""
    PARENT = auto()
    BORDER = auto()
    INNER = auto()
    CHILD = auto()


# =============================================
# Utility Class: Point
# =============================================
class Point:
    """A 2D point with basic vector operations."""

    def __init__(self, x: float = 0.0, y: float = 0.0):
        """Create a new Point instance."""
        self.x = x
        self.y = y

    def __add__(self, other: Point) -> Point:
        """Add two points component-wise."""
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        """Subtract two points component-wise."""
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float) -> Point:
        """Scale the point by a scalar value."""
        return Point(self.x * other, self.y * other)

    def distance(self) -> float:
        """Calculate the Euclidean distance from the origin."""
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def direction(self) -> float:
        """Calculate the angle (radians) of the point relative to the x-axis."""
        return math.atan2(self.y, self.x)

    def shift(self, x: float) -> Point:
        """Shift the point by given x and y offsets."""
        return Point(self.x + x, self.y + x)

    def tuple(self) -> tuple[int, int]:
        """Convert the point to a tuple."""
        return round(self.x), round(self.y)


# =============================================
# Color Scheme
# =============================================
class ColorSchemeComponent(Enum):
    """Enumeration of different components that can have customizable colors."""
    CANVAS_BG = auto()
    WORD_BG = auto()
    SYLLABLE_BG = auto()

    WORD_COLOR = auto()
    SYLLABLE_COLOR = auto()
    VOWEL_COLOR = auto()
    DOT_COLOR = auto()


ColorScheme = dict[ColorSchemeComponent, str]

_default_color_scheme: ColorScheme = {
        ColorSchemeComponent.CANVAS_BG: CANVAS_BG,
        ColorSchemeComponent.WORD_BG: WORD_BG,
        ColorSchemeComponent.SYLLABLE_BG: SYLLABLE_BG,
        ColorSchemeComponent.WORD_COLOR: WORD_COLOR,
        ColorSchemeComponent.SYLLABLE_COLOR: SYLLABLE_COLOR,
        ColorSchemeComponent.VOWEL_COLOR: VOWEL_COLOR,
        ColorSchemeComponent.DOT_COLOR: DOT_COLOR
    }


def get_default_color_scheme() -> ColorScheme:
    """Returns a copy of the default color scheme."""
    return copy.copy(_default_color_scheme)

def reset_color_scheme(color_scheme: ColorScheme):
    """Resets the given color scheme to the default values."""
    for key, value in _default_color_scheme.items():
        color_scheme[key] = value

# =============================================
# Utility Functions
# =============================================
def get_line_width(typ: str, scale: float) -> int:
    """Calculate the line width based on type and scale, ensuring a minimum value."""
    return max(math.ceil(LINE_WIDTHS[typ] * scale), MIN_LINE_WIDTH[typ])

def get_half_line_distance(scale: float) -> float:
    """Calculate the scaled half-line distance, ensuring a minimum value."""
    return max(DEFAULT_HALF_LINE_DISTANCE * scale, MIN_HALF_LINE_DISTANCE)

def create_empty_image(image_center: Point, mode: str = 'RGBA') -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create an empty image with the specified mode."""
    image = Image.new(mode, (image_center * 2).tuple())
    return image, ImageDraw.Draw(image)

def ensure_min_radius(radius: float):
    """Calculate a  radius with constraints."""
    return max(radius, MIN_RADIUS)
