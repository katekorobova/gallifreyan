from __future__ import annotations

import math
from abc import ABC, abstractmethod
from random import uniform
from typing import Optional

from PIL.Image import Image
from PIL.ImageDraw import ImageDraw

from .characters import Letter, Separator, Character
from .characters.consonants import Consonant
from .characters.vowels import Vowel, VowelType
from .common import Interactive
from .common.circles import OuterCircle, InnerCircle, DistanceInfo
from .. import repository
from ..utils import Point, PressedType, create_empty_image
from ...config import DEFAULT_WORD_RADIUS, SYLLABLE_INITIAL_SCALE_MIN, \
    SYLLABLE_INITIAL_SCALE_MAX, SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX, INNER_CIRCLE_INITIAL_SCALE_MIN, \
    INNER_CIRCLE_INITIAL_SCALE_MAX, INNER_CIRCLE_SCALE_MIN, INNER_CIRCLE_SCALE_MAX, SYLLABLE_BG, SYLLABLE_COLOR, ALEPH


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


class Syllable(AbstractSyllable, Interactive):
    """
    Represents a structured syllable, which may consist of consonants and vowels.
    Manages visual representation and interactive behavior.
    """
    background = SYLLABLE_BG
    color = SYLLABLE_COLOR

    def __init__(self, consonant: Consonant = None, vowel: Vowel = None):
        """Initialize a syllable with an optional consonant and vowel."""
        super().__init__()
        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(distance_info)
        self.inner_circle = InnerCircle(distance_info)

        # Image-related attributes
        self._image, self._draw = create_empty_image()
        self._image_ready = False

        # Core attributes
        self.first_consonant, self.vowel = consonant, vowel
        self.second_consonant: Optional[Consonant] = None
        self._following: Optional[Syllable] = None
        self.consonants: list[Consonant] = []
        self._update_key_properties()

        # Scale, radius, and positioning attributes
        self._scale = 0.0
        self._center = Point()
        self._parent_scale = 1.0
        self._parent_outer_circle: Optional[OuterCircle] = None
        self._personal_scale = uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self._inner_scale = uniform(INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX)
        self._update_after_resizing()

        self._direction = 0
        self.set_direction(uniform(-math.pi, math.pi))

        # Interaction properties
        self._pressed_letter: Optional[Letter] = None

    # =============================================
    # Initialization
    # =============================================
    def set_following(self, following: Optional[Syllable]) -> None:
        """Set the following syllable."""
        self._following = following

    def _update_text(self) -> None:
        self.text = ''.join(
            letter.text for letter in (self.first_consonant, self.second_consonant, self.vowel) if letter)

    def _update_key_properties(self) -> None:
        """Update syllable properties such as consonants, letters, and text representation."""
        outer_consonant = (
                self.first_consonant or Consonant.get_consonant(ALEPH, *repository.get().all[ALEPH].properties))
        inner_consonant = self.second_consonant or outer_consonant
        self.consonants = sorted({outer_consonant, inner_consonant}, key=lambda l: l.consonant_type.group)
        self._update_text()

        self.outer_circle.initialize(outer_consonant.borders)
        self.inner_circle.initialize(inner_consonant.borders)

    # =============================================
    # Insertion
    # =============================================
    def add(self, character: Character) -> bool:
        """Add a letter to the syllable, if possible."""
        if isinstance(character, Vowel) and not self.vowel:
            self.vowel = character
        elif (isinstance(character, Consonant) and not self.second_consonant and not self.vowel and
              Consonant.compatible(self.first_consonant, character)):
            self.second_consonant = character
        else:
            return False

        character.initialize(self._direction, self._scale, self.outer_circle, self.inner_circle)
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
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle press events at a given point."""
        shifted = point - self._center
        distance = shifted.distance()
        if self.outer_circle.outside_circle(distance):
            return None

        return (self._handle_outer_border_press(distance) or
                self._handle_visible_vowel_press(shifted) or
                self._handle_inner_space_press(shifted, distance) or
                self._handle_inner_border_press(distance) or
                self._handle_consonant_press(shifted) or
                self._handle_hidden_vowel_press(shifted) or
                self._handle_parent_press(shifted))

    def _handle_outer_border_press(self, distance: float) -> Optional[PressedType]:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self._distance_bias = distance - self.outer_circle.radius
            self._pressed_type = PressedType.OUTER_CIRCLE
            return self._pressed_type
        return None

    def _handle_inner_space_press(self, point: Point, distance: float) -> Optional[PressedType]:
        """Handle press events inside the inner circle."""
        if self.inner_circle.inside_circle(distance):
            return self._handle_parent_press(point)
        return None

    def _handle_inner_border_press(self, distance: float) -> Optional[PressedType]:
        """Handle press events on the inner border."""
        if self.inner_circle.on_circle(distance):
            self._distance_bias = distance - self.inner_circle.radius
            self._pressed_type = PressedType.INNER_CIRCLE
            return self._pressed_type
        return None

    def _handle_parent_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events for the parent."""
        self._position_bias = point
        self._pressed_type = PressedType.SELF
        return self._pressed_type

    def _handle_visible_vowel_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events for visible vowels."""
        if self.vowel and self.vowel.vowel_type is not VowelType.HIDDEN and self.vowel.press(point):
            self._pressed_letter = self.vowel
            self._pressed_type = PressedType.CHILD
            return self._pressed_type
        return None

    def _handle_hidden_vowel_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events for hidden vowels."""
        if self.vowel and self.vowel.vowel_type is VowelType.HIDDEN and self.vowel.press(point):
            self._pressed_letter = self.vowel
            self._pressed_type = PressedType.CHILD
            return self._pressed_type
        return None
    def _handle_consonant_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events for consonants."""
        for cons in reversed(self.consonants):
            if cons.press(point):
                self._pressed_letter = cons
                self._pressed_type = PressedType.CHILD
                return self._pressed_type
        return None

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point):
        """Move the object based on the provided point and head syllable's radius."""
        shifted = point - self._center
        distance = shifted.distance()
        match self._pressed_type:
            case PressedType.INNER_CIRCLE:
                self._adjust_inner_scale(distance)
            case PressedType.OUTER_CIRCLE:
                self._adjust_scale(distance)
            case PressedType.SELF:
                self._adjust_direction(point)
            case PressedType.CHILD:
                self._move_child(shifted)

    def _move_child(self, shifted: Point):
        """Move the pressed child element."""
        self._pressed_letter.move(shifted)
        self._image_ready = False

    def _calculate_center(self) -> None:
        if self._parent_outer_circle:
            radius = self._parent_outer_circle.radius
            self._center = Point(math.cos(self._direction) * radius, math.sin(self._direction) * radius)
        else:
            self._center = Point()

    # =============================================
    # Resizing
    # =============================================
    def get_scale(self):
        return self._scale

    def set_parent_outer_circle(self, parent_outer_circle: Optional[OuterCircle]):
        self._parent_outer_circle = parent_outer_circle

    def set_personal_scale(self, personal_scale: float):
        """Set the personal scale of the object and update properties accordingly."""
        self._personal_scale = personal_scale
        self._update_after_resizing()

    def set_parent_scale(self, parent_scale: float):
        """Update the scale based on the parent scale."""
        self._parent_scale = parent_scale
        self._calculate_center()
        self._update_after_resizing()

    def _adjust_scale(self, distance: float):
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_personal_scale(min(max(new_radius / DEFAULT_WORD_RADIUS / self._parent_scale,
                                        SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def set_inner_scale(self, scale: float):
        """Set the inner circle scale and update related properties."""
        self._image_ready = False
        self._inner_scale = scale
        self.inner_circle.set_radius(self._scale * self._inner_scale * DEFAULT_WORD_RADIUS)
        self.inner_circle.create_circle(self.color, self.background)

        for consonant in self.consonants:
            consonant.resize(self._scale, self.outer_circle, self.inner_circle)

        if self.vowel:
            self.vowel.resize(self._scale, self.outer_circle, self.inner_circle)

    def _adjust_inner_scale(self, distance: float):
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_inner_scale(min(max(new_radius / self.outer_circle.radius, INNER_CIRCLE_SCALE_MIN), INNER_CIRCLE_SCALE_MAX))

    def _update_after_resizing(self):
        """Update scaling and circle radii, and calculate image properties."""
        self._image_ready = False
        self._scale = self._parent_scale * self._personal_scale
        self.distance_info.scale_distance(self._scale)
        self.outer_circle.scale_borders(self._scale)
        self.outer_circle.set_radius(self._scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)

        self.inner_circle.scale_borders(self._scale)
        self.inner_circle.set_radius(self._scale * self._inner_scale * DEFAULT_WORD_RADIUS)
        self.inner_circle.create_circle(self.color, self.background)

        for consonant in self.consonants:
            consonant.resize(self._scale, self.outer_circle, self.inner_circle)

        if self.vowel:
            self.vowel.resize(self._scale, self.outer_circle, self.inner_circle)

        if self._following:
            self._following.set_parent_scale(self._scale)

    # =============================================
    # Rotation
    # =============================================
    def set_direction(self, direction: float):
        """Set the direction of the object and update letters."""
        self._image_ready = False
        self._direction = direction
        self._calculate_center()

        for consonant in self.consonants:
            consonant.set_parent_direction(direction)

        if self.vowel:
            self.vowel.set_parent_direction(direction)

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the syllable when moved."""
        adjusted_point = point - self._position_bias
        self.set_direction(adjusted_point.direction())

    # =============================================
    # Drawing
    # =============================================
    def redraw(self, image: Image, draw: ImageDraw) -> None:
        """Generate the syllable image."""
        if not self._image_ready:
            self._create_image()
        image.paste(self._image, self._center.tuple(), self._image)

    def _create_image(self):
        # Clear the image
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

        if self.vowel and self.vowel.vowel_type is VowelType.HIDDEN:
            self.vowel.redraw(self._image, self._draw)
        self._redraw_consonants()
        self.inner_circle.redraw_circle(self._draw)
        if self.vowel and self.vowel.vowel_type is not VowelType.HIDDEN:
            self.vowel.redraw(self._image, self._draw)

        # Paste the outer circle image
        self.outer_circle.paste_circle(self._image)
        self._image_ready = True

    def _redraw_consonants(self):
        """Draw all consonants."""
        for cons in self.consonants:
            cons.redraw(self._image, self._draw)

    def apply_color_changes(self):
        """Update color-dependent arguments."""
        self._image_ready = False
        self.outer_circle.create_circle(self.color, self.background)
        self.inner_circle.create_circle(self.color, self.background)

        for consonant in self.consonants:
            consonant.apply_color_changes()

        if self.vowel:
            self.vowel.apply_color_changes()

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self, angle: float):
        """Perform an animation step by adjusting directions."""
        letter_angle = 2 * angle
        for consonant in self.consonants:
            consonant.perform_animation(letter_angle)
        if self.vowel:
            self.vowel.perform_animation(-letter_angle)

        if self._parent_outer_circle:
            self.set_direction(self._direction + angle)
        else:
            self._image_ready = False
