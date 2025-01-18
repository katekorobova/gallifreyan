import math
import random
from abc import ABC, abstractmethod
from enum import auto, Enum

from PIL import ImageDraw

from ..utils import Point, line_width
from ...config import SYLLABLE_IMAGE_RADIUS


class CharacterType(Enum):
    """Enumeration to represent types of letters."""
    LETTER = auto()
    SEPARATOR = auto()
    SPACE = auto()


class Character(ABC):
    def __init__(self, text: str, character_type: CharacterType):
        """
        Initialize a Character instance.

        :param text: The textual representation of the character.
        :param character_type: The type of the character.
        """
        self.text = text
        self.character_type = character_type


class Separator(Character):
    def __init__(self, text: str):
        """
        Initialize a Separator instance.

        :param text: The textual representation of the separator.
        """
        super().__init__(text, CharacterType.SEPARATOR)


class Space(Character):
    def __init__(self, text: str):
        """
        Initialize a Separator instance.

        :param text: The textual representation of the separator.
        """
        super().__init__(text, CharacterType.SPACE)


class LetterType(Enum):
    """Enumeration to represent types of letters."""
    CONSONANT = auto()
    VOWEL = auto()


class Letter(Character):
    """Abstract base class representing a generic letter."""
    IMAGE_CENTER = Point(SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS)

    def __init__(self, text: str, letter_type: LetterType, borders: str):
        """
        Initialize a Letter instance.

        :param text: The textual representation of the letter.
        :param letter_type: The type of the letter (CONSONANT/VOWEL).
        :param borders: A string representing the letter's border properties.
        """
        super().__init__(text, CharacterType.LETTER)
        self.letter_type = letter_type
        self.borders = borders
        self.direction = 0.0
        self.parent_direction = 0.0
        self.personal_direction = 0.0
        self._set_personal_direction(random.uniform(0.9 * math.pi, 1.1 * math.pi))

        self.line_widths: list[int] = []
        self.half_line_widths: list[float] = []
        self._half_line_distance = 0.0

    def initialize(self, syllable):
        """Set the image object used for drawing."""
        self.update_direction(syllable.direction)
        self.resize(syllable)

    @abstractmethod
    def press(self, point: Point) -> bool:
        """
        Handle a press event at a given point.

        :param point: The point where the press occurred.
        :return: A boolean indicating whether the press was handled.
        """
        pass

    @abstractmethod
    def move(self, point: Point):
        """
        Handle a move event to a given point.

        :param point: The new point to move to.
        """
        pass

    def _update_properties_after_resizing(self, syllable):
        """
        Update properties after syllable resizing.
        """
        self.line_widths = [line_width(border, syllable.scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]
        self._half_line_distance = syllable.half_line_distance

    def _update_properties_after_rotation(self):
        """Update properties after rotation."""
        pass

    @abstractmethod
    def update_argument_dictionaries(self):
        """Update argument dictionaries."""
        pass

    def update_direction(self, parent_direction: float):
        self.parent_direction = parent_direction
        self.direction = self.parent_direction + self.personal_direction
        self._update_properties_after_rotation()
        self.update_argument_dictionaries()

    def set_direction(self, direction: float):
        self.direction = direction
        self.personal_direction = self.direction - self.parent_direction
        self._update_properties_after_rotation()
        self.update_argument_dictionaries()

    def _set_personal_direction(self, personal_direction: float):
        self.personal_direction = personal_direction
        self.direction = self.parent_direction + self.personal_direction

    def resize(self, syllable):
        self._update_properties_after_resizing(syllable)
        self.update_argument_dictionaries()

    @abstractmethod
    def draw(self, image: ImageDraw.Draw):
        """Draw the letter."""
        pass
