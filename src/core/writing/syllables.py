import math
import random
from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image, ImageDraw

from .characters import Letter, Separator, Character
from .consonants import Consonant
from .vowels import Vowel, VowelType
from .. import repository
from ..utils import Point, PressedType, half_line_distance
from ...config import (SYLLABLE_IMAGE_RADIUS, DEFAULT_WORD_RADIUS, MIN_RADIUS,
                       SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX,
                       SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX,
                       INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX,
                       INNER_CIRCLE_SCALE_MIN, INNER_CIRCLE_SCALE_MAX,
                       SYLLABLE_BG, SYLLABLE_COLOR, CYCLE, ALEPH)


class AbstractSyllable(ABC):

    def __init__(self, head: Character):
        self.head = head
        self.text = head.text

    @abstractmethod
    def remove_starting_with(self, character: Character) -> None:
        """
        Remove a character from the syllable, updating properties accordingly.
        """
        pass

    @abstractmethod
    def add(self, character: Character) -> bool:
        """
        Add a character to the syllable, if possible.
        """
        pass

    @abstractmethod
    def insert(self, index: int, character: Character) -> bool:
        """
        Insert a character into the syllable, if possible.
        """
        pass


class SeparatorSyllable(AbstractSyllable):
    def __init__(self, separator: Separator):
        super().__init__(separator)
        self.characters = [separator]

    def remove_starting_with(self, character: Character) -> None:
        """
        Remove a character from the syllable, updating properties accordingly.
        """
        if isinstance(character, Separator) and character in self.characters:
            index = self.characters.index(character)
            self.characters[index:] = []
            self._update_text()

    def add(self, character: Character) -> bool:
        """
        Add a character to the syllable, if possible.
        """
        if isinstance(character, Separator):
            self.characters.append(character)
            self._update_text()
            return True
        else:
            return False

    def insert(self, index: int, character: Character) -> bool:
        """
        Insert a character into the syllable, if possible.
        """
        if isinstance(character, Separator):
            self.characters.insert(index, character)
            self.head = self.characters[0]
            self._update_text()
            return True
        else:
            return False

    def _update_text(self):
        self.text = ''.join(char.text for char in self.characters)


class Syllable(AbstractSyllable):
    """
    Represents a syllable, combining consonants and vowels into structured elements with visual representation.
    """
    IMAGE_CENTER = Point(SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS)

    background = SYLLABLE_BG
    color = SYLLABLE_COLOR

    def __init__(self, cons1: Consonant = None, vowel: Vowel = None):
        super().__init__(cons1 or vowel)

        # Image-related attributes
        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')
        self._inner_circle_arg_dict: list[dict] = []
        self._image_ready = False

        # Core attributes
        self.cons1, self.vowel = cons1, vowel
        self.cons2: Optional[Consonant] = None
        self._following: Optional[Syllable] = None
        self.consonants: list[Consonant] = []
        self.letters: list[Letter] = []
        self._update_key_properties()

        # Scale, radius, and positioning attributes
        self.scale = 0.0
        self._parent_scale = 1.0
        self.outer_radius = 0.0
        self.inner_radius = 0.0
        self.half_line_distance = 0.0
        self.border_offset = (0.0, 0.0)
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
    def set_following(self, following) -> None:
        self._following = following

    @classmethod
    def _create_empty_image(cls, mode: str = 'RGBA') -> tuple[Image.Image, ImageDraw.Draw]:
        """Create an empty image with the specified mode."""
        image = Image.new(mode, (cls.IMAGE_CENTER * 2))
        return image, ImageDraw.Draw(image)

    def _update_key_properties(self):
        """Update syllable properties such as consonants, letters, and text representation."""
        self.head = self.cons1 or self.vowel
        self._outer = self.cons1 or Consonant.get_consonant(ALEPH, *repository.get().consonants[ALEPH])
        self._inner = self.cons2 or self._outer
        self.consonants = sorted({self._outer, self._inner}, key=lambda l: l.consonant_type.group)
        self.letters = [item for item in [self.cons1, self.cons2, self.vowel] if item]
        self.text = ''.join(letter.text for letter in self.letters)

    # =============================================
    # Insertion
    # =============================================
    def add(self, character: Character) -> bool:
        """Add a letter to the syllable, if possible."""
        if isinstance(character, Vowel) and not self.vowel:
            self.vowel = character
        elif isinstance(character, Consonant) \
                and not self.cons2 and not self.vowel and Consonant.compatible(self.cons1, character):
            self.cons2 = character
        else:
            return False

        character.initialize(self)
        self._update_key_properties()
        self._image_ready = False
        return True

    def insert(self, index: int, character: Character) -> bool:
        """Insert a letter into the syllable, if possible."""
        if isinstance(character, Consonant):
            if not self._insert_consonant(index, character):
                return False
        elif isinstance(character, Vowel):
            if not self._insert_vowel(index, character):
                return False
        else:
            return False

        character.initialize(self)
        self._update_key_properties()
        self._image_ready = False
        return True

    def _insert_consonant(self, index: int, consonant: Consonant) -> bool:
        match index:
            case 0:
                if not self.cons1:
                    self.cons1 = consonant
                    return True
                elif not self.cons2 and Consonant.compatible(consonant, self.cons1):
                    self.cons2 = self.cons1
                    self.cons1 = consonant
                    return True
            case 1:
                if self.cons1 and not self.cons2 and not self.vowel \
                        and Consonant.compatible(self.cons1, consonant):
                    self.cons2 = consonant
                    return True
        return False

    def _insert_vowel(self, index: int, vowel: Vowel) -> bool:
        match index:
            case 1:
                if not self.cons2 and not self.vowel:
                    self.vowel = vowel
                    return True
            case 2:
                if self.cons2 and not self.vowel:
                    self.vowel = vowel
                    return True
        return False

    # =============================================
    # Deletion
    # =============================================
    def remove_starting_with(self, character: Character):
        """Remove a letter from the syllable, updating properties accordingly."""
        if character == self.cons2:
            self.cons2, self.vowel = None, None
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

        # Check if the press is outside the outer boundary
        if distance > self.outer_radius + self.half_line_distance:
            return False

        # Check if the press is on the outer border
        if distance > self.outer_radius - self.half_line_distance:
            self._handle_outer_border_press(distance)
            return True

        # Handle press if it is on a visible vowel
        if self._handle_visible_vowel_press(point):
            return True

        # Check if the press is within the inner radius
        if distance < self.inner_radius - self.half_line_distance:
            self._handle_parent_press(point)
            return True

        # Check if the press is on the inner border
        if distance < self.inner_radius + self.half_line_distance:
            self._handle_inner_border_press(distance)
            return True

        # Handle press if it is on a consonant
        if self._handle_consonant_press(point):
            return True

        # Handle press if it is on a hidden vowel
        if self._handle_hidden_vowel_press(point):
            return True

        # Handle press events for the parent
        self._handle_parent_press(point)
        return True

    def _handle_outer_border_press(self, distance: float) -> None:
        """Handle press events on the outer border."""
        self.pressed_type = PressedType.BORDER
        self._distance_bias = distance - self.outer_radius

    def _handle_inner_border_press(self, distance: float) -> None:
        """Handle press events on the inner border."""
        self.pressed_type = PressedType.INNER
        self._distance_bias = distance - self.inner_radius

    def _handle_parent_press(self, point: Point) -> None:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = point

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
        self._personal_scale = scale
        self._update_properties_after_resizing()

    def update_scale(self, parent_scale=1.0):
        self._parent_scale = parent_scale
        self._update_properties_after_resizing()

    def _adjust_scale(self, distance: float):
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_scale(min(max(new_radius / DEFAULT_WORD_RADIUS / self._parent_scale,
                                       SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def set_inner_scale(self, scale: float):
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
        self.outer_radius = DEFAULT_WORD_RADIUS * self.scale
        self.inner_radius = self.outer_radius * self.inner_scale
        self.half_line_distance = half_line_distance(self.scale)
        self.border_offset = ((len(self._outer.borders) - 1) * self.half_line_distance,
                              (len(self._inner.borders) - 1) * self.half_line_distance)

        for consonant in self.consonants:
            consonant.resize(self)

        if self.vowel:
            self.vowel.resize(self)

        self._update_inner_circle_args()
        self._create_outer_circle()
        self._image_ready = False

        if self._following:
            self._following.update_scale(self.scale)

    # =============================================
    # Rotation
    # =============================================
    def set_direction(self, direction: float):
        self.direction = direction

        for consonant in self.consonants:
            consonant.update_direction(direction)

        if self.vowel:
            self.vowel.update_direction(direction)

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
        if len(self._inner.borders) == 1:
            adjusted_radius = self._calculate_adjusted_radius(self.inner_radius, self._inner.half_line_widths[0])
            self._inner_circle_arg_dict.append(self._create_circle_args(adjusted_radius, self._inner.line_widths[0]))
        else:
            for i in range(2):
                adjusted_radius = self._calculate_adjusted_radius(
                    self.inner_radius, (-1) ** i * self.half_line_distance + self._inner.half_line_widths[i])
                self._inner_circle_arg_dict.append(
                    self._create_circle_args(adjusted_radius, self._inner.line_widths[i]))

    def _create_circle_args(self, adjusted_radius: float, line_width: float) -> dict:
        """Generate circle arguments for drawing."""
        start, end = self.IMAGE_CENTER.shift(-adjusted_radius), self.IMAGE_CENTER.shift(adjusted_radius)
        return {'xy': (start, end), 'outline': self.color, 'fill': self.background, 'width': line_width}

    def _create_outer_circle(self):
        """Draw the outer circle for the syllable."""
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._mask_image.size), fill=1)

        if len(self._outer.borders) == 1:
            adjusted_radius = self._calculate_adjusted_radius(self.outer_radius, self._outer.half_line_widths[0])
            start, end = self.IMAGE_CENTER.shift(-adjusted_radius), self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=self.color, width=self._outer.line_widths[0])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self._outer.line_widths[0])
        else:
            adjusted_radius = self.outer_radius + self.half_line_distance + self._outer.half_line_widths[0]
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end),
                                      outline=self.color, fill=self.background, width=self._outer.line_widths[0])

            adjusted_radius = max(
                self.outer_radius - self.half_line_distance + self._outer.half_line_widths[1], MIN_RADIUS)
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=self.color, width=self._outer.line_widths[1])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self._outer.line_widths[1])

    @staticmethod
    def _calculate_adjusted_radius(base_radius: float, adjustment: float, min_radius: float = MIN_RADIUS):
        """Calculate an adjusted radius with constraints."""
        return max(base_radius + adjustment, min_radius)

    # =============================================
    # Drawing
    # =============================================
    def create_image(self) -> Image:
        """Render the syllable image."""
        if self._image_ready:
            return self._image

        # Clear the image
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

        if self.vowel and self.vowel.vowel_type is VowelType.HIDDEN:
            self.vowel.draw(self._draw)
        self._draw_consonants()
        self._draw_inner_circle()
        if self.vowel and self.vowel.vowel_type is not VowelType.HIDDEN:
            self.vowel.draw(self._draw)

        # Paste the outer circle image
        self._image.paste(self._border_image, mask=self._mask_image)
        self._image_ready = True
        return self._image

    def _draw_consonants(self):
        for cons in self.consonants:
            cons.draw(self._draw)

    def _draw_inner_circle(self):
        for args in self._inner_circle_arg_dict:
            self._draw.ellipse(**args)

    def apply_color_changes(self):
        for consonant in self.consonants:
            consonant.update_argument_dictionaries()

        if self.vowel:
            self.vowel.update_argument_dictionaries()

        self._update_inner_circle_args()
        self._create_outer_circle()
        self._image_ready = False

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self, direction_sign: int, is_tail: bool):
        delta = direction_sign * 2 * math.pi / CYCLE

        if self.vowel:
            self.vowel.set_direction(self.vowel.direction - 2 * delta)

        for consonant in self.consonants:
            consonant.set_direction(consonant.direction + 2 * delta)

        if is_tail:
            self.set_direction(self.direction + delta)
        else:
            self._image_ready = False
