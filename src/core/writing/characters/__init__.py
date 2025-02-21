import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import auto, Enum
from itertools import repeat
from random import uniform

from ..common import Interactive
from ..common.circles import OuterCircle, InnerCircle
from ...utils import get_line_width, get_half_line_distance


class TokenType(Enum):
    """Enumeration to represent types of tokens."""
    SPACE = auto()
    WORD = auto()
    NUMBER = auto()
    PUNCTUATION = auto()


class CharacterType(Enum):
    """Enumeration to represent types of characters."""
    SPACE = (1, TokenType.SPACE)
    CONSONANT = (2, TokenType.WORD)
    VOWEL = (3, TokenType.WORD)
    SEPARATOR = (4, TokenType.WORD)
    DIGIT = (5, TokenType.NUMBER)
    NUMBER_MARK = (6, TokenType.NUMBER)
    PUNCTUATION_MARK = (7, TokenType.PUNCTUATION)

    def __init__(self, index: int, token_type: TokenType):
        """Initialize a character type with an index and a token type."""
        self.index = index
        self.token_type = token_type


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

    def __init__(self, text: str, character_type: CharacterType, borders: str):
        """Initialize a Letter instance."""
        super().__init__(text, character_type)
        self.borders = borders
        self.direction = 0.0
        self.parent_direction = 0.0
        self.personal_direction = 0.0
        self._set_personal_direction(uniform(0.9 * math.pi, 1.1 * math.pi))

        length = len(borders)
        self.line_widths = list(repeat(0, length))
        self.half_line_widths = list(repeat(0.0, length))
        self._half_line_distance = 0.0

    def initialize(self, direction: float, scale: float, outer_circle: OuterCircle, inner_circle: InnerCircle):
        """Initialize the letter's properties based on a given syllable."""
        self.set_parent_direction(direction)
        self.resize(scale, outer_circle, inner_circle)

    def _update_properties_after_resizing(self, scale: float, outer_circle: OuterCircle, inner_circle: InnerCircle):
        """Update letter properties after resizing based on the given syllable."""
        self.line_widths = [get_line_width(border, scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]
        self._half_line_distance = get_half_line_distance(scale)

    def _update_properties_after_rotation(self):
        """Update letter properties after rotation."""

    @abstractmethod
    def _update_argument_dictionaries(self):
        """Update the argument dictionaries used for rendering."""

    def apply_color_changes(self) -> None:
        """Apply color changes to the letter."""
        self._update_argument_dictionaries()

    def set_parent_direction(self, parent_direction: float):
        """Update the letter's direction based on the parent direction."""
        self.parent_direction = parent_direction
        self.direction = self.parent_direction + self.personal_direction
        self._update_properties_after_rotation()
        self._update_argument_dictionaries()

    def set_direction(self, direction: float):
        """Set a new direction for the letter."""
        self.direction = direction
        self.personal_direction = self.direction - self.parent_direction
        self._update_properties_after_rotation()
        self._update_argument_dictionaries()

    def _set_personal_direction(self, personal_direction: float):
        """Set a new personal direction for the letter."""
        self.personal_direction = personal_direction
        self.direction = self.parent_direction + self.personal_direction

    def resize(self, scale: float, outer_circle: OuterCircle, inner_circle: InnerCircle):
        """Resize the letter based on the given syllable."""
        self._update_properties_after_resizing(scale, outer_circle, inner_circle)
        self._update_argument_dictionaries()

    def perform_animation(self, angle: float):
        self.set_direction(self.direction + angle)
