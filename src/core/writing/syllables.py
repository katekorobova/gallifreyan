from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image

from .characters import Letter, Separator, Character
from .circles import HasOuterCircle
from .consonants import Consonant
from .vowels import Vowel, VowelType
from .. import repository
from ..tools import AnimationProperties
from ..utils import Point, PressedType, create_empty_image, ensure_min_radius
from ...config import (SYLLABLE_IMAGE_RADIUS, DEFAULT_WORD_RADIUS, SYLLABLE_INITIAL_SCALE_MIN,
                       SYLLABLE_INITIAL_SCALE_MAX,
                       SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX,
                       INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX,
                       INNER_CIRCLE_SCALE_MIN, INNER_CIRCLE_SCALE_MAX,
                       SYLLABLE_BG, SYLLABLE_COLOR, ALEPH)


class AbstractSyllable(ABC):
    """
    Abstract base class for representing syllables.
    Provides an interface for managing characters within a syllable.
    """

    def __init__(self):
        """Initialize the syllable."""
        self.text = ''

    @abstractmethod
    def remove_starting_with(self, character: Character) -> None:
        """Remove a character from the syllable, updating properties accordingly."""

    @abstractmethod
    def add(self, character: Character) -> bool:
        """Add a character to the syllable, if possible."""

    @abstractmethod
    def _update_text(self) -> None:
        pass



class SeparatorSyllable(AbstractSyllable):
    """Represents a syllable consisting of only separator characters."""

    def __init__(self, separator: Separator):
        """Initialize a separator syllable with a given separator character."""
        super().__init__()
        self.separators = [separator]
        self._update_text()

    def _update_text(self) -> None:
        self.text = ''.join(separator.text for separator in self.separators)

    def remove_starting_with(self, character: Character) -> None:
        """Remove a character from the syllable, updating properties accordingly."""
        if isinstance(character, Separator) and character in self.separators:
            index = self.separators.index(character)
            self.separators[index:] = []
            self._update_text()

    def add(self, character: Character) -> bool:
        """Add a character to the syllable, if possible."""
        if isinstance(character, Separator):
            self.separators.append(character)
            self._update_text()
            return True

        return False


class Syllable(AbstractSyllable, HasOuterCircle):
    """
    Represents a structured syllable, which may consist of consonants and vowels.
    Manages visual representation and interactive behavior.
    """

    IMAGE_CENTER = Point(SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS)
    background = SYLLABLE_BG
    color = SYLLABLE_COLOR

    def __init__(self, consonant: Consonant = None, vowel: Vowel = None):
        """Initialize a syllable with an optional consonant and vowel."""
        outer_consonant: Consonant = consonant or Consonant.get_consonant(ALEPH, *repository.get().all[ALEPH].properties)
        HasOuterCircle.__init__(self, outer_consonant.borders, self.IMAGE_CENTER)
        AbstractSyllable.__init__(self)

        # Image-related attributes
        self._image, self._draw = create_empty_image(self.IMAGE_CENTER)
        self._inner_circle_arg_dict: list[dict] = []
        self._image_ready = False

        # Core attributes
        self.first_consonant, self.vowel = consonant, vowel
        self.second_consonant: Optional[Consonant] = None
        self._following: Optional[Syllable] = None
        self.consonants: list[Consonant] = []

        self.outer_consonant = outer_consonant
        self.inner_consonant = outer_consonant
        self.consonants = [outer_consonant]
        self._update_text()

        # Scale, radius, and positioning attributes
        self.scale = 0.0
        self._parent_scale = 1.0
        self.inner_radius = 0.0
        self.border_offset = 0.0
        self._personal_scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self.inner_scale = random.uniform(INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX)
        self._update_properties_after_resizing()

        self.direction = 0
        self.set_direction(random.uniform(-math.pi, math.pi))

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Letter] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    # =============================================
    # Initialization
    # =============================================
    def set_following(self, following: Optional[Syllable]) -> None:
        """Set the following syllable."""
        self._following = following

    def _update_text(self) -> None:
        self.text = [item.text for item in [self.first_consonant, self.second_consonant, self.vowel] if item]

    def _update_key_properties(self) -> None:
        """Update syllable properties such as consonants, letters, and text representation."""
        self.inner_consonant = self.second_consonant or self.outer_consonant
        self.consonants = sorted({self.outer_consonant, self.inner_consonant}, key=lambda l: l.consonant_type.group)
        self._update_text()

    # =============================================
    # Insertion
    # =============================================
    def add(self, character: Character) -> bool:
        """Add a letter to the syllable, if possible."""
        if isinstance(character, Vowel) and not self.vowel:
            self.vowel = character
        elif isinstance(character, Consonant) and \
                not self.second_consonant and not self.vowel and \
                Consonant.compatible(self.first_consonant, character):
            self.second_consonant = character
        else:
            return False

        character.initialize(self)
        self._update_key_properties()
        self._image_ready = False
        return True

    # =============================================
    # Deletion
    # =============================================
    def remove_starting_with(self, character: Character):
        """Remove a letter from the syllable, updating properties accordingly."""
        if character == self.second_consonant:
            self.second_consonant, self.vowel = None, None
        elif character == self.vowel:
            self.vowel = None
        else:
            raise ValueError(f"Letter '{character.text}' not found in syllable '{self.text}'")
        self._update_key_properties()
        self._image_ready = False

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> bool:
        """Handle press events at a given point."""
        distance = point.distance()
        if self.beyond_border(distance):
            return False

        return (self._handle_outer_border_press(distance) or
                self._handle_visible_vowel_press(point) or
                self._handle_inner_space_press(point, distance) or
                self._handle_inner_border_press(distance) or
                self._handle_consonant_press(point) or
                self._handle_hidden_vowel_press(point) or
                self._handle_parent_press(point))

    def _handle_outer_border_press(self, distance: float) -> bool:
        """Handle press events on the outer border."""
        if self.on_border(distance):
            self.pressed_type = PressedType.BORDER
            self._distance_bias = distance - self.outer_radius
            return True
        return False

    def _handle_inner_space_press(self, point: Point, distance: float) -> bool:
        """Handle press events inside the inner circle."""
        if distance < self.inner_radius - self.half_line_distance:
            return self._handle_parent_press(point)
        return False

    def _handle_inner_border_press(self, distance: float) -> bool:
        """Handle press events on the inner border."""
        if distance < self.inner_radius + self.half_line_distance:
            self.pressed_type = PressedType.INNER
            self._distance_bias = distance - self.inner_radius
            return True
        return False

    def _handle_parent_press(self, point: Point) -> bool:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = point
        return True

    def _handle_visible_vowel_press(self, point: Point) -> bool:
        """Handle press events for visible vowels."""
        if self.vowel and self.vowel.vowel_type is not VowelType.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self._pressed = self.vowel
            return True
        return False

    def _handle_hidden_vowel_press(self, point: Point) -> bool:
        """Handle press events for hidden vowels."""
        if self.vowel and self.vowel.vowel_type is VowelType.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self._pressed = self.vowel
            return True
        return False

    def _handle_consonant_press(self, point: Point) -> bool:
        """Handle press events for consonants."""
        for cons in reversed(self.consonants):
            if cons.press(point):
                self.pressed_type = PressedType.CHILD
                self._pressed = cons
                return True
        return False

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point, radius=0.0):
        """Move the object based on the provided point and head syllable's radius."""
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
            case PressedType.CHILD:
                self._move_child(shifted)

    def _move_child(self, shifted: Point):
        """Move the pressed child element."""
        self._pressed.move(shifted)
        self._image_ready = False

    # =============================================
    # Resizing
    # =============================================
    def set_scale(self, scale: float):
        """Set the personal scale of the object and update properties accordingly."""
        self._personal_scale = scale
        self._update_properties_after_resizing()

    def update_scale(self, parent_scale=1.0):
        """Update the scale based on the parent scale."""
        self._parent_scale = parent_scale
        self._update_properties_after_resizing()

    def _adjust_scale(self, distance: float):
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_scale(min(max(new_radius / DEFAULT_WORD_RADIUS / self._parent_scale,
                               SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def set_inner_scale(self, scale: float):
        """Set the inner circle scale and update related properties."""
        self.inner_scale = scale
        self.inner_radius = self.outer_radius * self.inner_scale

        for consonant in self.consonants:
            consonant.resize(self)

        if self.vowel:
            self.vowel.resize(self)

        self._update_inner_circle_args()
        self._image_ready = False

    def _adjust_inner_scale(self, distance: float):
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_inner_scale(min(max(new_radius / self.outer_radius, INNER_CIRCLE_SCALE_MIN), INNER_CIRCLE_SCALE_MAX))

    def _update_properties_after_resizing(self):
        """Update scaling and circle radii, and calculate image properties."""
        self.scale = self._parent_scale * self._personal_scale
        self.scale_lines(self.scale)
        self.scale_outer_radius(self.scale)
        self.create_outer_circle(self.color, self.background)
        self.inner_radius = self.outer_radius * self.inner_scale
        self.border_offset = (len(self.inner_consonant.borders) - 1) * self.half_line_distance

        for consonant in self.consonants:
            consonant.resize(self)

        if self.vowel:
            self.vowel.resize(self)

        self._update_inner_circle_args()
        self._image_ready = False

        if self._following:
            self._following.update_scale(self.scale)

    # =============================================
    # Rotation
    # =============================================
    def set_direction(self, direction: float):
        """Set the direction of the object and update letters."""
        for consonant in self.consonants:
            consonant.update_direction(direction)

        if self.vowel:
            self.vowel.update_direction(direction)

        self.direction = direction
        self._image_ready = False

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the syllable when moved."""
        adjusted_point = point - self._point_bias
        self.set_direction(adjusted_point.direction())

    # =============================================
    # Helper Functions for Updating Image Arguments
    # =============================================
    def _update_inner_circle_args(self):
        """Prepare arguments for drawing inner circles."""
        self._inner_circle_arg_dict = []
        if len(self.inner_consonant.borders) == 1:
            adjusted_radius = ensure_min_radius(self.inner_radius + self.inner_consonant.half_line_widths[0])
            self._inner_circle_arg_dict.append(
                self._create_circle_args(adjusted_radius, self.inner_consonant.line_widths[0]))
        else:
            for i in range(2):
                adjusted_radius = ensure_min_radius(
                    self.inner_radius + (-1) ** i * self.half_line_distance + self.inner_consonant.half_line_widths[i])
                self._inner_circle_arg_dict.append(
                    self._create_circle_args(adjusted_radius, self.inner_consonant.line_widths[i]))

    def _create_circle_args(self, adjusted_radius: float, line_width: float) -> dict:
        """Generate circle arguments for drawing."""
        start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
        end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
        return {'xy': (start, end), 'outline': self.color, 'fill': self.background, 'width': line_width}

    # =============================================
    # Drawing
    # =============================================
    def get_image(self) -> Image:
        """Generate the syllable image."""
        if self._image_ready:
            return self._image

        # Clear the image
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

        if self.vowel and self.vowel.vowel_type is VowelType.HIDDEN:
            self.vowel.redraw(self._draw)
        self._redraw_consonants()
        self._redraw_inner_circle()
        if self.vowel and self.vowel.vowel_type is not VowelType.HIDDEN:
            self.vowel.redraw(self._draw)

        # Paste the outer circle image
        self.paste_outer_circle(self._image)
        self._image_ready = True
        return self._image

    def _redraw_consonants(self):
        """Draw all consonants."""
        for cons in self.consonants:
            cons.redraw(self._draw)

    def _redraw_inner_circle(self):
        """Draw the inner circle using predefined arguments."""
        for args in self._inner_circle_arg_dict:
            self._draw.ellipse(**args)

    def apply_color_changes(self):
        """Update color-dependent arguments."""
        for consonant in self.consonants:
            consonant.update_argument_dictionaries()

        if self.vowel:
            self.vowel.update_argument_dictionaries()

        self.create_outer_circle(self.color, self.background)
        self._update_inner_circle_args()
        self._image_ready = False

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self, direction_sign: int, is_tail: bool):
        """Perform an animation step by adjusting directions."""
        if self.vowel:
            self.vowel.perform_animation(-direction_sign)

        for consonant in self.consonants:
            consonant.perform_animation(direction_sign)

        if is_tail:
            delta = direction_sign * 2 * math.pi / AnimationProperties.cycle
            self.set_direction(self.direction + delta)
        else:
            self._image_ready = False
