import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import auto, IntFlag
from itertools import repeat
from typing import Optional

from PIL import ImageDraw, Image

from ..common import DistanceInfo, Interactive
from ..common.circles import OuterCircle, InnerCircle
from ...tools import AnimationProperties
from ...utils import Point, get_line_width, get_half_line_distance, PressedType, create_empty_image
from ....config import (DEFAULT_WORD_RADIUS, WORD_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG,
                        MARK_INITIAL_SCALE_MIN, MARK_INITIAL_SCALE_MAX, MARK_SCALE_MIN, MARK_SCALE_MAX,
                        INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX,
                        INNER_CIRCLE_SCALE_MIN, INNER_CIRCLE_SCALE_MAX)


class CharacterType(IntFlag):
    """Enumeration to represent types of characters."""
    _CONSONANT = auto()
    _VOWEL = auto()
    _SEPARATOR = auto()
    _DIGIT = auto()
    _NUMBER_MARK = auto()

    WORD = auto()
    NUMBER = auto()
    SPACE = auto()

    CONSONANT = WORD | _CONSONANT
    VOWEL = WORD | _VOWEL
    SEPARATOR = WORD | _SEPARATOR

    DIGIT = NUMBER | _DIGIT
    NUMBER_MARK = NUMBER | _NUMBER_MARK
    # PUNCTUATION_MARK = auto()
    # MULTIPURPOSE_MARK = NUMBER_MARK | PUNCTUATION_MARK


@dataclass
class CharacterInfo:
    character_type: CharacterType
    properties: list[str]


class Character(ABC):
    """Abstract base class representing a character."""

    def __init__(self, text: str, character_type: CharacterType):
        """Initialize a Character instance."""
        self.text = text
        self.character_type = character_type


class Space(Character):
    """Class representing a space character."""

    def __init__(self, text: str):
        """Initialize a Separator instance."""
        super().__init__(text, CharacterType.SPACE)


class Separator(Character):
    """Class representing a syllable separator character."""

    def __init__(self, text: str):
        """Initialize a Separator instance."""
        super().__init__(text, CharacterType.SEPARATOR)


class InteractiveCharacter(Character, Interactive, ABC):
    """Abstract base class representing an interactive character."""

    def __init__(self, text: str, character_type: CharacterType):
        """Initialize an InteractiveCharacter instance."""
        Character.__init__(self, text, character_type)
        Interactive.__init__(self)


class Letter(InteractiveCharacter, ABC):
    """Abstract base class representing a generic letter."""
    IMAGE_CENTER = Point(SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS)

    def __init__(self, text: str, character_type: CharacterType, borders: str):
        """Initialize a Letter instance."""
        super().__init__(text, character_type)
        self.borders = borders
        self.direction = 0.0
        self.parent_direction = 0.0
        self.personal_direction = 0.0
        self._set_personal_direction(random.uniform(0.9 * math.pi, 1.1 * math.pi))

        length = len(borders)
        self.line_widths = list(repeat(0, length))
        self.half_line_widths = list(repeat(0.0, length))
        self._half_line_distance = 0.0

    def initialize(self, direction: float, scale: float, outer_circle: OuterCircle, inner_circle: InnerCircle):
        """Initialize the letter's properties based on a given syllable."""
        self.update_direction(direction)
        self.resize(scale, outer_circle, inner_circle)

    def _update_properties_after_resizing(self, scale: float, outer_circle: OuterCircle, inner_circle: InnerCircle):
        """Update letter properties after resizing based on the given syllable."""
        self.line_widths = [get_line_width(border, scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]
        self._half_line_distance = get_half_line_distance(scale)

    def _update_properties_after_rotation(self):
        """Update letter properties after rotation."""

    @abstractmethod
    def update_argument_dictionaries(self):
        """Update the argument dictionaries used for rendering."""

    def update_direction(self, parent_direction: float):
        """Update the letter's direction based on the parent direction."""
        self.parent_direction = parent_direction
        self.direction = self.parent_direction + self.personal_direction
        self._update_properties_after_rotation()
        self.update_argument_dictionaries()

    def set_direction(self, direction: float):
        """Set a new direction for the letter."""
        self.direction = direction
        self.personal_direction = self.direction - self.parent_direction
        self._update_properties_after_rotation()
        self.update_argument_dictionaries()

    def _set_personal_direction(self, personal_direction: float):
        """Set a new personal direction for the letter."""
        self.personal_direction = personal_direction
        self.direction = self.parent_direction + self.personal_direction

    def resize(self, scale: float, outer_circle: OuterCircle, inner_circle: InnerCircle):
        """Resize the letter based on the given syllable."""
        self._update_properties_after_resizing(scale, outer_circle, inner_circle)
        self.update_argument_dictionaries()

    @abstractmethod
    def redraw(self, image: ImageDraw.ImageDraw):
        """Redraw the letter."""

    def perform_animation(self, direction_sign: int):
        delta = direction_sign * 2 * math.pi / AnimationProperties.cycle
        self.set_direction(self.direction + 2 * delta)


class NumberMark(InteractiveCharacter):
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    color = SYLLABLE_COLOR
    background = SYLLABLE_BG

    def __init__(self, text: str, borders: str):
        super().__init__(text, CharacterType.NUMBER_MARK)
        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(self.IMAGE_CENTER, distance_info)
        self.inner_circle = InnerCircle(self.IMAGE_CENTER, distance_info)
        self.outer_circle.initialize(borders)
        self.inner_circle.initialize(borders)
        self._image, self._draw = create_empty_image(self.IMAGE_CENTER)

        # Scale, radius, and positioning attributes
        self._scale = 1.0
        self._parent_scale = 1.0
        self._dependent = False
        self._personal_scale = random.uniform(MARK_INITIAL_SCALE_MIN, MARK_INITIAL_SCALE_MAX)
        self._inner_scale = random.uniform(INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX)
        self._update_after_resizing()

        self._direction = 0
        self._set_direction(random.uniform(-math.pi, math.pi))

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle press events at a given point."""
        distance = point.distance()
        if self.outer_circle.outside_circle(distance):
            return None

        return (self._handle_outer_border_press(distance) or
                self._handle_inner_space_press(point) or
                self._handle_inner_border_press(point) or
                self._handle_parent_press(point))

    def _handle_outer_border_press(self, distance: float) -> Optional[PressedType]:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self._pressed_type = PressedType.OUTER_CIRCLE
            self._distance_bias = distance - self.outer_circle.radius
            return self._pressed_type
        return None

    def _handle_inner_space_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events inside the inner circle."""
        if self.inner_circle.inside_circle(point.distance()):
            return self._handle_parent_press(point)
        return None

    def _handle_inner_border_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events on the inner border."""
        distance = point.distance()
        if self.inner_circle.on_circle(distance):
            self._pressed_type = PressedType.INNER_CIRCLE
            self._distance_bias = distance - self.inner_circle.radius
            return self._pressed_type
        return None

    def _handle_parent_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events for the parent."""
        self._pressed_type = PressedType.SELF
        self._point_bias = point
        return self._pressed_type

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point, radius=0.0) -> None:
        """Move the mark based on the provided point and number group's radius."""
        if self._dependent:
            shifted = point - self.calculate_position(radius)
            distance = shifted.distance()
        else:
            distance = point.distance()
        match self._pressed_type:
            case PressedType.INNER_CIRCLE:
                self._adjust_inner_scale(distance)
            case PressedType.OUTER_CIRCLE:
                self._adjust_personal_scale(distance)
            case PressedType.SELF:
                self._adjust_direction(point)

    def calculate_position(self, radius: float) -> Point:
        return Point(math.cos(self._direction) * radius, math.sin(self._direction) * radius)

    # =============================================
    # Resizing
    # =============================================
    def set_dependent(self, dependent: bool) -> None:
        if self._dependent != dependent:
            self._dependent = dependent
            self._update_after_resizing()

    def update_scale(self, parent_scale=1.0) -> None:
        """Update the scale based on the parent scale."""
        self._parent_scale = parent_scale
        self._update_after_resizing()

    def _set_personal_scale(self, scale: float) -> None:
        """Set the personal scale of the object and update properties accordingly."""
        self._personal_scale = scale
        self._update_after_resizing()

    def _adjust_personal_scale(self, distance: float) -> None:
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        if self._dependent:
            scale = new_radius / DEFAULT_WORD_RADIUS / self._parent_scale
        else:
            scale = new_radius / DEFAULT_WORD_RADIUS
        self._set_personal_scale(min(max(scale, MARK_SCALE_MIN), MARK_SCALE_MAX))

    def _adjust_inner_scale(self, distance: float) -> None:
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        scale = new_radius / self.outer_circle.radius
        self._inner_scale = min(max(scale, INNER_CIRCLE_SCALE_MIN), INNER_CIRCLE_SCALE_MAX)
        self._update_after_changing_inner_circle()

    def _update_after_resizing(self):
        """Update properties after resizing."""
        if self._dependent:
            self._scale = self._parent_scale * self._personal_scale
        else:
            self._scale = self._personal_scale
        self.distance_info.scale_distance(self._scale)
        self.outer_circle.scale_borders(self._scale)
        self.outer_circle.set_radius(self._scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)
        self._update_after_changing_inner_circle()

    def _update_after_changing_inner_circle(self):
        """Update properties after changing inner circle."""
        self.inner_circle.scale_borders(self._scale)
        self.inner_circle.set_radius(self._scale * self._inner_scale * DEFAULT_WORD_RADIUS)
        self.inner_circle.create_circle(self.color, self.background)
        self._redraw()

    # =============================================
    # Rotation
    # =============================================
    def _set_direction(self, direction: float):
        """Set the direction of the number mark."""
        self._direction = direction

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the number mark."""
        adjusted_point = point - self._point_bias
        self._set_direction(adjusted_point.direction())

    # =============================================
    # Drawing
    # =============================================
    def paste_image(self, image: Image.Image, xy: tuple[int, int]):
        image.paste(self._image, xy, self._image)

    def _redraw(self):
        """Draw the mark."""
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)
        self.outer_circle.paste_circle(self._image)
        self.inner_circle.redraw_circle(self._draw)

    def apply_color_changes(self):
        self.outer_circle.create_circle(self.color, self.background)
        self.inner_circle.create_circle(self.color, self.background)
        self._redraw()

    def perform_animation(self, direction_sign: int):
        delta = direction_sign * 2 * math.pi / AnimationProperties.cycle
        self._set_direction(self._direction + delta)
