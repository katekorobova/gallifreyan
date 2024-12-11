from __future__ import annotations

import math
from enum import Enum, auto
from typing import List

# ==========================
# UI Constants
# ==========================
BUTTON_WIDTH = 3
BUTTON_HEIGHT = 1
BUTTON_IMAGE_SIZE = 36

PADX = 10
PADY = 10

FONT = ('Segoe UI', 14)
WINDOW_BG = 'midnightblue'
BUTTON_BG = '#11114D'
CANVAS_BG = 'white'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# ==========================
# Color Constants (RGBA)
# ==========================
SYLLABLE_BG = (150, 150, 255, 200)
WORD_BG = (200, 220, 255, 255)
SYLLABLE_COLOR = (34, 42, 131, 255)
WORD_COLOR = (0, 50, 150, 255)

# ==========================
# Scaling and Geometry Constants
# ==========================
WORD_INITIAL_POSITION = (300, 300)

WORD_INITIAL_SCALE_MIN = 0.8
WORD_SCALE_MIN = 0.3

SYLLABLE_INITIAL_SCALE_MIN = 0.8
SYLLABLE_INITIAL_SCALE_MAX = 0.8
SYLLABLE_SCALE_MIN = 0.3
SYLLABLE_SCALE_MAX = 0.85

INNER_INITIAL_SCALE_MIN = 0.5
INNER_INITIAL_SCALE_MAX = 0.5
INNER_SCALE_MIN = 0.2
INNER_SCALE_MAX = 0.7

# ==========================
# Radius and Distance Constants
# ==========================
OUTER_CIRCLE_RADIUS = 200
HALF_LINE_DISTANCE = 8
MIN_HALF_LINE_DISTANCE = 2
MIN_RADIUS = 1

WORD_IMAGE_RADIUS = OUTER_CIRCLE_RADIUS + 4 * HALF_LINE_DISTANCE
SYLLABLE_IMAGE_RADIUS = math.ceil(OUTER_CIRCLE_RADIUS * SYLLABLE_SCALE_MAX) + 4 * HALF_LINE_DISTANCE

DOT_RADIUS = OUTER_CIRCLE_RADIUS / 20
MIN_DOT_RADIUS = 0

# ==========================
# Line Width Constants
# ==========================
LINE_WIDTHS = {'1': 4, '2': 10}
MIN_LINE_WIDTH = {'1': 1, '2': 2}

# ==========================
# Miscellaneous Constants
# ==========================
ALEPH = 'א'  # Hebrew Aleph letter


# ==========================
# Enum for Pressed Types
# ==========================
class PressedType(Enum):
    PARENT = auto()
    BORDER = auto()
    INNER = auto()
    CHILD = auto()


# ==========================
# Utility Class: Point
# ==========================
class Point(tuple):
    """A 2D point with basic vector operations."""

    def __new__(cls, x: float = 0.0, y: float = 0.0):
        return super().__new__(cls, (x, y))

    def __add__(self, other: Point) -> Point:
        return Point(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other: Point) -> Point:
        return Point(self[0] - other[0], self[1] - other[1])

    def distance(self) -> float:
        """Calculate the Euclidean distance from the origin."""
        return math.sqrt(self[0] ** 2 + self[1] ** 2)

    def direction(self) -> float:
        """Calculate the angle (radians) of the point relative to the x-axis."""
        return math.atan2(self[1], self[0])

    def shift(self, x: float, y: float) -> Point:
        """Shift the point by given x and y offsets."""
        return Point(self[0] + x, self[1] + y)


# ==========================
# Utility Functions
# ==========================
def unique(items: List) -> List:
    """Return a list of unique items while preserving order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item))]


def line_width(typ: str, scale: float) -> int:
    """Calculate the line width based on type and scale, ensuring a minimum value."""
    return max(math.ceil(LINE_WIDTHS[typ] * scale), MIN_LINE_WIDTH[typ])


def half_line_distance(scale: float) -> float:
    """Calculate the scaled half-line distance, ensuring a minimum value."""
    return max(HALF_LINE_DISTANCE * scale, MIN_HALF_LINE_DISTANCE)
