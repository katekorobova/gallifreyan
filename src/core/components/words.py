import math
import random
import tkinter as tk
from typing import List, Optional

from PIL import ImageTk, Image, ImageDraw

from src.utils import (
    Point, PressedType, line_width, half_line_distance, MIN_RADIUS, OUTER_CIRCLE_RADIUS,
    WORD_IMAGE_RADIUS, WORD_COLOR, WORD_BG, WORD_INITIAL_SCALE_MIN, WORD_SCALE_MIN
)
from .syllables import Syllable


class Word:
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)

    def __init__(self, center: Point, syllables: List[Syllable]):
        self.center = center
        self.borders = '21'
        self.outer_radius = 0.0
        self._widths: List[int] = []
        self._half_widths: List[float] = []

        # Initialize syllables and their relationships
        for i in reversed(range(len(syllables) - 1)):
            syllables[i].set_following(syllables[i + 1])
        syllables[-1].set_following(None)

        self.first = syllables[0]
        self.rest = syllables[1:]
        self.scale = random.uniform(WORD_INITIAL_SCALE_MIN, 1) if self.rest else 1
        self.first.resize(self.scale)
        self.syllables = syllables
        self.text = ''.join(s.text for s in syllables)

        # Image-related attributes
        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')
        self._image_tk = ImageTk.PhotoImage(image=self._image)
        self._update_image_properties()

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Syllable] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    @classmethod
    def _create_empty_image(cls, mode='RGBA') -> tuple[Image.Image, ImageDraw.Draw]:
        """Create an empty image and its drawing object."""
        image = Image.new(mode, (cls.IMAGE_CENTER * 2))
        return image, ImageDraw.Draw(image)

    def _update_image_properties(self):
        """Update properties based on scale and border widths."""
        self.outer_radius = OUTER_CIRCLE_RADIUS * self.scale
        self._widths = [line_width(border, self.scale) for border in self.borders]
        self._half_widths = [width / 2 for width in self._widths]
        self._half_line_distance = half_line_distance(self.scale)
        self._create_outer_circle()

    def set_syllables(self, syllables: List[Syllable]):
        for i in reversed(range(0, len(syllables) - 1)):
            syllables[i].set_following(syllables[i + 1])
        syllables[-1].set_following(None)
        self.first = syllables[0]
        self.rest = syllables[1:]
        self.first.resize(self.scale)
        if not self.rest:
            self.first.resize(parent_scale=1, personal_scale=self.scale)
            self.scale = 1
            self._update_image_properties()
        self.syllables = syllables
        self.text = ''.join(map(lambda s: s.text, syllables))

    def press(self, point: Point) -> bool:
        """Handle press events."""
        word_point = point - self.center

        if self.rest:
            distance = word_point.distance()

            # Check if the press is outside the outer boundary
            if distance > self.outer_radius + self._half_line_distance:
                return False

            # Check if the press is on the outer border
            if distance > self.outer_radius - self._half_line_distance:
                self._handle_outer_border_press(distance)
                return True

            # Handle press if it is on a syllable
            for syllable in reversed(self.rest):
                if self._handle_child_press(syllable, word_point):
                    return True

            # Handle press if it is on the first syllable
            if self._handle_first_child_press(word_point):
                return True

            # Handle press events for the parent
            self._handle_parent_press(word_point)
            return True
        else:
            return self._handle_first_child_press(word_point)

    def _handle_outer_border_press(self, distance: float) -> None:
        """Handle press events on the outer border."""
        self.pressed_type = PressedType.BORDER
        self._distance_bias = distance - self.outer_radius

    def _handle_child_press(self, syllable: Syllable, word_point: Point) -> bool:
        """Attempt to press a child syllable."""
        first_radius = self.first.outer_radius
        offset_point = word_point - Point(math.cos(syllable.direction) * first_radius,
                                          math.sin(syllable.direction) * first_radius)
        if syllable.press(offset_point):
            self.pressed_type = PressedType.CHILD
            self._pressed = syllable
            return True
        return False

    def _handle_first_child_press(self, word_point: Point) -> bool:
        """Attempt to press the first child syllable."""
        if self.first.press(word_point):
            if self.first.pressed_type == PressedType.PARENT:
                self.pressed_type = PressedType.PARENT
                self._point_bias = word_point
            else:
                self.pressed_type = PressedType.CHILD
                self._pressed = self.first
            return True

    def _handle_parent_press(self, word_point: Point) -> None:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = word_point

    def move(self, point: Point):
        """Handle move events."""
        word_point = point - self.center
        match self.pressed_type:
            case PressedType.CHILD:
                self._move_child(word_point)
            case PressedType.BORDER:
                self._resize_word(word_point)
            case PressedType.PARENT:
                self.center = point - self._point_bias

    def _move_child(self, word_point: Point):
        """Move a pressed child syllable."""
        if self._pressed is self.first:
            self.first.move(word_point)
        else:
            first_radius = self.first.outer_radius
            self._pressed.move(word_point, first_radius)

    def _resize_word(self, word_point: Point):
        """Resize the word based on movement."""
        new_radius = word_point.distance() - self._distance_bias
        self.scale = min(max(new_radius / OUTER_CIRCLE_RADIUS, WORD_SCALE_MIN), 1)
        self._update_image_properties()
        self.first.resize(self.scale)

    def create_image(self, canvas: tk.Canvas):
        """Create and display the word image on the canvas."""

        if self.rest:
            # Clear the image
            self._draw.rectangle(((0, 0), self._image.size), fill=WORD_BG)

            # Paste the first syllable onto the image
            self._paste_first()

            # Paste other syllables onto the image
            first_syllable_radius = self.first.scale * OUTER_CIRCLE_RADIUS
            for s in self.rest:
                self._paste_rest(s, first_syllable_radius)

            # Paste the outer circle image
            self._image.paste(self._border_image, mask=self._mask_image)
        else:
            # Clear the image
            self._draw.rectangle(((0, 0), self._image.size), fill=0)

            # Paste the first syllable onto the image
            self._paste_first()

        self._image_tk.paste(self._image)
        canvas.create_image(self.center, image=self._image_tk)

    def _paste_first(self):
        image = self.first.create_image()
        self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER), image)

    def _paste_rest(self, syllable: Syllable, radius: float):
        image = syllable.create_image()
        self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER +
                                       Point(round(math.cos(syllable.direction) * radius),
                                             round(math.sin(syllable.direction) * radius))), image)

    def _create_outer_circle(self):
        """Create the outer circle representation."""

        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._border_image.size), fill=1)
        if len(self.borders) == 1:
            adjusted_radius = self.outer_radius + self._half_widths[0]
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=WORD_COLOR, width=self._widths[0])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self._widths[0])
        else:
            adjusted_radius = self.outer_radius + self._half_line_distance + self._half_widths[0]
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=WORD_COLOR, fill=WORD_BG, width=self._widths[0])

            adjusted_radius = max(self.outer_radius - self._half_line_distance + self._half_widths[1], MIN_RADIUS)
            start = self.IMAGE_CENTER.shift(-adjusted_radius)
            end = self.IMAGE_CENTER.shift(adjusted_radius)
            self._border_draw.ellipse((start, end), outline=WORD_COLOR, width=self._widths[1])
            self._mask_draw.ellipse((start, end), outline=1, fill=0, width=self._widths[1])
