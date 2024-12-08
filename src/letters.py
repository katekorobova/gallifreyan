import math
import random
from abc import ABC
from enum import auto, Enum

from PIL import ImageDraw

from utils import Point, line_width


class LetterType(Enum):
    CONSONANT = auto()
    VOWEL = auto()


class Letter(ABC):

    def __init__(self, text: str, letter_type: LetterType, borders: str):
        self.text = text
        self.letter_type = letter_type
        self.borders = borders
        self.direction = random.uniform(-math.pi, math.pi)

        self.widths, self.half_widths = None, None

        self._half_line_distance = None
        self._image: ImageDraw = None

    def set_image(self, image):
        self._image = image

    def press(self, point: Point) -> bool:
        # implement where necessary
        pass

    def move(self, point: Point):
        # implement where necessary
        pass

    def update_syllable_properties(self, syllable):
        self.widths = list(map(lambda x: line_width(x, syllable.scale), self.borders))
        self.half_widths = list(map(lambda x: x / 2, self.widths))

        self._half_line_distance = syllable.half_line_distance

    def _update_image_properties(self):
        # implement where necessary
        pass

    def draw_decoration(self):
        # implement where necessary
        pass
