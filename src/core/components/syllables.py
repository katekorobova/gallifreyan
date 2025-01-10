import math
import random
from abc import ABC
from typing import Optional

from PIL import Image, ImageDraw

from .consonants import Consonant
from .characters import Letter, Separator, Character
from .vowels import Vowel, VowelType
from ..utils import Point, PressedType, half_line_distance
from ...config import (MIN_RADIUS, OUTER_CIRCLE_RADIUS,
                       SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG, SYLLABLE_INITIAL_SCALE_MIN,
                       SYLLABLE_INITIAL_SCALE_MAX, SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX, INNER_INITIAL_SCALE_MIN,
                       INNER_INITIAL_SCALE_MAX, INNER_SCALE_MIN, INNER_SCALE_MAX)


class AbstractSyllable(ABC):

    def __init__(self, head: Character):
        self.head = head
        self.text = head.text

    def remove_starting_with(self, _: Character) -> None:
        """
        Remove a character from the syllable, updating properties accordingly.
        """
        pass

    def add(self, _: Character) -> bool:
        """
        Add a character to the syllable, if valid.
        """
        return False


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
            self._update_syllable_properties()

    def add(self, character: Character) -> bool:
        """
        Add a character to the syllable, if valid.
        """
        if isinstance(character, Separator):
            self.characters.append(character)
            self._update_syllable_properties()
            return True
        else:
            return False

    def _update_syllable_properties(self):
        self.text = ''.join(char.text for char in self.characters)


class Syllable(AbstractSyllable):
    """
    Represents a syllable, combining consonants and vowels into structured elements with visual representation.
    """
    IMAGE_CENTER = Point(SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS)

    def __init__(self, cons1: Consonant, vowel: Vowel = None):
        # Core attributes
        super().__init__(cons1)
        self.cons1, self.vowel = cons1, vowel
        self.cons2 = None
        self._following: Optional[Syllable] = None
        self._inner: Optional[Consonant] = None
        self.consonants: list[Consonant] = []
        self.letters: list[Letter] = []

        # Scale, radius, and positioning attributes
        self._parent_scale = 1.0
        self._personal_scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self.inner_scale = random.uniform(INNER_INITIAL_SCALE_MIN, INNER_INITIAL_SCALE_MAX)
        self.scale = 0.0
        self.direction = random.uniform(-math.pi, math.pi)
        self.outer_radius = 0.0
        self.inner_radius = 0.0
        self.half_line_distance = 0.0
        self.border_offset = (0.0, 0.0)

        # Image-related attributes
        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')
        self._inner_circle_arg_dict: list[dict] = []
        self._image_ready = False

        self._initialize_letters()
        self._update_image_properties()

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Letter] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    @classmethod
    def _create_empty_image(cls, mode: str = 'RGBA') -> tuple[Image.Image, ImageDraw.Draw]:
        """Create an empty image with the specified mode."""
        image = Image.new(mode, (cls.IMAGE_CENTER * 2))
        return image, ImageDraw.Draw(image)

    def _initialize_letters(self):
        """Initialize the letters, setting their image properties."""
        self._update_syllable_properties()
        for letter in self.letters:
            letter.set_image(self._draw)

    def _update_syllable_properties(self):
        """Update syllable properties such as consonants, letters, and text representation."""
        self._inner = self.cons2 or self.cons1
        self.consonants = sorted(filter(None, (self.cons1, self.cons2)), key=lambda l: l.consonant_type.group)
        self.letters = list(filter(None, (self.cons1, self.cons2, self.vowel)))
        self.text = ''.join(letter.text for letter in self.letters)

    @staticmethod
    def _calculate_adjusted_radius(base_radius: float, adjustment: float, min_radius: float = MIN_RADIUS):
        """Calculate an adjusted radius with constraints."""
        return max(base_radius + adjustment, min_radius)

    def _update_image_properties(self):
        """Update scaling and circle radii, and calculate image properties."""
        self.scale = self._parent_scale * self._personal_scale
        self.outer_radius = OUTER_CIRCLE_RADIUS * self.scale
        self.inner_radius = self.outer_radius * self.inner_scale
        self.half_line_distance = half_line_distance(self.scale)
        self.border_offset = ((len(self.cons1.borders) - 1) * self.half_line_distance,
                              (len(self._inner.borders) - 1) * self.half_line_distance)

        for letter in self.letters:
            letter.update_properties(self)

        self._update_inner_circle_args()
        self._create_outer_circle()
        self._image_ready = False

    def _update_inner_circle_args(self):
        """Prepare arguments for drawing inner circles."""
        self._inner_circle_arg_dict = []
        if len(self._inner.borders) == 1:
            adjusted_radius = self._calculate_adjusted_radius(self.inner_radius, self._inner.half_line_widths[0])
            self._inner_circle_arg_dict.append(self._create_circle_args(adjusted_radius, self._inner.line_widths[0]))
        else:
            for i in range(2):
                adjusted_radius = self._calculate_adjusted_radius(
                    self.inner_radius, (-1) ** i * self.half_line_distance + self._inner.half_line_widths[i]
                )
                self._inner_circle_arg_dict.append(
                    self._create_circle_args(adjusted_radius, self._inner.line_widths[i]))

    def _create_circle_args(self, adjusted_radius: float, line_width: float) -> dict:
        """Generate circle arguments for drawing."""
        start, end = self.IMAGE_CENTER.shift(-adjusted_radius), self.IMAGE_CENTER.shift(adjusted_radius)
        return {'xy': (start, end), 'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': line_width}

    def _create_outer_circle(self):
        """Draw the outer circle for the syllable."""
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._mask_image.size), fill=1)

        if len(self.cons1.borders) == 1:
            adjusted_radius = self._calculate_adjusted_radius(self.outer_radius, self.cons1.half_line_widths[0])
            start, end = self.IMAGE_CENTER.shift(-adjusted_radius), self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=SYLLABLE_COLOR, width=self.cons1.line_widths[0])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self.cons1.line_widths[0])
        else:
            adjusted_radius = self.outer_radius + self.half_line_distance + self.cons1.half_line_widths[0]
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end),
                                      outline=SYLLABLE_COLOR, fill=SYLLABLE_BG, width=self.cons1.line_widths[0])

            adjusted_radius = max(
                self.outer_radius - self.half_line_distance + self.cons1.half_line_widths[1], MIN_RADIUS)
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=SYLLABLE_COLOR, width=self.cons1.line_widths[1])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self.cons1.line_widths[1])

    def set_following(self, following) -> None:
        self._following = following

    def remove_starting_with(self, character: Character):
        """Remove a letter from the syllable, updating properties accordingly."""
        if character == self.cons2:
            self.cons2, self.vowel = None, None
        elif character == self.vowel:
            self.vowel = None
        else:
            raise ValueError(f'Letter {character.text} not found in syllable {self.text}')
        self._update_syllable_properties()
        self._image_ready = False

    def add(self, character: Character) -> bool:
        """Add a letter to the syllable, if valid."""
        if isinstance(character, Vowel) and not self.vowel:
            self.vowel = character
        elif isinstance(character, Consonant) \
                and not self.cons2 and not self.vowel:
            # and not self.cons2 and not self.vowel and Consonant.compatible(self.cons1, character):
            self.cons2 = character
        else:
            return False

        character.set_image(self._draw)
        character.update_properties(self)
        self._update_syllable_properties()
        self._image_ready = False
        return True

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

    def move(self, point: Point, radius=0.0):
        shifted = point - Point(math.cos(self.direction) * radius, math.sin(self.direction) * radius)
        distance = shifted.distance()

        match self.pressed_type:
            case PressedType.INNER:
                self._adjust_inner_scale(distance)
            case PressedType.BORDER:
                self._adjust_border_scale(distance)
            case PressedType.PARENT:
                if radius:
                    self._adjust_direction(point)
            case PressedType.CHILD:
                self._move_child(shifted)

    def _adjust_inner_scale(self, distance: float):
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.inner_scale = min(max(new_radius / self.outer_radius, INNER_SCALE_MIN), INNER_SCALE_MAX)
        self._update_image_properties()

    def _adjust_border_scale(self, distance: float):
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self._personal_scale = min(
            max(new_radius / OUTER_CIRCLE_RADIUS / self._parent_scale, SYLLABLE_SCALE_MIN),
            SYLLABLE_SCALE_MAX)
        self._update_image_properties()
        if self._following:
            self._following.resize(self.scale)

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the syllable when moved."""
        adjusted_point = point - self._point_bias
        self.direction = adjusted_point.direction()
        self._update_image_properties()

    def _move_child(self, shifted: Point):
        """Move the pressed child element."""
        self._pressed.move(shifted)
        self._image_ready = False

    def resize(self, parent_scale: float = None, personal_scale: float = None):
        if parent_scale is not None:
            self._parent_scale = parent_scale
        if personal_scale is not None:
            self._personal_scale = max(self._personal_scale * personal_scale, SYLLABLE_SCALE_MIN)
        self._update_image_properties()

        if self._following:
            self._following.resize(self.scale)

    def create_image(self) -> Image:
        """Render the syllable image."""
        if self._image_ready:
            return self._image

        # Clear the image
        self._draw.rectangle(((0, 0), self._image.size), fill=SYLLABLE_BG)

        if self.vowel and self.vowel.vowel_type is VowelType.HIDDEN:
            self.vowel.draw()
        self._draw_consonants()
        self._draw_inner_circle()
        if self.vowel and self.vowel.vowel_type is not VowelType.HIDDEN:
            self.vowel.draw()

        # Paste the outer circle image
        self._image.paste(self._border_image, mask=self._mask_image)
        self._image_ready = True
        return self._image

    def _draw_consonants(self):
        for cons in self.consonants:
            cons.draw()

    def _draw_inner_circle(self):
        for args in self._inner_circle_arg_dict:
            self._draw.ellipse(**args)
