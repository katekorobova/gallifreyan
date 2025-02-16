from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from enum import Enum
from itertools import repeat
from typing import Optional

from PIL import ImageDraw, Image

from .characters import Character, CharacterType
from ..tools import AnimationProperties
from ..utils import Point, line_width, half_line_distance, PressedType
from ...config import SYLLABLE_COLOR, SYLLABLE_BG, MIN_RADIUS, WORD_IMAGE_RADIUS, DIGIT_SCALE_MIN, DIGIT_SCALE_MAX


class DigitType(str, Enum):
    """Enumeration for different types of digits."""
    CIRCULAR = 'c'
    LINE = 'l'


class Digit(Character, ABC):
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    color = SYLLABLE_COLOR
    background = SYLLABLE_BG

    def __init__(self, text: str, borders: str, digit_type: DigitType):
        super().__init__(text, CharacterType.DIGIT)
        self.digit_type = digit_type
        self.borders = borders

        length = len(borders)
        self.line_widths = list(repeat(0, length))
        self.half_line_widths = list(repeat(0.0, length))
        self._half_line_distance = 0.0
        self.scale = 1

        self.outer_radius = 0.0
        self.inner_radius = 0.0
        self._border_offset = 0.0
        self.previous_inner_radius = 0.0
        self.default_stripe_width = 0.0

        # Image-related attributes
        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')

        self._pressed_type: Optional[PressedType] = None
        self._distance_bias = 0.0

    @classmethod
    def _create_empty_image(cls, mode: str = 'RGBA') -> tuple[Image.Image, ImageDraw.ImageDraw]:
        """Create an empty image with the specified mode."""
        image = Image.new(mode, (cls.IMAGE_CENTER * 2).tuple())
        return image, ImageDraw.Draw(image)

    @staticmethod
    def get_digit(text: str, border: str, digit_type_code: str):
        """Factory method to create a vowel instance based on the given type code."""
        digit_type = DigitType(digit_type_code)
        digit_classes = {
            DigitType.CIRCULAR: CircularDigit,
            DigitType.LINE: LineDigit
        }
        if digit_type not in digit_classes:
            raise ValueError(f"No such digit type: '{digit_type}' (digit='{text}')")
        return digit_classes[digit_type](text, border)

    @abstractmethod
    def press(self, point: Point) -> bool:
        """Handle a press event at a given point."""
        distance = point.distance()
        if self.inner_radius < distance < self.inner_radius + 2 * self._half_line_distance:
            self._distance_bias = distance - self.inner_radius
            self._pressed_type = PressedType.INNER
            return True
        return False

    @abstractmethod
    def move(self, point: Point):
        """Handle a move event to a given point."""
        if self._pressed_type == PressedType.INNER:
            self._adjust_scale(point)

    def update_scale(self, number_scale: float):
        self.line_widths = [line_width(border, number_scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]
        self._half_line_distance = half_line_distance(number_scale)
        self._border_offset = (len(self.borders) - 1) * 2 * self._half_line_distance

    def update_inner_radius(self, previous_inner_radius: float, default_stripe_width: float):
        """Resize the inner circle based on the number's scale."""
        self.previous_inner_radius = previous_inner_radius
        self.default_stripe_width = default_stripe_width
        self.inner_radius = previous_inner_radius + default_stripe_width * self.scale
        self._create_inner_circle()

    def update_outer_radius(self, outer_radius: float):
        self.outer_radius = outer_radius
        self._create_mask()

    @abstractmethod
    def redraw(self):
        """Draw the digit."""
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

    def paste_decorations(self, image: Image.Image):
        image.paste(self._image, mask=self._mask_image)

    def paste_inner_circle(self, image: Image.Image):
        image.paste(self._border_image, mask=self._border_image)

    def _create_mask(self):
        self._mask_draw.rectangle(((0, 0), self._mask_image.size), fill=0)
        start = self.IMAGE_CENTER.shift(-self.outer_radius - 1).tuple()
        end = self.IMAGE_CENTER.shift(self.outer_radius + 1).tuple()
        self._mask_draw.ellipse((start, end), fill=1)

    def _create_inner_circle(self):
        """Draw the inner circle for the digit."""
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)

        if len(self.borders) == 1:
            adjusted_radius = self._calculate_adjusted_radius(
                self.inner_radius, self.half_line_widths[0])
            start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
            end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
            self._border_draw.ellipse((start, end), outline=self.color, width=self.line_widths[0])
        else:
            adjusted_radius = self._calculate_adjusted_radius(
                self.inner_radius, 2 * self._half_line_distance + self.half_line_widths[0])
            start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
            end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
            self._border_draw.ellipse((start, end), outline=self.color,
                                      fill=self.background, width=self.line_widths[0])

            adjusted_radius = self._calculate_adjusted_radius(self.inner_radius, self.half_line_widths[0])
            start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
            end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
            self._border_draw.ellipse((start, end), outline=self.color, fill=0, width=self.line_widths[1])

    @staticmethod
    def _calculate_adjusted_radius(
            base_radius: float, adjustment: float, min_radius: float = MIN_RADIUS):
        """Calculate an adjusted radius with constraints."""
        return max(base_radius + adjustment, min_radius)

    def _create_circle_args(self, adjusted_radius: float, width: float) -> dict:
        """Generate circle arguments for drawing."""
        start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
        end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
        return {'xy': (start, end), 'outline': self.color, 'fill': self.background, 'width': width}

    def set_scale(self, scale: float):
        """Set the inner circle scale and update related properties."""
        self.scale = scale

    def _adjust_scale(self, point: Point):
        """Adjust the inner scale based on the moved distance."""
        distance = point.distance()
        new_stripe_width = distance - self._distance_bias - self.previous_inner_radius
        self.set_scale(min(max(new_stripe_width / self.default_stripe_width, DIGIT_SCALE_MIN), DIGIT_SCALE_MAX))

    def apply_color_changes(self):
        self._create_inner_circle()
        self.redraw()

    def perform_animation(self, direction_sign: int):
        pass

class CircularDigit(Digit):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, DigitType.CIRCULAR)

        seen = []
        self.unique_borders = ''.join(border for border in borders
                                      if not (border in seen or seen.append(border)))
        self._pressed_id = 0
        self._bias = Point()
        self._radius = 0.0
        self._radii: list[float] = []
        self._distance = 0.0
        self._centers = [Point() for _ in self.unique_borders]
        self.directions = [random.uniform(0, 2 * math.pi) for _ in self.unique_borders]
        self._ellipse_args: list[dict] = []

    def press(self, point: Point) -> bool:
        if super().press(point):
            return True

        for i in range(len(self._centers) - 1, -1, -1):
            delta = point - self._centers[i]
            if delta.distance() < self._radius:
                self._bias = delta
                self._pressed_type = PressedType.PARENT
                self._pressed_id = i
                return True
        return False

    def move(self, point: Point):
        super().move(point)
        if self._pressed_type == PressedType.PARENT:
            point -= self._bias
            self.set_direction(point.direction(), self._pressed_id)

    def set_direction(self, direction: float, index: int):
        """Set a new direction for the letter."""
        self.directions[index] = direction
        self._calculate_centers()
        self.redraw()

    def update_outer_radius(self, outer_radius: float):
        super().update_outer_radius(outer_radius)
        self._radius = max((self.outer_radius - self.inner_radius - self._border_offset) / 2, MIN_RADIUS)
        self._distance = self.inner_radius + self._border_offset + self._radius
        self._calculate_centers()
        self._radii = [self._radius]
        if self.borders == '11':
            self._radii.append(max(self._radius - 2 * self._half_line_distance, MIN_RADIUS))


    def _calculate_centers(self):
        """Calculate the positions of the two dot centers based on the current direction."""
        self._centers = [Point(math.cos(direction) * self._distance, math.sin(direction) * self._distance)
                         for direction in self.directions]

    def _get_bounds(self, center: Point, radius: float) -> tuple[tuple[int, int], tuple[int, int]]:
        """Calculate bounding box for an ellipse."""
        start = (self.IMAGE_CENTER + center).shift(-radius).tuple()
        end = (self.IMAGE_CENTER + center).shift(radius).tuple()
        return start, end

    def redraw(self):
        """Draw the digit as a circle on the given image."""
        super().redraw()
        for center, width in zip(self._centers, self.line_widths):
            for radius in self._radii:
                self._draw.ellipse(xy=self._get_bounds(center, radius),
                                   outline=self.color, fill=self.background, width=width)

    def perform_animation(self, direction_sign: int):
        delta = 2 * math.pi / AnimationProperties.cycle
        for i, direction in enumerate(self.directions):
            self.set_direction(direction + direction_sign * 2 * delta, i)
            direction_sign = -direction_sign


class LineDigit(Digit):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, DigitType.LINE)
        self.direction = random.uniform(0, 2 * math.pi)

        self._end = Point()
        self._bias = Point()
        self._line_args: list[dict] = []
        self._polygon_args = {}

    def _is_within_bounds(self, point: Point, base_angle: float) -> bool:
        """Check if a point is within the interaction bounds."""
        distance = point.distance()
        angle = point.direction() - base_angle
        rotated = Point(math.cos(angle) * distance, math.sin(angle) * distance)
        return (self.inner_radius + self._border_offset < rotated.x < self.outer_radius and
                -self._half_line_distance < rotated.y < self._half_line_distance)

    def press(self, point: Point) -> bool:
        if super().press(point):
            return True

        if self._is_within_bounds(point, self.direction):
            self._bias = point - self._end
            self._pressed_type = PressedType.PARENT
            return True
        return False

    def move(self, point: Point):
        super().move(point)
        if self._pressed_type == PressedType.PARENT:
            point -= self._bias
            self.set_direction(point.direction())

    def set_direction(self, direction: float):
        """Set a new direction for the letter."""
        self.direction = direction
        self._calculate_endpoint()
        self.redraw()

    def update_outer_radius(self, outer_radius):
        """Update digit properties after resizing based on the given syllable."""
        super().update_outer_radius(outer_radius)
        self._calculate_endpoint()

    def _calculate_endpoint(self) -> None:
        """Helper method to calculate an endpoint given an angle."""
        self._end = Point(math.cos(self.direction) * self.outer_radius,
                          math.sin(self.direction) * self.outer_radius)

    def redraw(self):
        """Draw the digit as a line."""
        super().redraw()
        if len(self.borders) == 1:
            self._draw.line(xy=(self.IMAGE_CENTER.tuple(), (self.IMAGE_CENTER + self._end).tuple()),
                            fill=self.color, width=self.line_widths[0])
        else:
            d = Point(math.cos(self.direction + math.pi / 2) * self._half_line_distance,
                      math.sin(self.direction + math.pi / 2) * self._half_line_distance)
            start1 = (self.IMAGE_CENTER + d).tuple()
            end1 = (self.IMAGE_CENTER + self._end + d).tuple()
            start2 = (self.IMAGE_CENTER - d).tuple()
            end2 = (self.IMAGE_CENTER + self._end - d).tuple()

            self._draw.polygon(xy=(start1, end1, end2, start2), outline=self.background, fill=self.background)
            self._draw.line(xy=(start1, end1), fill=self.color, width=self.line_widths[0])
            self._draw.line(xy=(start2, end2), fill=self.color, width=self.line_widths[1])

    def perform_animation(self, direction_sign: int):
        delta = direction_sign * 2 * math.pi / AnimationProperties.cycle
        self.set_direction(self.direction + 2 * delta)