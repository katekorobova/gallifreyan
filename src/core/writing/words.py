import math
import tkinter as tk
from abc import ABC
from dataclasses import dataclass
from itertools import count, repeat
from typing import Optional

from PIL import ImageTk, Image, ImageDraw

from .characters import Character, Separator, CharacterType
from .syllables import Consonant, Syllable, SeparatorSyllable, AbstractSyllable
from .vowels import Vowel
from ..utils import Point, PressedType, line_width, half_line_distance
from ...config import (WORD_IMAGE_RADIUS, DEFAULT_WORD_RADIUS, MIN_RADIUS,
                       OUTER_CIRCLE_SCALE_MIN, OUTER_CIRCLE_SCALE_MAX,
                       WORD_BG, WORD_COLOR)


@dataclass
class _RedistributionState:
    """Represents the state during syllable redistribution."""
    syllable: Optional[Syllable] = None
    cons2: Optional[Consonant] = None
    completed = False


def unique_syllables(items: list[AbstractSyllable]) -> list[Syllable]:
    """Return a list of unique syllables while preserving order."""
    seen = set()
    return [item for item in items
            if not (item in seen or seen.add(item)) and isinstance(item, Syllable)]


class AbstractWord(ABC):
    """Abstract class representing a word composed of characters."""

    def __init__(self):
        """Initialize an abstract word object."""
        self.characters: list[Character] = []
        self.text = ''

    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index."""
        self.characters[index:index] = characters
        self._update_text()
        return True

    def remove_characters(self, index: int, end_index: int):
        """Remove characters from the word."""
        self.characters[index: end_index] = []
        self._update_text()

    def remove_starting_with(self, index: int):
        """Remove characters from the word, updating properties accordingly."""
        self.characters[index:] = []
        self._update_text()

    def _update_text(self):
        """Update the word's text representation."""
        self.text = ''.join(character.text for character in self.characters)


class SpaceWord(AbstractWord):
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


class Word(AbstractWord):
    """Represents a structured word with characters, syllables, and image rendering."""
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    background = WORD_BG
    color = WORD_COLOR

    def __init__(self, center: Point, characters: list[Character]):
        """Initialize a Word instance with a center point and characters."""
        super().__init__()
        self.center = center
        self.borders = '21'
        self.outer_radius = 0.0

        length = len(self.borders)
        self._line_widths = list(repeat(0, length))
        self._half_line_widths = list(repeat(0.0, length))
        self._half_line_distance = 0.0
        self.outer_circle_scale = OUTER_CIRCLE_SCALE_MIN

        # Image-related attributes
        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')
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
        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Syllable] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    # =============================================
    # Initialization
    # =============================================
    @classmethod
    def _create_empty_image(cls, mode='RGBA') -> tuple[Image.Image, ImageDraw.Draw]:
        """Create an empty image and its drawing object."""
        image = Image.new(mode, (cls.IMAGE_CENTER * 2))
        return image, ImageDraw.Draw(image)

    def update_properties_after_resizing(self):
        """Update properties based on the head syllable scale."""
        head_scale = self.head.scale
        self.outer_radius = DEFAULT_WORD_RADIUS * self.outer_circle_scale * head_scale
        self._line_widths = [line_width(border, head_scale) for border in self.borders]
        self._half_line_widths = [width / 2 for width in self._line_widths]
        self._half_line_distance = half_line_distance(head_scale)
        self._create_outer_circle()

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
    def press(self, point: Point) -> bool:
        """Handle press events."""
        word_point = point - self.center
        if self.tail:
            distance = word_point.distance()
            if distance > self.outer_radius + self._half_line_distance:
                return False

            return (self._handle_outer_border_press(distance) or
                    self._handle_tail_press(word_point) or
                    self._handle_head_press(word_point) or
                    self._handle_parent_press(word_point))

        if self.head:
            return self._handle_head_press(word_point)

        return False

    def _handle_outer_border_press(self, distance: float) -> bool:
        """Handle press events on the outer border."""
        if distance > self.outer_radius - self._half_line_distance:
            self.pressed_type = PressedType.BORDER
            self._distance_bias = distance - self.outer_radius
            return True
        return False

    def _handle_tail_press(self, word_point: Point) -> bool:
        """Attempt to press a non-head syllable."""
        for syllable in reversed(self.tail):
            head_radius = self.head.outer_radius
            offset_point = word_point - Point(math.cos(syllable.direction) * head_radius,
                                              math.sin(syllable.direction) * head_radius)
            if syllable.press(offset_point):
                self.pressed_type = PressedType.CHILD
                self._pressed = syllable
                return True
        return False

    def _handle_head_press(self, word_point: Point) -> bool:
        """Attempt to press the head syllable."""
        if self.head.press(word_point):
            if self.head.pressed_type == PressedType.PARENT:
                self.pressed_type = PressedType.PARENT
                self._point_bias = word_point
            else:
                self.pressed_type = PressedType.CHILD
                self._pressed = self.head
            return True
        return False

    def _handle_parent_press(self, word_point: Point) -> bool:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = word_point
        return True

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point):
        """Handle move events."""
        word_point = point - self.center
        match self.pressed_type:
            case PressedType.CHILD:
                self._move_child(word_point)
            case PressedType.BORDER:
                self._resize(word_point)
            case PressedType.PARENT:
                self.center = point - self._point_bias
            case _:
                return
        self._image_ready = False

    def _move_child(self, word_point: Point):
        """Move a pressed child syllable."""
        if self._pressed is self.head:
            self.head.move(word_point)
            self.update_properties_after_resizing()
        else:
            head_radius = self.head.outer_radius
            self._pressed.move(word_point, head_radius)

    # =============================================
    # Resizing
    # =============================================
    def _resize(self, word_point: Point):
        """Resize the word based on movement."""
        head_scale = self.head.scale
        new_radius = word_point.distance() - self._distance_bias
        self.outer_circle_scale = min(
            max(new_radius / DEFAULT_WORD_RADIUS / head_scale, OUTER_CIRCLE_SCALE_MIN),
            OUTER_CIRCLE_SCALE_MAX)

        self.outer_radius = DEFAULT_WORD_RADIUS * self.outer_circle_scale * head_scale
        self._create_outer_circle()

    # =============================================
    # Insertion and Deletion
    # =============================================
    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index and update syllables."""
        if any(character.character_type == CharacterType.SPACE for character in characters):
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
            if index < len(self.characters) and syllable is self.syllables_by_indices[index]:
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
            if not state.cons2 and state.syllable.add(consonant):
                state.cons2 = consonant
                self.syllables_by_indices[index] = state.syllable
            else:
                if self._check_syllable_start(index, consonant):
                    state.completed = True
                else:
                    state.syllable = Syllable(consonant)
                    state.cons2 = None
                    self.syllables_by_indices[index] = state.syllable
        else:
            if self._check_syllable_start(index, consonant):
                state.completed = True
            else:
                state.syllable = Syllable(consonant)
                self.syllables_by_indices[index] = state.syllable

    def _process_vowel(self, index: int, vowel: Vowel, state: _RedistributionState) -> None:
        """Process vowel letter and update state."""
        if state.syllable:
            state.syllable.add(vowel)
            self.syllables_by_indices[index] = state.syllable
            state.syllable = None
            state.cons2 = None
        else:
            if self.syllables_by_indices[index]:
                state.completed = True
            else:
                self.syllables_by_indices[index] = Syllable(vowel=vowel)

    def _process_separator(
            self, index: int, separator: Separator, state: _RedistributionState) -> None:
        """Process separator character and update state."""
        if state.syllable and state.syllable.add(separator):
            self.syllables_by_indices[index] = state.syllable
        else:
            state.syllable = None
            state.cons2 = None

            if self.syllables_by_indices[index]:
                state.completed = True
            else:
                self.syllables_by_indices[index] = SeparatorSyllable(separator)

    def _check_syllable_start(self, index: int, consonant: Consonant) -> bool:
        """Check if the given consonant starts the syllable at the specified index."""
        return self.syllables_by_indices[index] and \
            self.syllables_by_indices[index].head is consonant

    # =============================================
    # Helper Functions for Updating Image Arguments
    # =============================================
    def _create_outer_circle(self):
        """Create the outer circle representation."""
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._border_image.size), fill=1)
        if len(self.borders) == 1:
            adjusted_radius = self.outer_radius + self._half_line_widths[0]
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=self.color, width=self._line_widths[0])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self._line_widths[0])
        else:
            adjusted_radius = \
                self.outer_radius + self._half_line_distance + self._half_line_widths[0]
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=self.color,
                                      fill=self.background, width=self._line_widths[0])

            adjusted_radius = max(
                self.outer_radius - self._half_line_distance + self._half_line_widths[1],
                MIN_RADIUS)
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=self.color, width=self._line_widths[1])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self._line_widths[1])

    # =============================================
    # Drawing
    # =============================================
    def get_image(self) -> Image:
        """Retrieve the generated image, creating it if necessary."""
        if not self._image_ready:
            self._create_image()
        return self._image

    def put_image(self, canvas: tk.Canvas):
        """Create and display the word image on the canvas."""
        if self._image_ready:
            if self.canvas_item_id is not None:
                canvas.tag_raise(self.canvas_item_id)
            return

        if self.canvas_item_id is not None:
            canvas.delete(self.canvas_item_id)

        if self.syllables:
            self._create_image()
            self._image_tk.paste(self._image)
            self.canvas_item_id = canvas.create_image(self.center, image=self._image_tk)
        else:
            self._image_ready = True
            self.canvas_item_id = None

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
                self._image.paste(self._border_image, mask=self._mask_image)
            else:
                # Clear the image
                self._draw.rectangle(((0, 0), self._image.size), fill=0)

                # Paste the head syllable onto the image
                self._paste_head()

        self._image_ready = True

    def _paste_head(self):
        """Paste the head syllable's image onto the word image."""
        image = self.head.get_image()
        self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER), image)

    def _paste_tail(self, syllable: Syllable, radius: float):
        """Paste a non-head syllable's image at a position on the head syllable's orbit."""
        image = syllable.get_image()
        self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER +
                                       Point(round(math.cos(syllable.direction) * radius),
                                             round(math.sin(syllable.direction) * radius))), image)

    def apply_color_changes(self):
        """Apply color changes to the image and its syllables."""
        self._create_outer_circle()
        if self.syllables:
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
