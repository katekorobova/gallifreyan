import math
import random
import tkinter as tk
from typing import List, Optional

from PIL import ImageTk, Image, ImageDraw

from src.utils import Point, PressedType, line_width, half_line_distance, MIN_RADIUS, OUTER_CIRCLE_RADIUS, \
    WORD_IMAGE_RADIUS, WORD_COLOR, WORD_BG, WORD_INITIAL_SCALE_MIN, WORD_SCALE_MIN
from .syllables import Syllable


class Word:
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)

    def __init__(self, center: Point, syllables: List[Syllable]):
        self.center = center
        self.outer_radius = 0.0
        self.borders = '21'
        self._widths: List[int] = []
        self._half_widths: List[float] = []
        self._half_line_distance = 0.0

        for i in reversed(range(0, len(syllables) - 1)):
            syllables[i].set_following(syllables[i + 1])
        syllables[-1].set_following(None)

        self.first = syllables[0]
        self.rest = syllables[1:]
        if self.rest:
            self.scale = random.uniform(WORD_INITIAL_SCALE_MIN, 1)
        else:
            self.scale = 1
        self.first.resize(self.scale)
        self.syllables = syllables
        self.text = ''.join(map(lambda s: s.text, syllables))

        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')

        self._image_tk = ImageTk.PhotoImage(image=self._image.mode, size=self._image.size)
        self._update_image_properties()

        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Syllable] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    @classmethod
    def _create_empty_image(cls, mode='RGBA') -> tuple[Image.Image, ImageDraw.Draw]:
        """Creates an empty image and its corresponding drawing object."""
        image = Image.new(mode, (cls.IMAGE_CENTER * 2))
        return image, ImageDraw.Draw(image)

    def _update_image_properties(self):
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

    def press(self, point: Point):
        word_point = point - self.center
        if not len(self.rest):
            if self.first.press(word_point):
                if self.first.pressed_type == PressedType.PARENT:
                    self.pressed_type = PressedType.PARENT
                    self._point_bias = point - self.center
                else:
                    self.pressed_type = PressedType.CHILD
                    self._pressed = self.first
                return True
            else:
                return False
        else:
            distance = word_point.distance()
            if distance > self.outer_radius + self._half_line_distance:
                return False
            if distance > self.outer_radius - self._half_line_distance:
                self.pressed_type = PressedType.BORDER
                self._point_bias = distance - self.outer_radius
                return True

            first_radius = self.first.outer_radius
            for syllable in reversed(self.rest):
                if syllable.press(word_point - Point(math.cos(syllable.direction) * first_radius,
                                                     math.sin(syllable.direction) * first_radius)):
                    self.pressed_type = PressedType.CHILD
                    self._pressed = syllable
                    return True

            if self.first.press(word_point):
                if self.first.pressed_type == PressedType.PARENT:
                    self.pressed_type = PressedType.PARENT
                    self._point_bias = point - self.center
                else:
                    self.pressed_type = PressedType.CHILD
                    self._pressed = self.first
                return True

            self.pressed_type = PressedType.PARENT
            self._point_bias = point - self.center
            return True

    def move(self, point: Point):
        word_point = point - self.center
        match self.pressed_type:
            case PressedType.CHILD:
                if self._pressed is self.first:
                    self.first.move(word_point)
                else:
                    first_radius = self.first.outer_radius
                    self._pressed.move(word_point, first_radius)
            case PressedType.BORDER:
                new_radius = word_point.distance() - self._distance_bias
                self.scale = min(max(new_radius / OUTER_CIRCLE_RADIUS, WORD_SCALE_MIN), 1)
                self._update_image_properties()
                self.first.resize(self.scale)
            case PressedType.PARENT:
                self.center = point - self._point_bias

    def create_image(self, canvas: tk.Canvas):
        if not self.rest:
            self._draw.rectangle(((0, 0), self._image.size), fill=0)
            image = self.first.create_image()
            self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER), image)
            self._image_tk.paste(self._image)
            canvas.create_image(self.center, image=self._image_tk)
        else:
            # clear all
            self._draw.rectangle(((0, 0), self._image.size), fill=WORD_BG)
            image = self.first.create_image()
            self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER), image)
            first_radius = self.first.scale * OUTER_CIRCLE_RADIUS
            for s in self.rest:
                image = s.create_image()
                self._image.paste(image, tuple(self.IMAGE_CENTER - Syllable.IMAGE_CENTER +
                                               Point(round(math.cos(s.direction) * first_radius),
                                                     round(math.sin(s.direction) * first_radius))), image)

            # paste the outer circle image
            self._image.paste(self._border_image, mask=self._mask_image)
            self._image_tk.paste(self._image)
            canvas.create_image(self.center, image=self._image_tk)

    def _create_outer_circle(self):
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
