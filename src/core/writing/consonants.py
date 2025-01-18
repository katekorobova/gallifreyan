from __future__ import annotations

import math
import random
from abc import ABC
from collections import Counter
from enum import Enum

from PIL import ImageDraw

from .characters import Letter, LetterType
from ..utils import Point, line_width
from ...config import (SYLLABLE_BG, SYLLABLE_COLOR, DOT_COLOR,
                       DEFAULT_DOT_RADIUS, MIN_RADIUS)


class ConsonantType(Enum):
    """Enumeration of different consonant types with their codes and group values."""
    STRAIGHT_ANGLE = ('sa', 2)
    OBTUSE_ANGLE = ('oa', 2)
    REFLEX_ANGLE = ('ra', 2)
    BENT_LINE = ('bl', 1)
    RADIAL_LINE = ('rl', 1)
    DIAMETRAL_LINE = ('dl', 1)
    CIRCLE = ('cl', 3)
    MATCHING_DOTS = ('md', 4)
    DIFFERENT_DOTS = ('dd', 4)
    HOLLOW_DOT = ('hd', 4)
    SOLID_DOT = ('sd', 4)

    def __init__(self, code: str, group: int):
        """Initialize a consonant type with a specific code and group."""
        self.code = code
        self.group = group

    @classmethod
    def get_by_code(cls, code: str):
        """Retrieve a ConsonantType by its code."""
        for consonant_type in cls:
            if consonant_type.code == code:
                return consonant_type
        raise ValueError(f"Invalid consonant type code: {code}")


class Consonant(Letter, ABC):
    """Abstract base class for consonant representations."""
    background = SYLLABLE_BG
    color = SYLLABLE_COLOR

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        """Initialize a consonant with text, borders, and type."""
        super().__init__(text, LetterType.CONSONANT, borders)
        self.consonant_type = consonant_type
        self._distance = 0.0
        self._bias = Point()

    @staticmethod
    def get_consonant(text: str, border: str, consonant_type_code: str) -> Consonant:
        """Factory method to create an appropriate Consonant subclass."""
        consonant_type = ConsonantType.get_by_code(consonant_type_code)
        consonant_classes = {
            ConsonantType.STRAIGHT_ANGLE: StraightAngleConsonant,
            ConsonantType.OBTUSE_ANGLE: ObtuseAngleConsonant,
            ConsonantType.REFLEX_ANGLE: ReflexAngleConsonant,
            ConsonantType.BENT_LINE: BentLineConsonant,
            ConsonantType.RADIAL_LINE: RadialLineConsonant,
            ConsonantType.DIAMETRAL_LINE: DiametralLineConsonant,
            ConsonantType.CIRCLE: CircleConsonant,
            ConsonantType.MATCHING_DOTS: MatchingDotsConsonant,
            ConsonantType.DIFFERENT_DOTS: DifferentDotsConsonant,
            ConsonantType.HOLLOW_DOT: HollowDotConsonant,
            ConsonantType.SOLID_DOT: SolidDotConsonant}
        if consonant_type in consonant_classes:
            return consonant_classes[consonant_type](text, border)
        raise ValueError(f"Unsupported consonant type: {consonant_type}")

    @staticmethod
    def compatible(cons1: Consonant, cons2: Consonant) -> bool:
        """Determine compatibility between two consonants."""
        allow_double = {ConsonantType.OBTUSE_ANGLE, ConsonantType.CIRCLE}
        if cons1.consonant_type == cons2.consonant_type and cons1.consonant_type in allow_double:
            return True

        large_angles = {ConsonantType.STRAIGHT_ANGLE, ConsonantType.REFLEX_ANGLE, ConsonantType.DIAMETRAL_LINE}
        if cons1.consonant_type in large_angles and cons2.consonant_type in large_angles:
            return False

        full_data = {ConsonantType.RADIAL_LINE}
        unknown_order = {ConsonantType.DIAMETRAL_LINE}
        min_border = {
            ConsonantType.BENT_LINE, ConsonantType.STRAIGHT_ANGLE,
            ConsonantType.OBTUSE_ANGLE, ConsonantType.REFLEX_ANGLE,
            ConsonantType.CIRCLE}

        if cons1.consonant_type in full_data or cons2.consonant_type in full_data:
            return cons1.borders != cons2.borders
        if cons1.consonant_type in unknown_order or cons2.consonant_type in unknown_order:
            return Counter(cons1.borders) != Counter(cons2.borders)
        if cons1.consonant_type in min_border or cons2.consonant_type in min_border:
            return min(cons1.borders) != min(cons2.borders)

        return False


class LineBasedConsonant(Consonant, ABC):
    """Base class for consonants that use lines in their representation."""
    ANGLE = 0.0

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)

        self._ends = Point(), Point()
        self._pressed_id = 0
        self._line_width = 0.0
        self._half_line_width = 0.0
        self._line_args: list[dict] = []

    def _calculate_endpoints(self):
        """Calculate the endpoints for the line."""
        self._ends = [
            self._calculate_endpoint(self.direction - self.ANGLE),
            self._calculate_endpoint(self.direction + self.ANGLE)]

    def _calculate_endpoint(self, angle: float) -> Point:
        """Helper method to calculate an endpoint given an angle."""
        return Point(
            math.cos(angle) * self._distance,
            math.sin(angle) * self._distance)

    def press(self, point: Point) -> bool:
        """Check if a point interacts with the line."""
        if self._is_within_bounds(point, self.direction - self.ANGLE):
            self._pressed_id = 0
            self._bias = point - self._ends[0]
            return True
        if self._is_within_bounds(point, self.direction + self.ANGLE):
            self._pressed_id = 1
            self._bias = point - self._ends[1]
            return True
        return False

    def _is_within_bounds(self, point: Point, base_angle: float) -> bool:
        """Check if a point is within the interaction bounds."""
        distance = point.distance()
        angle = point.direction() - base_angle
        rotated = Point(math.cos(angle) * distance, math.sin(angle) * distance)
        return 0 < rotated[0] < self._distance and -self._half_line_distance < rotated[1] < self._half_line_distance

    def move(self, point: Point):
        """Move the line based on interaction."""
        point -= self._bias
        self.set_direction(point.direction() + (-self.ANGLE if self._pressed_id else self.ANGLE))

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)

        self._line_width = min(self.line_widths)
        self._half_line_width = self._line_width / 2
        self._distance = syllable.outer_radius
        self._calculate_endpoints()

    def _update_properties_after_rotation(self):
        super()._update_properties_after_rotation()
        self._calculate_endpoints()

    def update_argument_dictionaries(self):
        self._line_args = [
            {'xy': (self.IMAGE_CENTER, self.IMAGE_CENTER + end),
             'fill': self.color, 'width': self._line_width}
            for end in self._ends]

    def draw(self, image: ImageDraw.Draw):
        """Draw the consonant as a line."""
        for line_arg in self._line_args:
            image.line(**line_arg)


class BentLineConsonant(LineBasedConsonant):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.BENT_LINE)


class RadialLineConsonant(LineBasedConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.RADIAL_LINE)

        self._end = Point()
        self._polygon_args = {}
        self._set_personal_direction(random.uniform(0.7 * math.pi, 1.3 * math.pi))

    def press(self, point: Point) -> bool:
        """Check if a point interacts with this consonant."""
        if self._is_within_bounds(point, self.direction):
            self._bias = point - self._end
            return True
        return False

    def move(self, point: Point):
        """Update direction based on moved point."""
        point -= self._bias
        self.set_direction(point.direction())

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        self._end = self._calculate_endpoint(self.direction)

    def _update_properties_after_rotation(self):
        super()._update_properties_after_rotation()
        self._end = self._calculate_endpoint(self.direction)

    def update_argument_dictionaries(self):
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER, self.IMAGE_CENTER + self._end),
                'fill': self.color, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction + math.pi / 2) * self._half_line_distance,
                      math.sin(self.direction + math.pi / 2) * self._half_line_distance)

            start1, end1 = self.IMAGE_CENTER - d, self.IMAGE_CENTER + self._end - d
            start2, end2 = self.IMAGE_CENTER + d, self.IMAGE_CENTER + self._end + d

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': self.background, 'fill': self.background}
            self._line_args = [
                {'xy': (start1, end1), 'fill': self.color, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': self.color, 'width': self.line_widths[1]}]


class DiametralLineConsonant(LineBasedConsonant):
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.DIAMETRAL_LINE)

        self._set_personal_direction(0)
        self._polygon_args = {}

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        self._calculate_endpoints()

    def _update_properties_after_rotation(self):
        super()._update_properties_after_rotation()
        self._calculate_endpoints()

    def update_argument_dictionaries(self):
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER + self._ends[0], self.IMAGE_CENTER + self._ends[1]),
                'fill': self.color, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction) * self._half_line_distance,
                      math.sin(self.direction) * self._half_line_distance)

            start1, end1 = (self.IMAGE_CENTER + self._ends[0] - d, self.IMAGE_CENTER + self._ends[1] - d)
            start2, end2 = (self.IMAGE_CENTER + self._ends[0] + d, self.IMAGE_CENTER + self._ends[1] + d)

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': self.background, 'fill': self.background}
            self._line_args = [
                {'xy': (start1, end1), 'fill': self.color, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': self.color, 'width': self.line_widths[1]}]

    def draw(self, image: ImageDraw.Draw):
        """Draw the consonant."""
        if self._polygon_args:
            image.polygon(**self._polygon_args)

        super().draw(image)


class AngleBasedConsonant(LineBasedConsonant, ABC):
    """Base class for angle-based consonants."""

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)

        self._radius = 0.0
        self._arc_args = {}

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        self._radius = syllable.inner_radius + syllable.border_offset[1] + 2 * self._half_line_distance

    def update_argument_dictionaries(self):
        super().update_argument_dictionaries()
        adjusted_radius = self._radius + self._half_line_width
        start = self.IMAGE_CENTER.shift(-adjusted_radius)
        end = self.IMAGE_CENTER.shift(adjusted_radius)
        start_angle = math.degrees(self.direction - self.ANGLE)
        end_angle = math.degrees(self.direction + self.ANGLE)

        self._arc_args = {
            'xy': (start, end),
            'start': start_angle, 'end': end_angle,
            'fill': self.color, 'width': self._line_width
        }

    def draw(self, image: ImageDraw.Draw):
        """Draw a consonant with an arc."""
        super().draw(image)

        if self._arc_args:
            image.arc(**self._arc_args)


class StraightAngleConsonant(AngleBasedConsonant):
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.STRAIGHT_ANGLE)

        self._set_personal_direction(0)


class ObtuseAngleConsonant(AngleBasedConsonant):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.OBTUSE_ANGLE)


class ReflexAngleConsonant(AngleBasedConsonant):
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.REFLEX_ANGLE)

        self._set_personal_direction(0)


class DotConsonant(Consonant, ABC):
    color = DOT_COLOR

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)

        self._radius = 0.0
        self._line_width = 0.0

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        outer_radius, inner_radius, border_offset = syllable.outer_radius, syllable.inner_radius, syllable.border_offset

        self._line_width = line_width('1', syllable.scale)
        self._distance = max((outer_radius - border_offset[0] + inner_radius + border_offset[1]) / 2, MIN_RADIUS)
        self._radius = max(syllable.scale * DEFAULT_DOT_RADIUS, MIN_RADIUS)

    def _get_bounds(self, center: Point) -> dict:
        """Calculate bounding box for an ellipse."""

        start = (self.IMAGE_CENTER + center).shift(-self._radius)
        end = (self.IMAGE_CENTER + center).shift(self._radius)
        return {'xy': (start, end)}


class DoubleDotConsonant(DotConsonant, ABC):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)
        self._centers = Point(), Point()
        self._pressed_id = 0
        self._ellipse_args: list[dict] = []

    def press(self, point: Point) -> bool:
        for i, center in enumerate(self._centers):
            delta = point - center
            if delta.distance() < self._radius:
                self._bias = delta
                self._pressed_id = i
                return True
        return False

    def move(self, point: Point):
        point -= self._bias
        direction = point.direction()
        if self._pressed_id:
            self.set_direction(direction - self.ANGLE)
        else:
            self.set_direction(direction + self.ANGLE)

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        self._calculate_centers()

    def _update_properties_after_rotation(self):
        super()._update_properties_after_rotation()
        self._calculate_centers()

    def _calculate_centers(self):
        self._centers = (
            Point(math.cos(self.direction - self.ANGLE) * self._distance,
                  math.sin(self.direction - self.ANGLE) * self._distance),
            Point(math.cos(self.direction + self.ANGLE) * self._distance,
                  math.sin(self.direction + self.ANGLE) * self._distance))

    def draw(self, image: ImageDraw.Draw):
        for args in self._ellipse_args:
            image.ellipse(**args)


class MatchingDotsConsonant(DoubleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.MATCHING_DOTS)

    def update_argument_dictionaries(self):
        self._ellipse_args = [
            {**self._get_bounds(center), 'outline': self.color, 'fill': self.background, 'width': self._line_width}
            for center in self._centers]


class DifferentDotsConsonant(DoubleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.DIFFERENT_DOTS)

    def update_argument_dictionaries(self):
        self._ellipse_args = [
            {**self._get_bounds(self._centers[0]), 'fill': self.color},
            {**self._get_bounds(self._centers[1]),
             'outline': self.color, 'fill': self.background, 'width': self._line_width}]


class SingleDotConsonant(DotConsonant, ABC):
    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)

        self._center = Point()
        self._ellipse_args = {}

    def press(self, point: Point) -> bool:
        delta = point - self._center
        if delta.distance() < self._radius:
            self._bias = delta
            return True
        return False

    def move(self, point: Point):
        point -= self._bias
        self.set_direction(point.direction())

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)
        self._calculate_center()

    def _update_properties_after_rotation(self):
        super()._update_properties_after_rotation()
        self._calculate_center()

    def _calculate_center(self):
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

    def draw(self, image: ImageDraw.Draw):
        image.ellipse(**self._ellipse_args)


class HollowDotConsonant(SingleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.HOLLOW_DOT)

    def update_argument_dictionaries(self):
        self._ellipse_args = {
            **self._get_bounds(self._center),
            'outline': self.color, 'fill': self.background, 'width': self._line_width}


class SolidDotConsonant(SingleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.SOLID_DOT)

    def update_argument_dictionaries(self):
        self._ellipse_args = {**self._get_bounds(self._center), 'fill': self.color}


class CircleConsonant(Consonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.CIRCLE)

        self._width = 0.0
        self._half_width = 0.0
        self._radius = 0.0
        self._center = Point()
        self._ellipse_args = {}
        self._set_personal_direction(random.uniform(0.7 * math.pi, 1.3 * math.pi))

    def press(self, point: Point) -> bool:
        delta = point - self._center
        if delta.distance() < self._radius:
            self._bias = delta
            return True
        return False

    def move(self, point: Point):
        point -= self._bias
        self.set_direction(point.direction())

    def _update_properties_after_resizing(self, syllable):
        super()._update_properties_after_resizing(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        border_offset = syllable.border_offset

        self._width = min(self.line_widths)
        self._half_width = self._width / 2
        self._radius = max((outer_radius - border_offset[0] - inner_radius - border_offset[1]) / 4, MIN_RADIUS)
        self._distance = inner_radius + border_offset[1] + self._radius
        self._calculate_center()

    def _update_properties_after_rotation(self):
        super()._update_properties_after_rotation()
        self._calculate_center()

    def _calculate_center(self):
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

    def update_argument_dictionaries(self):
        adjusted_radius = self._radius + self._half_width
        start = (self.IMAGE_CENTER + self._center).shift(-adjusted_radius)
        end = (self.IMAGE_CENTER + self._center).shift(adjusted_radius)
        self._ellipse_args = {'xy': (start, end), 'outline': self.color, 'fill': self.background, 'width': self._width}

    def draw(self, image: ImageDraw.Draw):
        image.ellipse(**self._ellipse_args)
