import math
from enum import Enum
from typing import List, Dict

from letters import Letter, LetterType
from utils import Point, PressedType, line_width, half_line_distance, MIN_RADIUS, \
    SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG


class VowelDecoration(str, Enum):
    LARGE = 'l'
    WANDERING = 'w'
    ROTATING = 'r'
    CENTER = 'c'
    HIDDEN = 'h'


class Vowel(Letter):

    def __init__(self, text: str, borders: str, decoration_type: VowelDecoration):
        super().__init__(text, LetterType.VOWEL, borders)
        self.decoration_type = decoration_type
        self._center, self._radius = None, None
        self._bias = None

        self.pressed_type = PressedType.PARENT

        self._ellipse_arg_dicts: List[Dict] = []

    def press(self, point: Point) -> bool:
        delta = point - self._center
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self._radius:
            self._bias = delta
            self.pressed_type = PressedType.PARENT
            return True
        return False

    def move(self, point: Point):
        match self.pressed_type:
            case PressedType.PARENT:
                point = point - self._bias
                direction = math.atan2(point.y, point.x)
                self.direction = direction
                self._update_image_properties()

    def draw_decoration(self):
        for args in self._ellipse_arg_dicts:
            self._image.ellipse(**args)

    @staticmethod
    def get_vowel(text: str, border: str, decoration_code: str):
        decoration_type = VowelDecoration(decoration_code)
        match decoration_type:
            case VowelDecoration.LARGE:
                return LargeVowel(text, border)
            case VowelDecoration.WANDERING:
                return WanderingVowel(text, border)
            case VowelDecoration.ROTATING:
                return RotatingVowel(text, border)
            case VowelDecoration.CENTER:
                return CenterVowel(text, border)
            case VowelDecoration.HIDDEN:
                return HiddenVowel(text, border)
            case _:
                raise ValueError(f'No such vowel decoration: {decoration_type} (letter={text})')


class LargeVowel(Vowel):
    DEFAULT_RATIO = 0.75
    MIN_RATIO = 0.5
    MAX_RATIO = 1

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.LARGE)

    def update_syllable_properties(self, syllable):
        outer_radius = syllable.outer_radius
        scale = syllable.scale * self.DEFAULT_RATIO

        self.widths = list(map(lambda x: line_width(x, scale), self.borders))
        self.half_widths = list(map(lambda x: x / 2, self.widths))
        self._half_line_distance = half_line_distance(scale)
        self._radius = outer_radius * self.DEFAULT_RATIO
        self._update_image_properties()

    def _update_image_properties(self):
        self._center = Point(math.cos(self.direction) * self._radius,
                             math.sin(self.direction) * self._radius)

        self._ellipse_arg_dicts = []
        for i, border in enumerate(self.borders):
            circle_radius = max(self._radius - i * 2 * self._half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - circle_radius - self.half_widths[i]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + circle_radius + self.half_widths[i]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - circle_radius - self.half_widths[i]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + circle_radius + self.half_widths[i]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom), 'outline': SYLLABLE_COLOR,
                                            'fill': SYLLABLE_BG, 'width': self.widths[i]})


class WanderingVowel(Vowel):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.WANDERING)

        self.__distance = None

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)
        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self.__distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)

        # TODO different radii for singular and double circles
        self._radius = max((outer_radius - offset[0] - inner_radius - offset[1]) / 2 - 3 * syllable.half_line_distance,
                           MIN_RADIUS)

        self._update_image_properties()

    def _update_image_properties(self):
        self._center = Point(math.cos(self.direction) * self.__distance,
                             math.sin(self.direction) * self.__distance)
        if len(self.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - self._radius - self.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + self._radius + self.half_widths[0]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - self._radius - self.half_widths[0]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + self._radius + self.half_widths[0]
            self._ellipse_arg_dicts = [{'xy': (left, top, right, bottom), 'outline': SYLLABLE_COLOR,
                                        'fill': SYLLABLE_BG, 'width': self.widths[0]}]
        else:
            self._ellipse_arg_dicts = []
            radius = self._radius + self._half_line_distance
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - radius - self.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + radius + self.half_widths[0]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - radius - self.half_widths[0]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + radius + self.half_widths[0]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom), 'outline': SYLLABLE_COLOR,
                                            'fill': SYLLABLE_BG, 'width': self.widths[0]})

            radius = max(self._radius - self._half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - radius - self.half_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + radius + self.half_widths[1]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - radius - self.half_widths[1]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + radius + self.half_widths[1]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom), 'outline': SYLLABLE_COLOR,
                                            'fill': SYLLABLE_BG, 'width': self.widths[1]})


class RotatingVowel(Vowel):
    RATIO = 0.45

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.ROTATING)

        self.__distance = None

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)
        self._radius = syllable.inner_radius * self.RATIO
        self.__distance = syllable.inner_radius + syllable.offset[1]
        self._update_image_properties()

    def _update_image_properties(self):
        self._center = Point(math.cos(self.direction) * self.__distance,
                             math.sin(self.direction) * self.__distance)

        self._ellipse_arg_dicts = []
        if len(self.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - self._radius - self.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + self._radius + self.half_widths[0]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - self._radius - self.half_widths[0]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + self._radius + self.half_widths[0]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                            'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.widths[0]})
        else:
            circle_radius = self._radius + self._half_line_distance
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - circle_radius - self.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + circle_radius + self.half_widths[0]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - circle_radius - self.half_widths[0]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + circle_radius + self.half_widths[0]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                            'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.widths[0]})

            circle_radius = max(self._radius - self._half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - circle_radius - self.half_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + circle_radius + self.half_widths[1]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - circle_radius - self.half_widths[1]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + circle_radius + self.half_widths[1]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                            'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.widths[1]})


class CenterVowel(Vowel):
    RATIO = 0.5

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, VowelDecoration.CENTER)

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)
        inner_radius = syllable.inner_radius
        offset = syllable.offset
        inner_radius -= offset[1]

        # TODO different radii for singular and double circles
        self._radius = (inner_radius - 3 * syllable.half_line_distance) * self.RATIO
        self._update_image_properties()

    def _update_image_properties(self):
        self._center = Point(math.cos(self.direction) * self._radius,
                             math.sin(self.direction) * self._radius)

        if len(self.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - self._radius - self.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + self._radius + self.half_widths[0]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - self._radius - self.half_widths[0]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + self._radius + self.half_widths[0]
            self._ellipse_arg_dicts = [{'xy': (left, top, right, bottom),
                                        'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.widths[0]}]
        else:
            self._ellipse_arg_dicts = []
            circle_radius = self._radius + self._half_line_distance
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - circle_radius - self.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + circle_radius + self.half_widths[0]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - circle_radius - self.half_widths[0]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + circle_radius + self.half_widths[0]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                            'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.widths[0]})

            circle_radius = max(self._radius - self._half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS + self._center.x - circle_radius - self.half_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + self._center.x + circle_radius + self.half_widths[1]
            top = SYLLABLE_IMAGE_RADIUS + self._center.y - circle_radius - self.half_widths[1]
            bottom = SYLLABLE_IMAGE_RADIUS + self._center.y + circle_radius + self.half_widths[1]
            self._ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                            'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.widths[1]})


class HiddenVowel(RotatingVowel):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders)
        self.decoration_type = VowelDecoration.HIDDEN
