from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections import Counter
from enum import Enum

from .characters import Letter, LetterType
from ..utils import Point, line_width
from ...config import (SYLLABLE_BG, SYLLABLE_COLOR, DOT_COLOR,
                       DEFAULT_DOT_RADIUS, MIN_RADIUS)


class ConsonantType(Enum):
    STRAIGHT_ANGLE = ('sa', 2)
    OBTUSE_ANGLE = ('oa', 2)
    REFLEX_ANGLE = ('ra', 2)
    BENT_LINE = ('bl', 1)
    RADIAL_LINE = ('rl', 1)
    DIAMETRAL_LINE = ('dl', 1)
    CIRCLE = ('cl', 3)
    SIMILAR_DOTS = ('sd', 4)
    DIFFERENT_DOTS = ('dd', 4)
    WHITE_DOT = ('wd', 4)
    BLACK_DOT = ('bd', 4)

    def __init__(self, code: str, group: int):
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
    BACKGROUND = SYLLABLE_BG
    COLOR = SYLLABLE_COLOR

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
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
            ConsonantType.SIMILAR_DOTS: SimilarDotConsonant,
            ConsonantType.DIFFERENT_DOTS: DifferentDotConsonant,
            ConsonantType.WHITE_DOT: WhiteDotConsonant,
            ConsonantType.BLACK_DOT: BlackDotConsonant}
        if consonant_type in consonant_classes:
            return consonant_classes[consonant_type](text, border)
        raise ValueError(f"Unsupported consonant type: {consonant_type}")

    @staticmethod
    def compatible(cons1: Consonant, cons2: Consonant) -> bool:
        """Determine compatibility between two consonants."""
        allow_double = {ConsonantType.SIMILAR_DOTS, ConsonantType.DIFFERENT_DOTS, ConsonantType.BLACK_DOT,
                        ConsonantType.OBTUSE_ANGLE, ConsonantType.CIRCLE}
        if cons1.consonant_type == cons2.consonant_type and cons1.consonant_type in allow_double:
            return True

        large_angles = {ConsonantType.STRAIGHT_ANGLE, ConsonantType.REFLEX_ANGLE}
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
    """Base class for line-based consonants."""
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
        """Helper to calculate an endpoint for a given angle."""
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
        self._update_image_properties()

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)

        self._line_width = min(self.line_widths)
        self._half_line_width = self._line_width / 2
        self._distance = syllable.outer_radius

    def _update_image_properties(self):
        """Update the line arguments for drawing."""
        self._calculate_endpoints()
        self._line_args = [
            {'xy': (self.IMAGE_CENTER, self.IMAGE_CENTER + end),
             'fill': self.COLOR, 'width': self._line_width}
            for end in self._ends]

    def draw(self):
        """Draw the consonant."""
        for line_arg in self._line_args:
            self._image.line(**line_arg)


class BentLineConsonant(LineBasedConsonant):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.BENT_LINE)


class RadialLineConsonant(LineBasedConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.RADIAL_LINE)

        self._end = Point()
        self._polygon_args = {}

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
        self._update_image_properties()

    def _update_image_properties(self):
        """Update line and polygon arguments for drawing."""
        self._end = self._calculate_endpoint(self.direction)
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER, self.IMAGE_CENTER + self._end),
                'fill': self.COLOR, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction + math.pi / 2) * self._half_line_distance,
                      math.sin(self.direction + math.pi / 2) * self._half_line_distance)

            start1, end1 = self.IMAGE_CENTER - d, self.IMAGE_CENTER + self._end - d
            start2, end2 = self.IMAGE_CENTER + d, self.IMAGE_CENTER + self._end + d

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': self.BACKGROUND, 'fill': self.BACKGROUND}
            self._line_args = [
                {'xy': (start1, end1), 'fill': self.COLOR, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': self.COLOR, 'width': self.line_widths[1]}]


class DiametralLineConsonant(LineBasedConsonant):
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.DIAMETRAL_LINE)

        self._set_personal_direction(0)
        self._polygon_args = {}

    def _update_image_properties(self):
        """Update line arguments for drawing."""
        self._calculate_endpoints()
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER + self._ends[0], self.IMAGE_CENTER + self._ends[1]),
                'fill': self.COLOR, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction) * self._half_line_distance,
                      math.sin(self.direction) * self._half_line_distance)

            start1, end1 = (self.IMAGE_CENTER + self._ends[0] - d, self.IMAGE_CENTER + self._ends[1] - d)
            start2, end2 = (self.IMAGE_CENTER + self._ends[0] + d, self.IMAGE_CENTER + self._ends[1] + d)

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': self.BACKGROUND, 'fill': self.BACKGROUND}
            self._line_args = [
                {'xy': (start1, end1), 'fill': self.COLOR, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': self.COLOR, 'width': self.line_widths[1]}]

    def draw(self):
        """Draw the consonant."""
        if self._polygon_args:
            self._image.polygon(**self._polygon_args)

        super().draw()


class AngleBasedConsonant(LineBasedConsonant, ABC):
    """Base class for angle-based consonants."""

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)

        self._radius = 0.0
        self._arc_args = {}

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        self._radius = syllable.inner_radius + syllable.border_offset[1] + 2 * self._half_line_distance

    def _update_image_properties(self):
        """Update arc arguments for drawing."""
        super()._update_image_properties()
        adjusted_radius = self._radius + self._half_line_width
        start = self.IMAGE_CENTER.shift(-adjusted_radius)
        end = self.IMAGE_CENTER.shift(adjusted_radius)
        start_angle = math.degrees(self.direction - self.ANGLE)
        end_angle = math.degrees(self.direction + self.ANGLE)

        self._arc_args = {
            'xy': (start, end),
            'start': start_angle, 'end': end_angle,
            'fill': self.COLOR, 'width': self._line_width
        }

    def draw(self):
        """Draw a consonant with an arc."""
        super().draw()
        if self._arc_args:
            self._image.arc(**self._arc_args)


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
    COLOR = DOT_COLOR

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        super().__init__(text, borders, consonant_type)

        self._radius = 0.0
        self._line_width = 0.0

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        outer_radius, inner_radius, border_offset = syllable.outer_radius, syllable.inner_radius, syllable.border_offset

        self._line_width = line_width('1', syllable.scale)
        self._distance = max((outer_radius - border_offset[0] + inner_radius + border_offset[1]) / 2, MIN_RADIUS)
        self._radius = max(syllable.scale * DEFAULT_DOT_RADIUS, MIN_RADIUS)

    def _get_bounds(self, center: Point) -> dict:
        """Calculate bounding box for an ellipse."""

        start = (self.IMAGE_CENTER + center).shift(-self._radius)
        end = (self.IMAGE_CENTER + center).shift(self._radius)
        return {'xy': (start, end)}


class DualDotConsonant(DotConsonant):
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
        self._update_image_properties()

    @abstractmethod
    def _update_image_properties(self):
        self._centers = (
            Point(math.cos(self.direction - self.ANGLE) * self._distance,
                  math.sin(self.direction - self.ANGLE) * self._distance),
            Point(math.cos(self.direction + self.ANGLE) * self._distance,
                  math.sin(self.direction + self.ANGLE) * self._distance))

    def draw(self):
        for args in self._ellipse_args:
            self._image.ellipse(**args)


class SimilarDotConsonant(DualDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.SIMILAR_DOTS)

    def _update_image_properties(self):
        super()._update_image_properties()
        self._ellipse_args = [
            {**self._get_bounds(center), 'outline': self.COLOR, 'fill': self.BACKGROUND, 'width': self._line_width}
            for center in self._centers]


class DifferentDotConsonant(DualDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.DIFFERENT_DOTS)

    def _update_image_properties(self):
        super()._update_image_properties()
        self._ellipse_args = [
            {**self._get_bounds(self._centers[0]), 'fill': self.COLOR},
            {**self._get_bounds(self._centers[1]),
             'outline': self.COLOR, 'fill': self.BACKGROUND, 'width': self._line_width}]


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
        self._update_image_properties()

    def _calculate_center(self):
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

    def draw(self):
        self._image.ellipse(**self._ellipse_args)


class WhiteDotConsonant(SingleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.WHITE_DOT)

    def _update_image_properties(self):
        self._calculate_center()
        self._ellipse_args = {
            **self._get_bounds(self._center),
            'outline': self.COLOR, 'fill': self.BACKGROUND, 'width': self._line_width}


class BlackDotConsonant(SingleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.BLACK_DOT)

    def _update_image_properties(self):
        self._calculate_center()
        self._ellipse_args = {**self._get_bounds(self._center), 'fill': self.COLOR}


class CircleConsonant(Consonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantType.CIRCLE)

        self._width = 0.0
        self._half_width = 0.0
        self._radius = 0.0
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
        self._update_image_properties()

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        border_offset = syllable.border_offset

        self._width = min(self.line_widths)
        self._half_width = self._width / 2
        self._radius = max((outer_radius - border_offset[0] - inner_radius - border_offset[1]) / 4, MIN_RADIUS)
        self._distance = inner_radius + border_offset[1] + self._radius

    def _update_image_properties(self):
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

        adjusted_radius = self._radius + self._half_width
        start = (self.IMAGE_CENTER + self._center).shift(-adjusted_radius)
        end = (self.IMAGE_CENTER + self._center).shift(adjusted_radius)
        self._ellipse_args = {'xy': (start, end), 'outline': self.COLOR, 'fill': self.BACKGROUND, 'width': self._width}

    def draw(self):
        self._image.ellipse(**self._ellipse_args)
