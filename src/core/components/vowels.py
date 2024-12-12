import math
from abc import ABC
from enum import Enum
from typing import List, Dict

from src.utils import Point, PressedType, line_width, half_line_distance, MIN_RADIUS, \
    SYLLABLE_COLOR, SYLLABLE_BG
from .letters import Letter, LetterType


class VowelDecoration(str, Enum):
    LARGE = 'l'
    WANDERING = 'w'
    ROTATING = 'r'
    CENTER = 'c'
    HIDDEN = 'h'


class Vowel(Letter, ABC):
    """Base class for vowel decorations."""

    def __init__(self, text: str, borders: str, decoration_type: VowelDecoration):
        super().__init__(text, LetterType.VOWEL, borders)
        self.decoration_type = decoration_type

        self._radius = 0.0
        self._distance = 0.0
        self._center = Point()
        self._bias = Point()
        self.pressed_type = PressedType.PARENT
        self._ellipse_args: List[Dict] = []

    def press(self, point: Point) -> bool:
        delta = point - self._center
        if delta.distance() < self._radius:
            self._bias = delta
            self.pressed_type = PressedType.PARENT
            return True
        return False

    def move(self, point: Point):
        if self.pressed_type == PressedType.PARENT:
            point -= self._bias
            self._set_direction(point.direction())
            self._update_image_properties()

    def draw_decoration(self):
        for args in self._ellipse_args:
            self._image.ellipse(**args)

    def _update_ellipse_args(self, radii: List[float]):
        """Helper to calculate ellipse arguments."""
        self._ellipse_args = []
        for i, width in enumerate(self.line_widths):
            adjusted_radius = radii[i] + self.half_line_widths[i]
            start = (self.IMAGE_CENTER + self._center).shift(-adjusted_radius)
            end = (self.IMAGE_CENTER + self._center).shift(adjusted_radius)
            self._ellipse_args.append({'xy': (start, end), 'outline': SYLLABLE_COLOR,
                                       'fill': SYLLABLE_BG, 'width': width})

    def _calculate_center(self):
        self._center = Point(math.cos(self.direction) * self._distance, math.sin(self.direction) * self._distance)

    @staticmethod
    def get_vowel(text: str, border: str, decoration_code: str):
        decoration_type = VowelDecoration(decoration_code)
        decoration_map = {
            VowelDecoration.LARGE: LargeVowel,
            VowelDecoration.WANDERING: WanderingVowel,
            VowelDecoration.ROTATING: RotatingVowel,
            VowelDecoration.CENTER: CenterVowel,
            VowelDecoration.HIDDEN: HiddenVowel,
        }
        if decoration_type not in decoration_map:
            raise ValueError(f"No such vowel decoration: {decoration_type} (letter={text})")
        return decoration_map[decoration_type](text, border)


class LargeVowel(Vowel):
    DEFAULT_RATIO = 0.75

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.LARGE)

    def _update_syllable_properties(self, syllable):
        # super()._update_syllable_properties(syllable)
        scale = syllable.scale * self.DEFAULT_RATIO
        self.line_widths = [line_width(x, scale) for x in self.borders]
        self.half_line_widths = [w / 2 for w in self.line_widths]
        self._half_line_distance = half_line_distance(scale)
        self._radius = syllable.outer_radius * self.DEFAULT_RATIO
        self._distance = self._radius

    def _update_image_properties(self):
        self._calculate_center()
        radii = [max(self._radius - i * 2 * self._half_line_distance, MIN_RADIUS) for i in range(len(self.borders))]
        self._update_ellipse_args(radii)


class WanderingVowel(Vowel):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.WANDERING)

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        outer_radius, inner_radius, offset = syllable.outer_radius, syllable.inner_radius, syllable.offset
        self._distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)
        self._radius = max((outer_radius - offset[0] - inner_radius - offset[1]) / 2 - 3 * syllable.half_line_distance,
                           MIN_RADIUS)

    def _update_image_properties(self):
        self._calculate_center()
        if len(self.borders) == 1:
            radii = [self._radius]
        else:
            radii = [self._radius + self._half_line_distance, max(self._radius - self._half_line_distance, MIN_RADIUS)]
        self._update_ellipse_args(radii)


class RotatingVowel(Vowel):
    RATIO = 0.45

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.ROTATING)

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        self._radius = syllable.inner_radius * self.RATIO
        self._distance = syllable.inner_radius + syllable.offset[1]

    def _update_image_properties(self):
        self._calculate_center()
        if len(self.borders) == 1:
            radii = [self._radius]
        else:
            radii = [self._radius + self._half_line_distance, max(self._radius - self._half_line_distance, MIN_RADIUS)]
        self._update_ellipse_args(radii)


class CenterVowel(Vowel):
    RATIO = 0.5

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.CENTER)

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        inner_radius = syllable.inner_radius - syllable.offset[1]
        self._radius = max((inner_radius - 3 * syllable.half_line_distance) * self.RATIO, MIN_RADIUS)
        self._distance = self._radius

    def _update_image_properties(self):
        self._calculate_center()
        if len(self.borders) == 1:
            radii = [self._radius]
        else:
            radii = [self._radius + self._half_line_distance, max(self._radius - self._half_line_distance, MIN_RADIUS)]
        self._update_ellipse_args(radii)


class HiddenVowel(RotatingVowel):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders)
        self.decoration_type = VowelDecoration.HIDDEN
