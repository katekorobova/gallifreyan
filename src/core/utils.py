from __future__ import annotations

import math
from enum import Enum, auto

from ..config import LINE_WIDTHS, MIN_LINE_WIDTH, DEFAULT_HALF_LINE_DISTANCE, MIN_HALF_LINE_DISTANCE


# =============================================
# Enum for Pressed Types
# =============================================
class PressedType(Enum):
    PARENT = auto()
    BORDER = auto()
    INNER = auto()
    CHILD = auto()


# =============================================
# Utility Class: Point
# =============================================
class Point(tuple):
    """A 2D point with basic vector operations."""

    def __new__(cls, x: float = 0.0, y: float = 0.0):
        return super().__new__(cls, (x, y))

    def __add__(self, other: Point) -> Point:
        return Point(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other: Point) -> Point:
        return Point(self[0] - other[0], self[1] - other[1])

    def __mul__(self, other: float) -> Point:
        return Point(self[0] * other, self[1] * other)

    def distance(self) -> float:
        """Calculate the Euclidean distance from the origin."""
        return math.sqrt(self[0] ** 2 + self[1] ** 2)

    def direction(self) -> float:
        """Calculate the angle (radians) of the point relative to the x-axis."""
        return math.atan2(self[1], self[0])

    def shift(self, x: float) -> Point:
        """Shift the point by given x and y offsets."""
        return Point(self[0] + x, self[1] + x)


# =============================================
# Utility Functions
# =============================================
def line_width(typ: str, scale: float) -> int:
    """Calculate the line width based on type and scale, ensuring a minimum value."""
    return max(math.ceil(LINE_WIDTHS[typ] * scale), MIN_LINE_WIDTH[typ])


def half_line_distance(scale: float) -> float:
    """Calculate the scaled half-line distance, ensuring a minimum value."""
    return max(DEFAULT_HALF_LINE_DISTANCE * scale, MIN_HALF_LINE_DISTANCE)
