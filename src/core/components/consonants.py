from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections import Counter
from enum import Enum
from typing import List, Dict

from src.utils import Point, SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG, DOT_RADIUS, MIN_RADIUS
from .letters import Letter, LetterType


class ConsonantDecoration(Enum):
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
        """Retrieve a ConsonantDecoration by its code."""
        for decoration in cls:
            if decoration.code == code:
                return decoration
        raise ValueError(f"Invalid decoration code: {code}")


class Consonant(Letter, ABC):
    IMAGE_CENTER = Point(SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS)

    def __init__(self, text: str, borders: str, decoration_type: ConsonantDecoration):
        super().__init__(text, LetterType.CONSONANT, borders)
        self.decoration_type = decoration_type
        self._distance = 0.0
        self._bias = Point()

    @staticmethod
    def get_consonant(text: str, border: str, decoration_code: str) -> Consonant:
        """Factory method to create an appropriate Consonant subclass."""
        decoration_type = ConsonantDecoration.get_by_code(decoration_code)
        consonant_classes = {
            ConsonantDecoration.STRAIGHT_ANGLE: StraightAngleConsonant,
            ConsonantDecoration.OBTUSE_ANGLE: ObtuseAngleConsonant,
            ConsonantDecoration.REFLEX_ANGLE: ReflexAngleConsonant,
            ConsonantDecoration.BENT_LINE: BentLineConsonant,
            ConsonantDecoration.RADIAL_LINE: RadialLineConsonant,
            ConsonantDecoration.DIAMETRAL_LINE: DiametralLineConsonant,
            ConsonantDecoration.CIRCLE: CircleConsonant,
            ConsonantDecoration.SIMILAR_DOTS: SimilarDotConsonant,
            ConsonantDecoration.DIFFERENT_DOTS: DifferentDotConsonant,
            ConsonantDecoration.WHITE_DOT: WhiteDotConsonant,
            ConsonantDecoration.BLACK_DOT: BlackDotConsonant}
        if decoration_type in consonant_classes:
            return consonant_classes[decoration_type](text, border)
        raise ValueError(f"Unsupported decoration type: {decoration_type}")

    @staticmethod
    def compatible(cons1: Consonant, cons2: Consonant) -> bool:
        """Determine compatibility between two consonants."""
        full_data = {ConsonantDecoration.RADIAL_LINE}
        unknown_order = {ConsonantDecoration.DIAMETRAL_LINE}
        min_border = {
            ConsonantDecoration.BENT_LINE, ConsonantDecoration.STRAIGHT_ANGLE,
            ConsonantDecoration.OBTUSE_ANGLE, ConsonantDecoration.REFLEX_ANGLE,
            ConsonantDecoration.CIRCLE}

        if cons1.decoration_type in full_data or cons2.decoration_type in full_data:
            return cons1.borders != cons2.borders
        if cons1.decoration_type in unknown_order or cons2.decoration_type in unknown_order:
            return Counter(cons1.borders) != Counter(cons2.borders)
        if cons1.decoration_type in min_border or cons2.decoration_type in min_border:
            return min(cons1.borders) != min(cons2.borders)
        return False


class LineBasedConsonant(Consonant, ABC):
    """Base class for line-based consonants."""
    ANGLE = 0.0

    def __init__(self, text: str, borders: str, decoration_type: ConsonantDecoration):
        super().__init__(text, borders, decoration_type)

        self._ends = Point(), Point()
        self._pressed_id = 0
        self._width = 0.0
        self._half_width = 0.0
        self._line_args: List[Dict] = []

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
        self._set_direction(point.direction() + (-self.ANGLE if self._pressed_id else self.ANGLE))
        self._update_image_properties()

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)

        self._width = min(self.line_widths)
        self._half_width = self._width / 2
        self._distance = syllable.outer_radius

    def _update_image_properties(self):
        """Update the line arguments for drawing."""
        self._calculate_endpoints()
        self._line_args = [
            {'xy': (self.IMAGE_CENTER, self.IMAGE_CENTER + end),
             'fill': SYLLABLE_COLOR, 'width': self._width}
            for end in self._ends]

    def draw_decoration(self):
        """Draw the decoration lines."""
        for line_arg in self._line_args:
            self._image.line(**line_arg)


class BentLineConsonant(LineBasedConsonant):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.BENT_LINE)


class RadialLineConsonant(LineBasedConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.RADIAL_LINE)

        self._end = Point
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
        self._set_direction(point.direction())
        self._update_image_properties()

    def _update_image_properties(self):
        """Update line and polygon arguments for drawing."""
        self._end = self._calculate_endpoint(self.direction)
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER, self.IMAGE_CENTER + self._end),
                'fill': SYLLABLE_COLOR, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction + math.pi / 2) * self._half_line_distance,
                      math.sin(self.direction + math.pi / 2) * self._half_line_distance)

            start1, end1 = self.IMAGE_CENTER - d, self.IMAGE_CENTER + self._end - d
            start2, end2 = self.IMAGE_CENTER + d, self.IMAGE_CENTER + self._end + d

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': SYLLABLE_BG, 'fill': SYLLABLE_BG}
            self._line_args = [
                {'xy': (start1, end1), 'fill': SYLLABLE_COLOR, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': SYLLABLE_COLOR, 'width': self.line_widths[1]}]


class DiametralLineConsonant(LineBasedConsonant):
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.DIAMETRAL_LINE)

        self._set_personal_direction(0)
        self._polygon_args = {}

    def _update_image_properties(self):
        """Update line arguments for drawing."""
        self._calculate_endpoints()
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER + self._ends[0], self.IMAGE_CENTER + self._ends[1]),
                'fill': SYLLABLE_COLOR, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction) * self._half_line_distance,
                      math.sin(self.direction) * self._half_line_distance)

            start1, end1 = (self.IMAGE_CENTER + self._ends[0] - d, self.IMAGE_CENTER + self._ends[1] - d)
            start2, end2 = (self.IMAGE_CENTER + self._ends[0] + d, self.IMAGE_CENTER + self._ends[1] + d)

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': SYLLABLE_BG, 'fill': SYLLABLE_BG}
            self._line_args = [
                {'xy': (start1, end1), 'fill': SYLLABLE_COLOR, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': SYLLABLE_COLOR, 'width': self.line_widths[1]}]

    def draw_decoration(self):
        """Draw the decoration lines."""
        if self._polygon_args:
            self._image.polygon(**self._polygon_args)

        super().draw_decoration()


class AngleBasedConsonant(LineBasedConsonant, ABC):
    """Base class for angle-based consonants."""

    def __init__(self, text: str, borders: str, decoration_type: ConsonantDecoration):
        super().__init__(text, borders, decoration_type)

        self._radius = 0.0
        self._arc_args = {}

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        self._radius = syllable.inner_radius + syllable.offset[1] + 2 * self._half_line_distance

    def _update_image_properties(self):
        """Update arc arguments for drawing."""
        super()._update_image_properties()
        adjusted_radius = self._radius + self._half_width
        start = self.IMAGE_CENTER.shift(-adjusted_radius, -adjusted_radius)
        end = self.IMAGE_CENTER.shift(adjusted_radius, adjusted_radius)
        start_angle = math.degrees(self.direction - self.ANGLE)
        end_angle = math.degrees(self.direction + self.ANGLE)

        self._arc_args = {
            'xy': (start, end),
            'start': start_angle, 'end': end_angle,
            'fill': SYLLABLE_COLOR, 'width': self._width
        }

    def draw_decoration(self):
        """Draw the arc decoration."""
        super().draw_decoration()
        if self._arc_args:
            self._image.arc(**self._arc_args)


class StraightAngleConsonant(AngleBasedConsonant):
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.STRAIGHT_ANGLE)

        self._set_personal_direction(0)


class ObtuseAngleConsonant(AngleBasedConsonant):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.OBTUSE_ANGLE)


class ReflexAngleConsonant(AngleBasedConsonant):
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.REFLEX_ANGLE)

        self._set_personal_direction(0)


class DotConsonant(Consonant, ABC):
    def __init__(self, text: str, borders: str, decoration: ConsonantDecoration):
        super().__init__(text, borders, decoration)

        self._width = 0.0
        self._radius = 0.0

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)
        outer_radius, inner_radius, offset = syllable.outer_radius, syllable.inner_radius, syllable.offset

        self._width = min(self.line_widths)
        self._distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)
        self._radius = syllable.scale * DOT_RADIUS

    def _get_bounds(self, center: Point) -> Dict:
        """Calculate bounding box for an ellipse."""

        start = (self.IMAGE_CENTER + center).shift(-self._radius, -self._radius)
        end = (self.IMAGE_CENTER + center).shift(self._radius, self._radius)
        return {'xy': (start, end)}


class DualDotConsonant(DotConsonant):
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str, decoration_type: ConsonantDecoration):
        super().__init__(text, borders, decoration_type)
        self._centers = Point(), Point()
        self._pressed_id = 0
        self._ellipse_args: List[Dict] = []

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
            self._set_direction(direction - self.ANGLE)
        else:
            self._set_direction(direction + self.ANGLE)
        self._update_image_properties()

    @abstractmethod
    def _update_image_properties(self):
        self._centers = (
            Point(math.cos(self.direction - self.ANGLE) * self._distance,
                  math.sin(self.direction - self.ANGLE) * self._distance),
            Point(math.cos(self.direction + self.ANGLE) * self._distance,
                  math.sin(self.direction + self.ANGLE) * self._distance))

    def draw_decoration(self):
        for args in self._ellipse_args:
            self._image.ellipse(**args)


class SimilarDotConsonant(DualDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.SIMILAR_DOTS)

    def _update_image_properties(self):
        super()._update_image_properties()
        self._ellipse_args = [
            {**self._get_bounds(center), 'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self._width}
            for center in self._centers]


class DifferentDotConsonant(DualDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.DIFFERENT_DOTS)

    def _update_image_properties(self):
        super()._update_image_properties()
        self._ellipse_args = [
            {**self._get_bounds(self._centers[0]), 'fill': SYLLABLE_COLOR},
            {**self._get_bounds(self._centers[1]),
             'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self._width}]


class SingleDotConsonant(DotConsonant, ABC):
    def __init__(self, text: str, borders: str, decoration_type: ConsonantDecoration):
        super().__init__(text, borders, decoration_type)

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
        self._set_direction(point.direction())
        self._update_image_properties()

    def _calculate_center(self):
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

    def draw_decoration(self):
        self._image.ellipse(**self._ellipse_args)


class WhiteDotConsonant(SingleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.WHITE_DOT)

    def _update_image_properties(self):
        self._calculate_center()
        self._ellipse_args = {
            **self._get_bounds(self._center),
            'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self._width}


class BlackDotConsonant(SingleDotConsonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.BLACK_DOT)

    def _update_image_properties(self):
        self._calculate_center()
        self._ellipse_args = {**self._get_bounds(self._center), 'fill': SYLLABLE_COLOR}


class CircleConsonant(Consonant):
    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.CIRCLE)

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
        self._set_direction(point.direction())
        self._update_image_properties()

    def _update_syllable_properties(self, syllable):
        super()._update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self._width = min(self.line_widths)
        self._half_width = self._width / 2
        self._radius = max((outer_radius - offset[0] - inner_radius - offset[1]) / 4, MIN_RADIUS)
        self._distance = inner_radius + offset[1] + self._radius

    def _update_image_properties(self):
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

        adjusted_radius = self._radius + self._half_width
        start = (self.IMAGE_CENTER + self._center).shift(-adjusted_radius, -adjusted_radius)
        end = (self.IMAGE_CENTER + self._center).shift(adjusted_radius, adjusted_radius)
        self._ellipse_args = {'xy': (start, end), 'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self._width}

    def draw_decoration(self):
        self._image.ellipse(**self._ellipse_args)
