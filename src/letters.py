import math
import random
from abc import ABC, abstractmethod
from enum import auto, Enum
from typing import Optional, List

from PIL import ImageDraw

from utils import Point, line_width


class LetterType(Enum):
    """Enumeration to represent types of letters."""
    CONSONANT = auto()
    VOWEL = auto()


class Letter(ABC):
    """Abstract base class representing a generic letter."""

    def __init__(self, text: str, letter_type: LetterType, borders: str):
        """
        Initialize a Letter instance.

        :param text: The textual representation of the letter.
        :param letter_type: The type of the letter (CONSONANT/VOWEL).
        :param borders: A string representing the letter's border properties.
        """
        self.text = text
        self.letter_type = letter_type
        self.borders = borders
        self.parent_direction = 0.0
        self._set_personal_direction(random.uniform(0.9 * math.pi, 1.1 * math.pi))

        self.line_widths: List[float] = []
        self.half_line_widths: List[float] = []
        self._half_line_distance = 0.0
        self._image: Optional[ImageDraw.ImageDraw] = None

    def set_image(self, image: ImageDraw.ImageDraw):
        """Set the image object used for drawing."""
        self._image = image

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

    @abstractmethod
    def _update_image_properties(self):
        """Update properties necessary for drawing."""
        pass

    @abstractmethod
    def _update_syllable_properties(self, syllable):
        """
        Update the letter's properties based on the syllable.

        :param syllable: The syllable object containing scale and distances.
        """
        self.line_widths = [line_width(border, syllable.scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]
        self._half_line_distance = syllable.half_line_distance

        self.parent_direction = syllable.direction
        self.direction = self.parent_direction + self.personal_direction

    def _set_direction(self, direction: float):
        self.direction = direction
        self.personal_direction = self.direction - self.parent_direction

    def _set_personal_direction(self, personal_direction: float):
        self.personal_direction = personal_direction
        self.direction = self.parent_direction + self.personal_direction

    def update_properties(self, syllable):
        self._update_syllable_properties(syllable)
        self._update_image_properties()

    @abstractmethod
    def draw_decoration(self):
        """Draw additional decorations specific to the letter."""
        pass
