from __future__ import annotations

import math
import random
from abc import ABC
from collections import Counter
from enum import Enum

from PIL import ImageDraw

from .characters import Letter, CharacterType
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
    DIAMETRICAL_LINE = ('dl', 1)
    CIRCULAR = ('cr', 3)
    MATCHING_DOTS = ('md', 4)
    DIFFERENT_DOTS = ('dd', 4)
    HOLLOW_DOT = ('hd', 4)
    SOLID_DOT = ('sd', 4)

    def __init__(self, code: str, group: int):
        """Initialize a consonant type with the specified code and group."""
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
        super().__init__(text, CharacterType.CONSONANT, borders)
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
            ConsonantType.DIAMETRICAL_LINE: DiametricalLineConsonant,
            ConsonantType.CIRCULAR: CircularConsonant,
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
        allow_double = {ConsonantType.OBTUSE_ANGLE, ConsonantType.CIRCULAR}
        if cons1.consonant_type == cons2.consonant_type and cons1.consonant_type in allow_double:
            return True

        large_angles = {
            ConsonantType.STRAIGHT_ANGLE, ConsonantType.REFLEX_ANGLE, ConsonantType.DIAMETRICAL_LINE}
        if cons1.consonant_type in large_angles and cons2.consonant_type in large_angles:
            return False

        full_data = {ConsonantType.RADIAL_LINE}
        unknown_order = {ConsonantType.DIAMETRICAL_LINE}
        min_border = {
            ConsonantType.BENT_LINE, ConsonantType.STRAIGHT_ANGLE,
            ConsonantType.OBTUSE_ANGLE, ConsonantType.REFLEX_ANGLE,
            ConsonantType.CIRCULAR}

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
        return 0 < rotated.x < self._distance and -self._half_line_distance < rotated.y < self._half_line_distance

    def move(self, point: Point):
        """Move the line based on interaction."""
        point -= self._bias
        self.set_direction(point.direction() + (-self.ANGLE if self._pressed_id else self.ANGLE))

    def _update_properties_after_resizing(self, syllable):
        """Update properties after resizing the syllable."""
        super()._update_properties_after_resizing(syllable)

        self._line_width = min(self.line_widths)
        self._half_line_width = self._line_width / 2
        self._distance = syllable.outer_radius
        self._calculate_endpoints()

    def _update_properties_after_rotation(self):
        """Update properties after rotation."""
        super()._update_properties_after_rotation()
        self._calculate_endpoints()

    def update_argument_dictionaries(self):
        """Update dictionary arguments used for drawing lines."""
        self._line_args = [
            {'xy': (self.IMAGE_CENTER.tuple(), (self.IMAGE_CENTER + end).tuple()),
             'fill': self.color, 'width': self._line_width}
            for end in self._ends]

    def redraw(self, image: ImageDraw.ImageDraw):
        """Draw the consonant as a line."""
        for line_arg in self._line_args:
            image.line(**line_arg)


class BentLineConsonant(LineBasedConsonant):
    """Consonant represented by a bent line."""
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        """Initialize a bent line consonant."""
        super().__init__(text, borders, ConsonantType.BENT_LINE)


class RadialLineConsonant(LineBasedConsonant):
    """Consonant represented by a radial line extending from a center point."""

    def __init__(self, text: str, borders: str):
        """Initialize a radial line consonant."""
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
        """Update properties after resizing the syllable."""
        super()._update_properties_after_resizing(syllable)
        self._end = self._calculate_endpoint(self.direction)

    def _update_properties_after_rotation(self):
        """Update properties after rotation."""
        super()._update_properties_after_rotation()
        self._end = self._calculate_endpoint(self.direction)

    def update_argument_dictionaries(self):
        """Update dictionary arguments used for drawing the radial line."""
        if len(self.borders) == 1:
            self._polygon_args = {}
            self._line_args = [{
                'xy': (self.IMAGE_CENTER.tuple(), (self.IMAGE_CENTER + self._end).tuple()),
                'fill': self.color, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction + math.pi / 2) * self._half_line_distance,
                      math.sin(self.direction + math.pi / 2) * self._half_line_distance)

            start1 = (self.IMAGE_CENTER - d).tuple()
            end1 = (self.IMAGE_CENTER + self._end - d).tuple()
            start2 = (self.IMAGE_CENTER + d).tuple()
            end2 = (self.IMAGE_CENTER + self._end + d).tuple()

            self._polygon_args = {
                'xy': (start1, end1, end2, start2),
                'outline': self.background, 'fill': self.background}
            self._line_args = [
                {'xy': (start1, end1), 'fill': self.color, 'width': self.line_widths[0]},
                {'xy': (start2, end2), 'fill': self.color, 'width': self.line_widths[1]}]


class DiametricalLineConsonant(LineBasedConsonant):
    """Represents a diametrical line consonant."""
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        """Initialize a DiametricalLineConsonant with text and borders."""
        super().__init__(text, borders, ConsonantType.DIAMETRICAL_LINE)

        self._set_personal_direction(0)
        self._polygon_args = {}

    def _update_properties_after_resizing(self, syllable):
        """Update consonant properties after resizing."""
        super()._update_properties_after_resizing(syllable)
        self._calculate_endpoints()

    def _update_properties_after_rotation(self):
        """Update consonant properties after rotation."""
        super()._update_properties_after_rotation()
        self._calculate_endpoints()

    def update_argument_dictionaries(self):
        """Update drawing arguments for lines and polygons."""
        if len(self.borders) == 1:
            self._polygon_args = {}

            start = (self.IMAGE_CENTER + self._ends[0]).tuple()
            end = (self.IMAGE_CENTER + self._ends[1]).tuple()
            self._line_args = [{'xy': (start, end), 'fill': self.color, 'width': self.line_widths[0]}]
        else:
            d = Point(math.cos(self.direction) * self._half_line_distance,
                      math.sin(self.direction) * self._half_line_distance)

            start1 = (self.IMAGE_CENTER + self._ends[0] - d).tuple()
            end1 = (self.IMAGE_CENTER + self._ends[1] - d).tuple()
            start2 = (self.IMAGE_CENTER + self._ends[0] + d).tuple()
            end2 = (self.IMAGE_CENTER + self._ends[1] + d).tuple()

            self._polygon_args = {'xy': (start1, end1, end2, start2),
                                  'outline': self.background, 'fill': self.background}
            self._line_args = [{'xy': (start1, end1), 'fill': self.color, 'width': self.line_widths[0]},
                               {'xy': (start2, end2), 'fill': self.color, 'width': self.line_widths[1]}]

    def redraw(self, image: ImageDraw.ImageDraw):
        """Draw the consonant."""
        if self._polygon_args:
            image.polygon(**self._polygon_args)

        super().redraw(image)


class AngleBasedConsonant(LineBasedConsonant, ABC):
    """Base class for angle-based consonants."""

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        """Initialize an AngleBasedConsonant."""
        super().__init__(text, borders, consonant_type)

        self._radius = 0.0
        self._arc_args = {}

    def _update_properties_after_resizing(self, syllable):
        """Update consonant properties after resizing."""
        super()._update_properties_after_resizing(syllable)
        self._radius = syllable.inner_radius + syllable.border_offset[
            1] + 2 * self._half_line_distance

    def update_argument_dictionaries(self):
        """Update the argument dictionary for arc drawing."""
        super().update_argument_dictionaries()
        adjusted_radius = self._radius + self._half_line_width
        start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
        end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
        start_angle = math.degrees(self.direction - self.ANGLE)
        end_angle = math.degrees(self.direction + self.ANGLE)

        self._arc_args = {'xy': (start, end),'start': start_angle, 'end': end_angle,
                          'fill': self.color, 'width': self._line_width}

    def redraw(self, image: ImageDraw.ImageDraw):
        """Draw a consonant with an arc."""
        super().redraw(image)

        if self._arc_args:
            image.arc(**self._arc_args)


class StraightAngleConsonant(AngleBasedConsonant):
    """Represents a consonant with a straight-angle arc."""
    ANGLE = 0.5 * math.pi

    def __init__(self, text: str, borders: str):
        """Initialize a StraightAngleConsonant."""
        super().__init__(text, borders, ConsonantType.STRAIGHT_ANGLE)
        self._set_personal_direction(0)


class ObtuseAngleConsonant(AngleBasedConsonant):
    """Represents a consonant with an obtuse-angle arc."""
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str):
        """Initialize an ObtuseAngleConsonant."""
        super().__init__(text, borders, ConsonantType.OBTUSE_ANGLE)


class ReflexAngleConsonant(AngleBasedConsonant):
    """Represents a consonant with a reflex-angle arc."""
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        """Initialize a ReflexAngleConsonant."""
        super().__init__(text, borders, ConsonantType.REFLEX_ANGLE)
        self._set_personal_direction(0)


class DotConsonant(Consonant, ABC):
    """Base class for dot-based consonants."""
    color = DOT_COLOR

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        """Initialize a DotConsonant."""
        super().__init__(text, borders, consonant_type)
        self._radius = 0.0
        self._line_width = 0.0

    def _update_properties_after_resizing(self, syllable):
        """Update consonant properties after resizing."""
        super()._update_properties_after_resizing(syllable)
        outer_radius, inner_radius, border_offset = \
            syllable.outer_radius, syllable.inner_radius, syllable.border_offset

        self._line_width = line_width('1', syllable.scale)
        self._distance = max(
            (outer_radius - border_offset[0] + inner_radius + border_offset[1]) / 2, MIN_RADIUS)
        self._radius = max(syllable.scale * DEFAULT_DOT_RADIUS, MIN_RADIUS)

    def _get_bounds(self, center: Point) -> tuple[tuple[int, int], tuple[int, int]]:
        """Calculate bounding box for an ellipse."""
        start = (self.IMAGE_CENTER + center).shift(-self._radius).tuple()
        end = (self.IMAGE_CENTER + center).shift(self._radius).tuple()
        return start, end


class DoubleDotConsonant(DotConsonant, ABC):
    """Represents a consonant with two dots."""
    ANGLE = 0.3 * math.pi

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        """Initialize a DoubleDotConsonant with given text, borders, and consonant type."""
        super().__init__(text, borders, consonant_type)
        self._centers = Point(), Point()
        self._pressed_id = 0
        self._ellipse_args: list[dict] = []

    def press(self, point: Point) -> bool:
        """
        Check if the given point is within the radius of any dot.
        Return True if a dot is pressed, otherwise False.
        """
        for i, center in enumerate(self._centers):
            delta = point - center
            if delta.distance() < self._radius:
                self._bias = delta
                self._pressed_id = i
                return True
        return False

    def move(self, point: Point):
        """Move the consonant based on the given point, updating its direction."""
        point -= self._bias
        direction = point.direction()
        if self._pressed_id:
            self.set_direction(direction - self.ANGLE)
        else:
            self.set_direction(direction + self.ANGLE)

    def _update_properties_after_resizing(self, syllable):
        """Update consonant properties after resizing the syllable."""
        super()._update_properties_after_resizing(syllable)
        self._calculate_centers()

    def _update_properties_after_rotation(self):
        """Update consonant properties after rotation."""
        super()._update_properties_after_rotation()
        self._calculate_centers()

    def _calculate_centers(self):
        """Calculate the positions of the two dot centers based on the current direction."""
        self._centers = (
            Point(math.cos(self.direction - self.ANGLE) * self._distance,
                  math.sin(self.direction - self.ANGLE) * self._distance),
            Point(math.cos(self.direction + self.ANGLE) * self._distance,
                  math.sin(self.direction + self.ANGLE) * self._distance))

    def redraw(self, image: ImageDraw.ImageDraw):
        """Draw the two dots representing the consonant on the given image."""
        for args in self._ellipse_args:
            image.ellipse(**args)


class MatchingDotsConsonant(DoubleDotConsonant):
    """Represents a consonant with two matching dots."""

    def __init__(self, text: str, borders: str):
        """Initialize a MatchingDotsConsonant with given text and borders."""
        super().__init__(text, borders, ConsonantType.MATCHING_DOTS)

    def update_argument_dictionaries(self):
        """Update the argument dictionaries used for drawing the dots."""
        self._ellipse_args = [{'xy': self._get_bounds(center), 'outline': self.color,
                               'fill': self.background, 'width': self._line_width}
                              for center in self._centers]


class DifferentDotsConsonant(DoubleDotConsonant):
    """Represents a consonant with two different dots."""

    def __init__(self, text: str, borders: str):
        """Initializes a DifferentDotsConsonant with given text and borders."""
        super().__init__(text, borders, ConsonantType.DIFFERENT_DOTS)

    def update_argument_dictionaries(self):
        """Updates the argument dictionaries used for drawing the different dots."""
        self._ellipse_args = [
            {'xy': self._get_bounds(self._centers[0]), 'fill': self.color},
            {'xy': self._get_bounds(self._centers[1]), 'outline': self.color,
             'fill': self.background, 'width': self._line_width}]


class SingleDotConsonant(DotConsonant, ABC):
    """Represents a consonant with one dot."""

    def __init__(self, text: str, borders: str, consonant_type: ConsonantType):
        """Initialize a single-dot consonant with text, borders, and type."""
        super().__init__(text, borders, consonant_type)
        self._center = Point()
        self._ellipse_args = {}

    def press(self, point: Point) -> bool:
        """Handle pressing interaction by checking if the point is within the dot's radius."""
        delta = point - self._center
        if delta.distance() < self._radius:
            self._bias = delta
            return True
        return False

    def move(self, point: Point):
        """Update the direction of the consonant when moved."""
        point -= self._bias
        self.set_direction(point.direction())

    def _update_properties_after_resizing(self, syllable):
        """Update the properties of the consonant after resizing."""
        super()._update_properties_after_resizing(syllable)
        self._calculate_center()

    def _update_properties_after_rotation(self):
        """Update the properties of the consonant after rotation."""
        super()._update_properties_after_rotation()
        self._calculate_center()

    def _calculate_center(self):
        """Calculate the center position of the dot based on its direction and distance."""
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

    def redraw(self, image: ImageDraw.ImageDraw):
        """Redraw the consonant on the given image."""
        if self._ellipse_args:
            image.ellipse(**self._ellipse_args)


class HollowDotConsonant(SingleDotConsonant):
    """Represents a hollow dot consonant."""

    def __init__(self, text: str, borders: str):
        """Initialize a hollow dot consonant."""
        super().__init__(text, borders, ConsonantType.HOLLOW_DOT)

    def update_argument_dictionaries(self):
        """Update the drawing arguments for rendering the hollow dot."""
        self._ellipse_args = {'xy': self._get_bounds(self._center), 'outline': self.color,
                              'fill': self.background, 'width': self._line_width}


class SolidDotConsonant(SingleDotConsonant):
    """Represents a solid dot consonant."""

    def __init__(self, text: str, borders: str):
        """Initialize a solid dot consonant."""
        super().__init__(text, borders, ConsonantType.SOLID_DOT)

    def update_argument_dictionaries(self):
        """Update the drawing arguments for rendering the solid dot."""
        self._ellipse_args = {'xy': self._get_bounds(self._center), 'fill': self.color}


class CircularConsonant(Consonant):
    """Represents a circle consonant."""

    def __init__(self, text: str, borders: str):
        """Initialize a circular consonant."""
        super().__init__(text, borders, ConsonantType.CIRCULAR)

        self._line_width = 0.0
        self._half_line_width = 0.0
        self._radius = 0.0
        self._center = Point()
        self._ellipse_args = {}
        self._set_personal_direction(random.uniform(0.7 * math.pi, 1.3 * math.pi))

    def press(self, point: Point) -> bool:
        """Handle pressing interaction by checking if the point is within the circle's radius."""
        delta = point - self._center
        if delta.distance() < self._radius:
            self._bias = delta
            return True
        return False

    def move(self, point: Point):
        """Update the direction of the consonant when moved."""
        point -= self._bias
        self.set_direction(point.direction())

    def _update_properties_after_resizing(self, syllable):
        """Update the properties of the consonant after resizing."""
        super()._update_properties_after_resizing(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        border_offset = syllable.border_offset
        inner_line_width = syllable.inner.line_widths[0]
        inner_half_line_width = syllable.inner.half_line_widths[0]

        self._line_width = min(self.line_widths)
        self._half_line_width = self._line_width / 2
        overlap = min(self._line_width, inner_line_width)
        distance_adjustment = inner_half_line_width + self._half_line_width - overlap
        distance_start = inner_radius + border_offset[1] + distance_adjustment

        self._radius = max((outer_radius - border_offset[0] - distance_start) / 4, MIN_RADIUS)
        self._distance = distance_start + self._radius
        self._calculate_center()

    def _update_properties_after_rotation(self):
        """Update the properties of the consonant after rotation."""
        super()._update_properties_after_rotation()
        self._calculate_center()

    def _calculate_center(self):
        """Calculate the center position of the circle based on its direction and distance."""
        self._center = Point(math.cos(self.direction) * self._distance,
                             math.sin(self.direction) * self._distance)

    def update_argument_dictionaries(self):
        """Update the drawing arguments for rendering the circle."""
        adjusted_radius = self._radius + self._half_line_width
        start = (self.IMAGE_CENTER + self._center).shift(-adjusted_radius).tuple()
        end = (self.IMAGE_CENTER + self._center).shift(adjusted_radius).tuple()
        self._ellipse_args = {'xy': (start, end), 'outline': self.color, 'fill': self.background,
                              'width': self._line_width}

    def redraw(self, image: ImageDraw.ImageDraw):
        """Draw the consonant as a circle on the given image."""
        if self._ellipse_args:
            image.ellipse(**self._ellipse_args)
