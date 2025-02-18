from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from PIL import Image

from ....config import SYLLABLE_COLOR, SYLLABLE_BG, WORD_IMAGE_RADIUS, DIGIT_SCALE_MIN, DIGIT_SCALE_MAX
from ....core.tools import AnimationProperties
from ....core.utils import Point, PressedType, create_empty_image, ensure_min_radius
from ....core.writing.characters import Character, CharacterType
from ....core.writing.common.circles import DistanceInfo, InnerCircle, BorderInfo


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

        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.inner_circle = InnerCircle(self.IMAGE_CENTER, distance_info)
        self.inner_circle.initialize(borders)

        self.scale = 1.0
        self.outer_radius = 0.0
        self.base_inner_radius = 0.0
        self.base_stripe_width = 0.0

        # Image-related attributes
        self._image, self._draw = create_empty_image(self.IMAGE_CENTER)
        self._mask_image, self._mask_draw = create_empty_image(self.IMAGE_CENTER, '1')
        self._image_ready = False

        self._pressed_type: Optional[PressedType] = None
        self._distance_bias = 0.0

    @staticmethod
    def get_digit(text: str, border: str, digit_type_code: str) -> Digit:
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
        if not self.inner_circle.inside_circle(distance) and self.inner_circle.on_circle(distance):
            self._distance_bias = distance - self.inner_circle.radius
            self._pressed_type = PressedType.INNER
            return True
        return False

    @abstractmethod
    def move(self, point: Point) -> None:
        """Handle a move event to a given point."""
        if self._pressed_type == PressedType.INNER:
            self._adjust_scale(point)

    def update_inner_radius(self, base_inner_radius: float, base_stripe_width: float) -> None:
        """Resize the inner circle based on the number's scale."""
        self.base_inner_radius = base_inner_radius
        self.base_stripe_width = base_stripe_width
        inner_radius = base_inner_radius + base_stripe_width * self.scale
        if self.inner_circle.num_borders() > 1:
            inner_radius += 2 * self.distance_info.half_distance
        self.inner_circle.set_radius(inner_radius)

        self._mask_draw.rectangle(((0, 0), self._mask_image.size), fill=1)
        self.inner_circle.create_circle(self.color, self.background, self._mask_draw)
        self._image_ready = False

    def update_outer_radius(self, outer_radius: float, border_info: BorderInfo) -> None:
        self.outer_radius = outer_radius

    def paste_image(self, image: Image.Image) -> None:
        if not self._image_ready:
            self._create_image()
        image.paste(self._image, mask=self._mask_image)

    def _create_image(self):
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)
        self._redraw_decorations()
        self.inner_circle.redraw_circle(self._draw)
        self._image_ready = True

    def _redraw_decorations(self):
        pass

    def scale_borders(self, scale: float) -> None:
        """Scale the lines in the digit."""
        self.distance_info.scale_distance(scale)
        self.inner_circle.scale_borders(scale)

    def set_scale(self, scale: float):
        """Set the inner circle scale and update related properties."""
        self.scale = scale

    def _adjust_scale(self, point: Point):
        """Adjust the inner scale based on the moved distance."""
        distance = point.distance()
        new_stripe_width = distance - self._distance_bias - self.base_inner_radius
        if self.inner_circle.num_borders() > 1:
            new_stripe_width -= 2 * self.distance_info.half_distance
        self.set_scale(min(max(new_stripe_width / self.base_stripe_width, DIGIT_SCALE_MIN), DIGIT_SCALE_MAX))

    def apply_color_changes(self):
        self.inner_circle.create_circle(self.color, self.background)
        self._update_argument_dictionaries()
        self._image_ready = False

    def _update_argument_dictionaries(self) -> None:
        pass

    def perform_animation(self, direction_sign: int) -> None:
        pass


class _DigitCircle:
    def __init__(self):
        self.distance = 0.0
        self.center = Point()
        self.direction = random.uniform(0, 2 * math.pi)

        self.radius = 0.0
        self.radii = [0.0]

    def set_direction(self, direction: float):
        self.direction = direction
        self._calculate_center()

    def _calculate_center(self):
        """Calculate the positions of the circle based on the current direction."""
        self.center = Point(math.cos(self.direction) * self.distance, math.sin(self.direction) * self.distance)

    def set_distance_and_radius(self, distance: float, radius: float):
        self.distance = distance
        self.radius = radius
        self.radii = [radius]
        self._calculate_center()

    def set_second_radius(self, radius: float):
        self.radii.append(radius)


class CircularDigit(Digit):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, DigitType.CIRCULAR)

        num_borders = len(set(borders))
        self.circles = [_DigitCircle() for _ in range(num_borders)]
        self._ellipse_args: list[dict] = []

        self._pressed_circle: Optional[_DigitCircle] = None
        self._bias = Point()

    def press(self, point: Point) -> bool:
        if super().press(point):
            return True

        for circle in reversed(self.circles):
            delta = point - circle.center
            if delta.distance() < circle.radius:
                self._bias = delta
                self._pressed_type = PressedType.CHILD
                self._pressed_circle = circle
                return True
        return False

    def move(self, point: Point):
        super().move(point)
        if self._pressed_type == PressedType.CHILD:
            point -= self._bias
            self._pressed_circle.set_direction(point.direction())
            self._update_argument_dictionaries()
            self._image_ready = False


    def update_outer_radius(self, outer_radius: float, border_info: BorderInfo):
        super().update_outer_radius(outer_radius, border_info)
        outer_half_width = border_info.half_line_widths[-1]
        inner_half_width = self.inner_circle.border_info.half_line_widths[0]

        for i, circle in enumerate(self.circles):
            circle_half_width = self.inner_circle.border_info.half_line_widths[i]
            outer_distance_adjustment = abs(outer_half_width - circle_half_width)
            inner_distance_adjustment = abs(inner_half_width - circle_half_width)

            circle_start = self.inner_circle.radius + inner_distance_adjustment
            circle_end = outer_radius - outer_distance_adjustment
            radius = ensure_min_radius((circle_end - circle_start) / 2)
            distance = circle_start + radius
            circle.set_distance_and_radius(distance, radius)

            if self.inner_circle.border_info.borders == '11':
                radius = ensure_min_radius(circle.radius - 2 * self.distance_info.half_distance)
                circle.set_second_radius(radius)

        self._update_argument_dictionaries()

    def _get_bounds(self, center: Point, radius: float) -> tuple[tuple[int, int], tuple[int, int]]:
        """Calculate bounding box for an ellipse."""
        start = (self.IMAGE_CENTER + center).shift(-radius).tuple()
        end = (self.IMAGE_CENTER + center).shift(radius).tuple()
        return start, end

    def _update_argument_dictionaries(self):
        widths = self.inner_circle.border_info.line_widths
        half_widths = self.inner_circle.border_info.half_line_widths
        self._ellipse_args = [{'xy': self._get_bounds(circle.center, radius + half_width),
                               'outline': self.color, 'fill': self.background, 'width': width}
                              for circle, width, half_width in zip(self.circles, widths, half_widths)
                              for radius in circle.radii]

    def _redraw_decorations(self):
        """Draw the digit as a circle on the given image."""
        for args in self._ellipse_args:
            self._draw.ellipse(**args)

    def perform_animation(self, direction_sign: int):
        delta = 2 * math.pi / AnimationProperties.cycle
        for i, circle in enumerate(self.circles):
            circle.set_direction(circle.direction + direction_sign * 2 * delta)
            direction_sign = -direction_sign

        self._update_argument_dictionaries()
        self._image_ready = False


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
        half_distance = self.distance_info.half_distance
        return (self.inner_circle.radius < rotated.x < self.outer_radius and
                -half_distance < rotated.y < half_distance)

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
        self._update_argument_dictionaries()
        self._image_ready = False

    def update_outer_radius(self, outer_radius, border_info: BorderInfo):
        """Update digit properties after resizing based on the given syllable."""
        super().update_outer_radius(outer_radius, border_info)
        self._calculate_endpoint()
        self._update_argument_dictionaries()

    def _calculate_endpoint(self) -> None:
        """Helper method to calculate an endpoint given an angle."""
        self._end = Point(math.cos(self.direction) * self.outer_radius,
                          math.sin(self.direction) * self.outer_radius)

    def _update_argument_dictionaries(self):
        line_widths = self.inner_circle.border_info.line_widths
        if self.inner_circle.num_borders() > 1:
            half_distance = self.distance_info.half_distance
            d = Point(math.cos(self.direction + math.pi / 2) * half_distance,
                      math.sin(self.direction + math.pi / 2) * half_distance)
            start1 = (self.IMAGE_CENTER + d).tuple()
            end1 = (self.IMAGE_CENTER + self._end + d).tuple()
            start2 = (self.IMAGE_CENTER - d).tuple()
            end2 = (self.IMAGE_CENTER + self._end - d).tuple()

            self._draw.polygon(xy=(start1, end1, end2, start2), outline=self.background, fill=self.background)
            self._draw.line(xy=(start1, end1), fill=self.color, width=line_widths[0])
            self._draw.line(xy=(start2, end2), fill=self.color, width=line_widths[1])

            self._polygon_args = {'xy': (start1, end1, end2, start2),
                                  'outline': self.background, 'fill': self.background}
            self._line_args = [{'xy': (start1, end1), 'fill': self.color, 'width': line_widths[0]},
                               {'xy': (start2, end2), 'fill': self.color, 'width': line_widths[1]}]
        else:
            self._polygon_args = {}
            self._line_args = [{'xy': (self.IMAGE_CENTER.tuple(), (self.IMAGE_CENTER + self._end).tuple()),
                                'fill': self.color, 'width': line_widths[0]}]

    def _redraw_decorations(self):
        """Draw the digit as a line."""
        if self._polygon_args:
            self._draw.polygon(**self._polygon_args)

        for line_arg in self._line_args:
            self._draw.line(**line_arg)


    def perform_animation(self, direction_sign: int):
        delta = direction_sign * 2 * math.pi / AnimationProperties.cycle
        self.set_direction(self.direction + 2 * delta)
