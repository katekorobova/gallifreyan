import math
from abc import ABC
from enum import Enum
from itertools import repeat

from PIL import ImageDraw

from .characters import Letter, LetterType
from ..utils import Point, PressedType, line_width, half_line_distance
from ...config import VOWEL_COLOR, MIN_RADIUS, SYLLABLE_BG


class VowelType(str, Enum):
    LARGE = 'l'
    WANDERING = 'w'
    ORBITING = 'o'
    CENTER = 'c'
    HIDDEN = 'h'


class Vowel(Letter, ABC):
    """Base class for vowels."""
    background = SYLLABLE_BG
    color = VOWEL_COLOR

    def __init__(self, text: str, borders: str, vowel_type: VowelType):
        super().__init__(text, LetterType.VOWEL, borders)
        self.vowel_type = vowel_type
        self._radius = 0.0
        self._distance = 0.0
        self._center = Point()
        self._bias = Point()
        self.pressed_type = PressedType.PARENT
        self._radii = list(repeat(0.0, len(borders)))
        self._ellipse_args: list[dict] = []

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
            self.set_direction(point.direction())

    def draw(self, image: ImageDraw.Draw):
        for args in self._ellipse_args:
            image.ellipse(**args)

    def update_argument_dictionaries(self):
        self._ellipse_args = []
        for width, half_width, radius in zip(self.line_widths, self.half_line_widths, self._radii):
            adjusted_radius = radius + half_width
            start = (self.IMAGE_CENTER + self._center).shift(-adjusted_radius)
            end = (self.IMAGE_CENTER + self._center).shift(adjusted_radius)
            self._ellipse_args.append({'xy': (start, end), 'outline': self.color,
                                       'fill': self.background, 'width': width})

    def _calculate_center_and_radii(self):
        self._center = Point(math.cos(self.direction) * self._distance, math.sin(self.direction) * self._distance)
        self._radii = [max(self._radius - i * 2 * self._half_line_distance, MIN_RADIUS)
                       for i in range(len(self.borders))]

    @staticmethod
    def get_vowel(text: str, border: str, vowel_type_code: str):
        vowel_type = VowelType(vowel_type_code)
        vowel_classes = {
            VowelType.LARGE: LargeVowel,
            VowelType.WANDERING: WanderingVowel,
            VowelType.ORBITING: OrbitingVowel,
            VowelType.CENTER: CenterVowel,
            VowelType.HIDDEN: HiddenVowel,
        }
        if vowel_type not in vowel_classes:
            raise ValueError(f"No such vowel type: '{vowel_type}' (letter='{text}')")
        return vowel_classes[vowel_type](text, border)


class LargeVowel(Vowel):
    DEFAULT_RATIO = 0.75

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelType.LARGE)
        self._set_personal_direction(0)

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)

        scale = syllable.scale * self.DEFAULT_RATIO
        self.line_widths = [line_width(x, scale) for x in self.borders]
        self.half_line_widths = [w / 2 for w in self.line_widths]
        self._half_line_distance = half_line_distance(scale)
        self._radius = syllable.outer_radius * self.DEFAULT_RATIO
        self._distance = self._radius
        self._calculate_center_and_radii()

    def _update_properties_after_rotation(self):
        self._calculate_center_and_radii()


class WanderingVowel(Vowel):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelType.WANDERING)

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)

        outer_radius, inner_radius, border_offset = syllable.outer_radius, syllable.inner_radius, syllable.border_offset
        self._distance = max((outer_radius - border_offset[0] + inner_radius + border_offset[1]) / 2, MIN_RADIUS)
        self._radius = max((outer_radius - border_offset[0] - inner_radius - border_offset[1]) / 2
                           - 3 * syllable.half_line_distance, MIN_RADIUS)
        self._calculate_center_and_radii()

    def _update_properties_after_rotation(self):
        self._calculate_center_and_radii()


class OrbitingVowel(Vowel):
    RATIO = 0.45

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelType.ORBITING)

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        self._radius = syllable.inner_radius * self.RATIO
        self._distance = syllable.inner_radius + syllable.border_offset[1]
        self._calculate_center_and_radii()

    def _update_properties_after_rotation(self):
        self._calculate_center_and_radii()


class CenterVowel(Vowel):
    RATIO = 0.5

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelType.CENTER)

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        inner_radius = syllable.inner_radius - syllable.border_offset[1]
        self._radius = max((inner_radius - 3 * syllable.half_line_distance) * self.RATIO, MIN_RADIUS)
        self._distance = self._radius
        self._calculate_center_and_radii()

    def _update_properties_after_rotation(self):
        self._calculate_center_and_radii()


class HiddenVowel(OrbitingVowel):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders)
        self.vowel_type = VowelType.HIDDEN
