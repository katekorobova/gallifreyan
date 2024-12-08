import math
from typing import List
from enum import Enum, auto

BUTTON_WIDTH = 3
BUTTON_HEIGHT = 1
WINDOW_BG = 'midnightblue'
CANVAS_BG = 'white'
SYLLABLE_BG = (150, 150, 255, 200)
WORD_BG = (200, 220, 255, 255)
SYLLABLE_COLOR = (34, 42, 131, 255)
WORD_COLOR = (0, 50, 150, 255)
FONT = ('Segoe UI', 14)
PADX = 10
PADY = 10
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

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

BUTTON_IMAGE_SIZE = 36


OUTER_CIRCLE_RADIUS = 200
HALF_LINE_DISTANCE = 8
MIN_HALF_LINE_DISTANCE = 2
MIN_RADIUS = 0

LINE_WIDTHS = {'1': 4, '2': 10}
MIN_LINE_WIDTH = {'1': 1, '2': 2}

WORD_IMAGE_RADIUS = OUTER_CIRCLE_RADIUS + 4 * HALF_LINE_DISTANCE
SYLLABLE_IMAGE_RADIUS = math.ceil(OUTER_CIRCLE_RADIUS * SYLLABLE_SCALE_MAX) + 4 * HALF_LINE_DISTANCE

DOT_RADIUS = OUTER_CIRCLE_RADIUS / 20
MIN_DOT_RADIUS = 0

ALEPH = 'א'


class PressedType(Enum):
    PARENT = auto()
    BORDER = auto()
    INNER = auto()
    CHILD = auto()


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def shift(self, x, y):
        return Point(self.x + x, self.y + y)


def unique(items: List) -> List:
    final = []
    for item in items:
        if item not in final:
            final.append(item)
    return final


def line_width(typ: str, scale: float) -> int:
    return max(math.ceil(LINE_WIDTHS[typ] * scale), MIN_LINE_WIDTH[typ])


def half_line_distance(scale: float) -> float:
    return max(HALF_LINE_DISTANCE * scale, MIN_HALF_LINE_DISTANCE)
