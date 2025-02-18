import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import auto, IntFlag
from itertools import repeat
from typing import Optional

from PIL import ImageDraw, Image

from ..common import DistanceInfo
from ..common.circles import OuterCircle, InnerCircle
from ...tools import AnimationProperties
from ...utils import Point, get_line_width, get_half_line_distance, PressedType, create_empty_image
from ....config import (DEFAULT_WORD_RADIUS, WORD_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG,
                        SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX, SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX,
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


class Letter(Character, ABC):
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

    @abstractmethod
    def press(self, point: Point) -> bool:
        """Handle a press event at a given point."""

    @abstractmethod
    def move(self, point: Point):
        """Handle a move event to a given point."""

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


class NumberMark(Character):
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
        self.scale = 0.0
        self._parent_scale = 1.0
        self._personal_scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self._inner_scale = random.uniform(INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX)
        self._update_after_resizing()

        self.direction = 0
        self._set_direction(random.uniform(-math.pi, math.pi))

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> bool:
        """Handle press events at a given point."""
        distance = point.distance()
        if self.outer_circle.outside_circle(distance):
            return False

        return (self._handle_outer_border_press(distance) or
                self._handle_inner_space_press(point) or
                self._handle_inner_border_press(point) or
                self._handle_parent_press(point))

    def _handle_outer_border_press(self, distance: float) -> bool:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self.pressed_type = PressedType.BORDER
            self._distance_bias = distance - self.outer_circle.radius
            return True
        return False

    def _handle_inner_space_press(self, point: Point) -> bool:
        """Handle press events inside the inner circle."""
        if self.inner_circle.inside_circle(point.distance()):
            return self._handle_parent_press(point)
        return False

    def _handle_inner_border_press(self, point: Point) -> bool:
        """Handle press events on the inner border."""
        distance = point.distance()
        if self.inner_circle.on_circle(distance):
            self.pressed_type = PressedType.INNER
            self._distance_bias = distance - self.inner_circle.radius
            return True
        return False

    def _handle_parent_press(self, point: Point) -> bool:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = point
        return True

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point, radius=0.0) -> None:
        """Move the object based on the provided point and number's radius."""
        shifted = point - Point(math.cos(self.direction) * radius, math.sin(self.direction) * radius)
        distance = shifted.distance()

        match self.pressed_type:
            case PressedType.INNER:
                self._adjust_inner_scale(distance)
            case PressedType.BORDER:
                self._adjust_scale(distance)
            case PressedType.PARENT:
                if radius:
                    self._adjust_direction(point)

    # =============================================
    # Resizing
    # =============================================
    def set_scale(self, scale: float) -> None:
        """Set the personal scale of the object and update properties accordingly."""
        self._personal_scale = scale
        self._update_after_resizing()

    def update_scale(self, parent_scale=1.0) -> None:
        """Update the scale based on the parent scale."""
        self._parent_scale = parent_scale
        self._update_after_resizing()

    def _adjust_scale(self, distance: float) -> None:
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_scale(min(max(new_radius / DEFAULT_WORD_RADIUS / self._parent_scale,
                               SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def _adjust_inner_scale(self, distance: float) -> None:
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self._inner_scale = min(max(new_radius / self.outer_circle.radius, INNER_CIRCLE_SCALE_MIN), INNER_CIRCLE_SCALE_MAX)
        self._update_after_changing_inner_circle()

    def _update_after_resizing(self):
        """Update properties after resizing."""
        self.scale = self._parent_scale * self._personal_scale
        self.distance_info.scale_distance(self.scale)
        self.outer_circle.scale_borders(self.scale)
        self.outer_circle.set_radius(self.scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)
        self._update_after_changing_inner_circle()

    def _update_after_changing_inner_circle(self):
        """Update properties after changing inner circle."""
        self.inner_circle.scale_borders(self.scale)
        self.inner_circle.set_radius(self.scale * self._inner_scale * DEFAULT_WORD_RADIUS)
        self.inner_circle.create_circle(self.color, self.background)
        self._redraw()

    # =============================================
    # Rotation
    # =============================================
    def _set_direction(self, direction: float):
        """Set the direction of the number mark."""
        self.direction = direction

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the number mark."""
        adjusted_point = point - self._point_bias
        self._set_direction(adjusted_point.direction())

    # =============================================
    # Drawing
    # =============================================
    def get_image(self) -> Image.Image:
        return self._image

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
        self._set_direction(self.direction + delta)