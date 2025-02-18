import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import auto, IntFlag
from itertools import repeat

from PIL import ImageDraw

from .circles import OuterCircle, InnerCircle
from ..tools import AnimationProperties
from ..utils import Point, get_line_width, get_half_line_distance
from ...config import SYLLABLE_IMAGE_RADIUS


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

class Separator(Character):
    """Class representing a syllable separator character."""

    def __init__(self, text: str):
        """Initialize a Separator instance."""
        super().__init__(text, CharacterType.SEPARATOR)


class Space(Character):
    """Class representing a space character."""

    def __init__(self, text: str):
        """Initialize a Separator instance."""
        super().__init__(text, CharacterType.SPACE)


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