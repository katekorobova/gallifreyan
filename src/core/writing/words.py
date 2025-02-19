import math
import random
import tkinter as tk
from abc import ABC
from dataclasses import dataclass
from itertools import count, repeat
from typing import Optional

from PIL import ImageTk, Image

from .characters import Character, Separator, CharacterType
from .common import Interactive
from ..utils import Point, PressedType, create_empty_image
from ...config import (WORD_BG, WORD_COLOR, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT,
                       WORD_IMAGE_RADIUS, DEFAULT_WORD_RADIUS,
                       OUTER_CIRCLE_SCALE_MIN, OUTER_CIRCLE_SCALE_MAX, WORD_BORDERS)
from ...core.writing.characters.vowels import Vowel
from ...core.writing.common.circles import OuterCircle, DistanceInfo
from ...core.writing.syllables import Consonant, Syllable, SeparatorSyllable, AbstractSyllable


@dataclass
class _RedistributionState:
    """Represents the state during syllable redistribution."""
    syllable: Optional[Syllable] = None
    completed = False


def unique_syllables(items: list[AbstractSyllable]) -> list[Syllable]:
    """Return a list of unique syllables while preserving order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item)) and isinstance(item, Syllable)]


class Token(ABC):
    """Abstract class representing a token composed of characters."""

    def __init__(self):
        """Initialize an abstract word object."""
        self.characters: list[Character] = []
        self.text = ''

    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index."""
        self.characters[index:index] = characters
        self._update_text()
        return True

    def remove_characters(self, index: int, end_index: int) -> None:
        """Remove characters from the word."""
        self.characters[index: end_index] = []
        self._update_text()

    def remove_starting_with(self, index: int) -> None:
        """Remove characters from the word, updating properties accordingly."""
        self.characters[index:] = []
        self._update_text()

    def _update_text(self) -> None:
        """Update the word's text representation."""
        self.text = ''.join(character.text for character in self.characters)

    def paste_image(self, image: Image.Image, position: Point) -> None:
        """Retrieve the generated image, creating it if necessary."""

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]) -> None:
        """Create and display the word image on the canvas."""

    def apply_color_changes(self) -> None:
        """Apply color changes to the image and its syllables."""

    def perform_animation(self, direction_sign: int) -> None:
        """Perform an animation step."""


class SpaceToken(Token):
    """Represents a word consisting only of space characters."""

    def __init__(self, characters: list[Character]):
        """Initialize a space word object."""
        super().__init__()
        self.characters = characters
        self._update_text()

    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index """
        if any(character.character_type != CharacterType.SPACE for character in characters):
            return False

        return super().insert_characters(index, characters)


class InteractiveToken(Token, Interactive, ABC):
    """Abstract class representing a token with interactive properties."""


class Word(InteractiveToken):
    """Represents a structured word with characters, syllables, and image rendering."""
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    background = WORD_BG
    color = WORD_COLOR

    def __init__(self, characters: list[Character]):
        """Initialize a Word instance with characters."""
        super().__init__()

        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(self.IMAGE_CENTER, distance_info)
        self.outer_circle.initialize(WORD_BORDERS)

        self.outer_circle_scale = OUTER_CIRCLE_SCALE_MIN
        self.center = Point(random.randint(DEFAULT_WORD_RADIUS, DEFAULT_CANVAS_WIDTH - DEFAULT_WORD_RADIUS),
                            random.randint(DEFAULT_WORD_RADIUS, DEFAULT_CANVAS_HEIGHT - DEFAULT_WORD_RADIUS))

        # Image-related attributes
        self._image, self._draw = create_empty_image(self.IMAGE_CENTER)
        self._image_tk = ImageTk.PhotoImage(image=self._image)
        self._image_ready = False
        self.canvas_item_id: Optional[int] = None

        # Initialize syllables and their relationships
        self.syllables: list[Syllable] = []
        self.head: Optional[Syllable] = None
        self.tail: list[Syllable] = []
        self.syllables_by_indices: list[Optional[AbstractSyllable]] = []
        self.insert_characters(0, characters)

        # Interaction properties
        self._pressed_syllable: Optional[Syllable] = None

    # =============================================
    # Initialization
    # =============================================
    def update_properties_after_resizing(self):
        """Update properties based on the head syllable scale."""
        head_scale = self.head.scale
        self.distance_info.scale_distance(head_scale)
        self.outer_circle.scale_borders(head_scale)
        self.outer_circle.set_radius(self.outer_circle_scale * head_scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)

    def set_syllables(self):
        """Organize characters into syllables and update relationships."""
        self.syllables = unique_syllables(self.syllables_by_indices)
        if self.syllables:
            for i in reversed(range(0, len(self.syllables) - 1)):
                self.syllables[i].set_following(self.syllables[i + 1])
            self.syllables[-1].set_following(None)
            self.head = self.syllables[0]
            self.tail = self.syllables[1:]
            self.head.update_scale()
            self.update_properties_after_resizing()
        else:
            self.head = None
            self.tail = []

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle press events."""
        word_point = point - self.center
        if self.tail:
            distance = word_point.distance()
            if self.outer_circle.outside_circle(distance):
                return None

            return (self._handle_outer_border_press(distance) or
                    self._handle_tail_press(word_point) or
                    self._handle_head_press(word_point) or
                    self._handle_parent_press(word_point))

        if self.head:
            return self._handle_head_press(word_point)

        return None

    def _handle_outer_border_press(self, distance: float) -> Optional[PressedType]:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self._distance_bias = distance - self.outer_circle.radius
            self._pressed_type = PressedType.OUTER_CIRCLE
            return self._pressed_type
        return None

    def _handle_tail_press(self, word_point: Point) -> Optional[PressedType]:
        """Attempt to press a non-head syllable."""
        for syllable in reversed(self.tail):
            head_radius = self.head.outer_circle.radius
            offset_point = word_point - Point(math.cos(syllable.direction) * head_radius,
                                              math.sin(syllable.direction) * head_radius)
            if syllable.press(offset_point):
                self._pressed_syllable = syllable
                self._pressed_type = PressedType.CHILD
                return self._pressed_type
        return None

    def _handle_head_press(self, word_point: Point) -> Optional[PressedType]:
        """Attempt to press the head syllable."""
        head_pressed_type = self.head.press(word_point)
        if head_pressed_type:
            if head_pressed_type == PressedType.SELF:
                self._pressed_type = PressedType.SELF
                self._point_bias = word_point
            else:
                self._pressed_syllable = self.head
                self._pressed_type = PressedType.CHILD
            return self._pressed_type
        return None

    def _handle_parent_press(self, word_point: Point) -> bool:
        """Handle press events for the parent."""
        self._point_bias = word_point
        self._pressed_type = PressedType.SELF
        return True

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point, radius=0.0) -> None:
        """Handle move events."""
        word_point = point - self.center
        match self._pressed_type:
            case PressedType.CHILD:
                self._move_child(word_point)
            case PressedType.OUTER_CIRCLE:
                self._resize(word_point)
            case PressedType.SELF:
                self.center = point - self._point_bias
            case _:
                return
        self._image_ready = False

    def _move_child(self, word_point: Point) -> None:
        """Move a pressed child syllable."""
        if self._pressed_syllable is self.head:
            self.head.move(word_point)
            self.update_properties_after_resizing()
        else:
            head_radius = self.head.outer_circle.radius
            self._pressed_syllable.move(word_point, head_radius)

    # =============================================
    # Resizing
    # =============================================
    def _resize(self, word_point: Point) -> None:
        """Resize the word based on movement."""
        head_scale = self.head.scale
        new_radius = word_point.distance() - self._distance_bias
        self.outer_circle_scale = min(
            max(new_radius / DEFAULT_WORD_RADIUS / head_scale, OUTER_CIRCLE_SCALE_MIN),
            OUTER_CIRCLE_SCALE_MAX)

        self.outer_circle.set_radius(self.outer_circle_scale * head_scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)

    # =============================================
    # Insertion and Deletion
    # =============================================
    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index and update syllables."""
        if not all(character.character_type & CharacterType.WORD for character in characters):
            return False

        self._split_syllable(index)

        super().insert_characters(index, characters)
        self.syllables_by_indices[index: index] = repeat(None, len(characters))

        start = self._absorb_following(index)
        self._redistribute(start)

        self.set_syllables()
        self._image_ready = False
        return True

    def remove_characters(self, index: int, end_index: int):
        """Remove characters from the word and update syllables."""
        self._split_syllable(index)
        self._split_syllable(end_index)

        super().remove_characters(index, end_index)
        self.syllables_by_indices[index: end_index] = []

        start = self._absorb_following(index)
        self._redistribute(start)

        self.set_syllables()
        self._image_ready = False

    def remove_starting_with(self, index: int):
        """Remove characters from the word, updating properties accordingly."""
        self._split_syllable(index)

        super().remove_starting_with(index)
        self.syllables_by_indices[index:] = []

        self.set_syllables()
        self._image_ready = False

    def _split_syllable(self, index: int):
        """Split the syllable at the specified index, updating syllables as needed."""
        if index > 0:
            syllable = self.syllables_by_indices[index - 1]
            if index < len(self.characters) and syllable and syllable is self.syllables_by_indices[index]:
                syllable.remove_starting_with(self.characters[index])
                for i in range(index, len(self.characters)):
                    if syllable is self.syllables_by_indices[i]:
                        self.syllables_by_indices[i] = None
                    else:
                        return

    def _absorb_following(self, index: int) -> int:
        """Absorb newly inserted letters into existing syllables."""
        start = index
        if index > 0:
            syllable = self.syllables_by_indices[index - 1]
            for i in range(index, len(self.characters)):
                if syllable.add(self.characters[i]):
                    self.syllables_by_indices[i] = syllable
                    start = i + 1
                else:
                    break
        return start

    def _redistribute(self, start: int) -> None:
        """Redistribute syllables starting from a given index."""
        state = _RedistributionState()
        for i, character in zip(count(start), self.characters[start:]):
            if isinstance(character, Consonant):
                self._process_consonant(i, character, state)
            elif isinstance(character, Vowel):
                self._process_vowel(i, character, state)
            elif isinstance(character, Separator):
                self._process_separator(i, character, state)
            else:
                raise ValueError(f"No such character: '{character.text}'")
            if state.completed:
                break

    def _process_consonant(
            self, index: int, consonant: Consonant, state: _RedistributionState) -> None:
        """Process consonant letter and update state."""
        if state.syllable:
            if not state.syllable.add(consonant):
                if self._check_syllable_start(index, consonant):
                    state.completed = True
                    return

                state.syllable = Syllable(consonant)
                state.cons2 = None
        else:
            if self._check_syllable_start(index, consonant):
                state.completed = True
                return

            state.syllable = Syllable(consonant)
        self.syllables_by_indices[index] = state.syllable

    def _process_vowel(self, index: int, vowel: Vowel, state: _RedistributionState) -> None:
        """Process vowel letter and update state."""
        if state.syllable:
            state.syllable.add(vowel)
            self.syllables_by_indices[index] = state.syllable
            state.syllable = None
        else:
            if self.syllables_by_indices[index]:
                state.completed = True
            else:
                self.syllables_by_indices[index] = Syllable(vowel=vowel)

    def _process_separator(
            self, index: int, separator: Separator, state: _RedistributionState) -> None:
        """Process separator character and update state."""
        state.syllable = None
        if self.syllables_by_indices[index]:
            state.completed = True
        else:
            self.syllables_by_indices[index] = SeparatorSyllable(separator)

    def _check_syllable_start(self, index: int, consonant: Consonant) -> bool:
        """Check if the given consonant starts the syllable at the specified index."""
        syllable = self.syllables_by_indices[index]
        return isinstance(syllable, Syllable) and syllable.first_consonant is consonant

    # =============================================
    # Drawing
    # =============================================
    def paste_image(self, image: Image.Image, position: Point):
        """Retrieve the generated image, creating it if necessary."""
        if not self._image_ready:
            self._create_image()
        image.paste(self._image, (self.center - self.IMAGE_CENTER - position).tuple(), self._image)

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]):
        """Create and display the word image on the canvas."""
        if self._image_ready:
            if self.canvas_item_id is None:
                self._image_tk.paste(self._image)
                self.canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)
            else:
                canvas.tag_raise(self.canvas_item_id)
                to_be_removed.remove(self.canvas_item_id)
        else:
            self._create_image()
            self._image_tk.paste(self._image)
            self.canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)

    def _create_image(self):
        """Generate the full word image by assembling syllables and outer elements."""
        if self.head:
            if self.tail:
                # Clear the image
                self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

                # Paste the head syllable onto the image
                self._paste_head()

                # Paste other syllables onto the image
                head_radius = self.head.scale * DEFAULT_WORD_RADIUS
                for s in self.tail:
                    self._paste_tail(s, head_radius)

                # Paste the outer circle image
                self.outer_circle.paste_circle(self._image)
            else:
                # Clear the image
                self._draw.rectangle(((0, 0), self._image.size), fill=0)

                # Paste the head syllable onto the image
                self._paste_head()

        self._image_ready = True

    def _paste_head(self):
        """Paste the head syllable's image onto the word image."""
        image = self.head.get_image()
        self._image.paste(image, (self.IMAGE_CENTER - Syllable.IMAGE_CENTER).tuple(), image)

    def _paste_tail(self, syllable: Syllable, radius: float):
        """Paste a non-head syllable's image at a position on the head syllable's orbit."""
        image = syllable.get_image()
        self._image.paste(image, (self.IMAGE_CENTER - Syllable.IMAGE_CENTER +
                                  Point(math.cos(syllable.direction) * radius,
                                        math.sin(syllable.direction) * radius)).tuple(), image)

    def apply_color_changes(self):
        """Apply color changes to the image and its syllables."""
        self.outer_circle.create_circle(self.color, self.background)
        for syllable in self.syllables:
            syllable.apply_color_changes()
        self._image_ready = False

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self, direction_sign: int):
        """Perform an animation step, changing syllables' directions."""
        if self.head:
            self.head.perform_animation(direction_sign, False)

            for syllable in self.tail:
                direction_sign = -direction_sign
                syllable.perform_animation(direction_sign, True)

            self._image_ready = False
