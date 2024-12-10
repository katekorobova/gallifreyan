import json
import math
import random
import tkinter as tk
from typing import Dict, List, Tuple, Optional

from PIL import ImageTk, Image, ImageDraw

from consonants import Consonant
from letters import LetterType, Letter
from utils import Point, PressedType, line_width, half_line_distance, MIN_RADIUS, OUTER_CIRCLE_RADIUS, \
    WORD_IMAGE_RADIUS, WORD_COLOR, WORD_BG, WORD_INITIAL_SCALE_MIN, WORD_SCALE_MIN, \
    SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG, \
    SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX, SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX, \
    INNER_INITIAL_SCALE_MIN, INNER_INITIAL_SCALE_MAX, INNER_SCALE_MIN, INNER_SCALE_MAX
from vowels import Vowel, VowelDecoration


class WritingSystem:
    def __init__(self, consonant_file: str, vowel_file: str):
        self.consonant_table: List[List[str]] = []
        self.vowel_table: List[List[str]] = []
        self.consonants: Dict[str, Tuple[str, str]] = {}
        self.vowels: Dict[str, Tuple[str, str]] = {}
        self.letters: Dict[str, Tuple[LetterType, str, str]] = {}

        f = open(consonant_file, 'r', encoding='utf-8')
        data = json.loads(f.read())
        self.consonant_table = data['letters']
        self.consonant_borders = data['borders']
        self.consonant_decorations = data['decorations']
        # disabled = data['disabled']
        f.close()

        for i in range(len(self.consonant_table)):
            for j in range(len(self.consonant_table[i])):
                letter = self.consonant_table[i][j]
                self.consonants[letter] = self.consonant_borders[i], self.consonant_decorations[j]
                self.letters[letter] = LetterType.CONSONANT, self.consonant_borders[i], self.consonant_decorations[j]

        f = open(vowel_file, 'r', encoding='utf-8')
        data = json.loads(f.read())
        self.vowel_table = data['letters']
        self.vowel_borders = data['borders']
        self.vowel_decorations = data['decorations']
        # disabled = data['disabled']
        f.close()

        for i in range(len(self.vowel_table)):
            for j in range(len(self.vowel_table[i])):
                letter = self.vowel_table[i][j]
                self.vowels[letter] = self.vowel_borders[i], self.vowel_decorations[j]
                self.letters[letter] = LetterType.VOWEL, self.vowel_borders[i], self.vowel_decorations[j]


class Syllable:
    def __init__(self, cons1: Consonant, cons2: Optional[Consonant] = None, vowel: Optional[Vowel] = None):
        self.cons1, self.cons2, self.vowel = cons1, cons2, vowel
        self.direction = random.uniform(-math.pi, math.pi)
        self._parent_scale = 1.0
        self._personal_scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)

        self._inner: Optional[Consonant] = None
        self.offset = 0.0
        self._following: Optional[Syllable] = None
        self.consonants: List[Consonant] = []
        self.letters: List[Letter] = []
        self.text = ''
        self._update_syllable_properties()

        self.inner_scale = random.uniform(INNER_INITIAL_SCALE_MIN, INNER_INITIAL_SCALE_MAX)
        self.scale = 0.0
        self.outer_radius = 0.0
        self.inner_radius = 0.0
        self.half_line_distance = 0.0

        self._image_ready = False
        self._image = Image.new('RGBA', (2 * SYLLABLE_IMAGE_RADIUS, 2 * SYLLABLE_IMAGE_RADIUS))
        self._draw = ImageDraw.Draw(self._image)

        self._border_image = Image.new('RGBA', self._image.size)
        self._border_draw = ImageDraw.Draw(self._border_image)

        self._mask_image = Image.new('1', self._image.size)
        self._mask_draw = ImageDraw.Draw(self._mask_image)

        self._inner_circle_arg_dict: List[Dict] = []

        for letter in self.letters:
            letter.set_image(self._draw)
        self._update_image_properties()

        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Letter] = None
        self._bias: float | Point | None = None

    def _update_syllable_properties(self):
        self._inner = self.cons2 or self.cons1
        self.consonants = sorted(filter(None, (self.cons1, self.cons2)), key=lambda l: l.decoration_type.group)
        self.letters = list(filter(None, (self.cons1, self.cons2, self.vowel)))
        self.text = ''.join(map(lambda l: l.text, self.letters))

    def _update_image_properties(self):
        self.scale = self._parent_scale * self._personal_scale
        self.outer_radius = OUTER_CIRCLE_RADIUS * self.scale
        self.inner_radius = self.outer_radius * self.inner_scale
        self.half_line_distance = half_line_distance(self.scale)
        self.offset = ((len(self.cons1.borders) - 1) * self.half_line_distance,
                       (len(self._inner.borders) - 1) * self.half_line_distance)
        for letter in self.letters:
            letter.update_properties(self)

        if len(self._inner.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS - self.inner_radius - self._inner.half_line_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self.inner_radius + self._inner.half_line_widths[0]
            self._inner_circle_arg_dict = [{'xy': (left, left, right, right), 'outline': SYLLABLE_COLOR,
                                             'fill': SYLLABLE_BG, 'width': self._inner.line_widths[0]}]
        else:
            self._inner_circle_arg_dict = []
            radius = self.inner_radius + self.half_line_distance
            left = SYLLABLE_IMAGE_RADIUS - radius - self._inner.half_line_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + radius + self._inner.half_line_widths[0]
            self._inner_circle_arg_dict.append({'xy': (left, left, right, right), 'outline': SYLLABLE_COLOR,
                                                 'fill': SYLLABLE_BG, 'width': self._inner.line_widths[0]})

            radius = max(self.inner_radius - self.half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS - radius - self._inner.half_line_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + radius + self._inner.half_line_widths[1]
            self._inner_circle_arg_dict.append({'xy': (left, left, right, right), 'outline': SYLLABLE_COLOR,
                                                 'fill': SYLLABLE_BG, 'width': self._inner.line_widths[1]})

        self._create_outer_circle()
        self._image_ready = False

    def remove_starting_with(self, letter: Letter):
        if self.cons2 is letter:
            self.cons2 = None
            self.vowel = None
        elif self.vowel is letter:
            self.vowel = None
        else:
            raise ValueError(f'There is no letter {letter.text} in syllable {self.text}')
        self._update_syllable_properties()
        self._image_ready = False

    def add(self, letter: Letter):
        if isinstance(letter, Vowel):
            if self.vowel:
                return False
            self.vowel = letter
            letter.set_image(self._draw)
            letter.update_properties(self)
        elif isinstance(letter, Consonant):
            if self.cons2 or self.vowel or not Consonant.compatible(self.cons1, letter):
                return False
            self.cons2 = letter
            letter.set_image(self._draw)
            letter.update_properties(self)
        else:
            raise ValueError(f'No such letter type: {letter.letter_type} (letter={letter.text})')
        self._update_syllable_properties()
        self._image_ready = False
        return True

    def press(self, point: Point):
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        if radius > self.outer_radius + self.half_line_distance:
            return False
        if radius > self.outer_radius - self.half_line_distance:
            self.pressed_type = PressedType.BORDER
            self._bias = radius - self.outer_radius
            return True
        if self.vowel and self.vowel.decoration_type is not VowelDecoration.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self._pressed = self.vowel
            return True
        if self.inner_radius - self.half_line_distance < radius < self.inner_radius + self.half_line_distance:
            self.pressed_type = PressedType.INNER
            self._bias = radius - self.inner_radius
            return True
        if radius <= self.inner_radius - self.half_line_distance:
            self.pressed_type = PressedType.PARENT
            self._bias = point
            return True
        for cons in reversed(self.consonants):
            if cons.press(point):
                self.pressed_type = PressedType.CHILD
                self._pressed = cons
                return True
        if self.vowel and self.vowel.decoration_type is VowelDecoration.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self._pressed = self.vowel
            return True
        self.pressed_type = PressedType.PARENT
        self._bias = point
        return True

    def move(self, point: Point, radius=0.0):
        shifted = point.shift(-round(math.cos(self.direction) * radius),
                              -round(math.sin(self.direction) * radius))
        match self.pressed_type:
            case PressedType.INNER:
                new_radius = math.sqrt(shifted.x * shifted.x + shifted.y * shifted.y) - self._bias
                self.inner_scale = min(max(new_radius / self.outer_radius, INNER_SCALE_MIN), INNER_SCALE_MAX)
                self._update_image_properties()
            case PressedType.BORDER:
                new_radius = math.sqrt(shifted.x * shifted.x + shifted.y * shifted.y) - self._bias
                self._personal_scale = min(
                    max(new_radius / OUTER_CIRCLE_RADIUS / self._parent_scale, SYLLABLE_SCALE_MIN),
                    SYLLABLE_SCALE_MAX)
                self._update_image_properties()
                if self._following:
                    self._following.resize(self.scale)
            case PressedType.PARENT:
                if radius:
                    point = point - self._bias
                    self.direction = math.atan2(point.y, point.x)
                    self._update_image_properties()
            case PressedType.CHILD:
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

    def set_following(self, following):
        self._following = following

    def create_image(self) -> Image:
        if self._image_ready:
            return self._image
        # clear all
        self._draw.rectangle(((0, 0), self._image.size), fill=SYLLABLE_BG)
        if self.vowel and self.vowel.decoration_type is VowelDecoration.HIDDEN:
            self.vowel.draw_decoration()
        self._draw_cons_decoration()
        self._draw_inner_circle()
        if self.vowel and self.vowel.decoration_type is not VowelDecoration.HIDDEN:
            self.vowel.draw_decoration()
        # paste the outer circle image
        self._image.paste(self._border_image, mask=self._mask_image)
        self._image_ready = True
        return self._image

    def _draw_cons_decoration(self):
        for cons in self.consonants:
            cons.draw_decoration()

    def _draw_inner_circle(self):
        for args in self._inner_circle_arg_dict:
            self._draw.ellipse(**args)

    def _create_outer_circle(self):
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._mask_image.size), fill=1)
        if len(self.cons1.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS - self.outer_radius - self.cons1.half_line_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self.outer_radius + self.cons1.half_line_widths[0]
            self._border_draw.ellipse((left, left, right, right),
                                      outline=SYLLABLE_COLOR, width=self.cons1.line_widths[0])
            self._mask_draw.ellipse((left, left, right, right),
                                    outline=1, fill=0, width=self.cons1.line_widths[0])

        else:
            radius = self.outer_radius + self.half_line_distance
            left = SYLLABLE_IMAGE_RADIUS - radius - self.cons1.half_line_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + radius + self.cons1.half_line_widths[0]
            self._border_draw.ellipse((left, left, right, right),
                                      outline=SYLLABLE_COLOR, fill=SYLLABLE_BG, width=self.cons1.line_widths[0])

            radius = max(self.outer_radius - self.half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS - radius - self.cons1.half_line_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + radius + self.cons1.half_line_widths[1]
            self._border_draw.ellipse((left, left, right, right),
                                      outline=SYLLABLE_COLOR, width=self.cons1.line_widths[1])
            self._mask_draw.ellipse((left, left, right, right),
                                    outline=1, fill=0, width=self.cons1.line_widths[1])


class Word:
    def __init__(self, center: Point, syllables: List[Syllable]):
        self.center = center
        self.outer_radius = 0.0
        self.borders = '21'
        self._widths: List[float] = []
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

        self._image = Image.new('RGBA', (2 * WORD_IMAGE_RADIUS, 2 * WORD_IMAGE_RADIUS))
        self._draw = ImageDraw.Draw(self._image)

        self._border_image = Image.new('RGBA', self._image.size)
        self._border_draw = ImageDraw.Draw(self._border_image)

        self._mask_image = Image.new('1', self._image.size)
        self._mask_draw = ImageDraw.Draw(self._mask_image)

        self._image_tk = ImageTk.PhotoImage(image=self._image.mode, size=self._image.size)
        self._update_image_properties()

        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Syllable] = None
        self._bias: float | Point | None = None

    def _update_image_properties(self):
        self.outer_radius = OUTER_CIRCLE_RADIUS * self.scale
        self._widths = list(map(lambda x: line_width(x, self.scale), self.borders))
        self._half_widths = list(map(lambda x: x / 2, self._widths))
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
                    self._bias = point - self.center
                else:
                    self.pressed_type = PressedType.CHILD
                    self._pressed = self.first
                return True
            else:
                return False
        else:
            radius = math.sqrt(word_point.x * word_point.x + word_point.y * word_point.y)
            if radius > self.outer_radius + self._half_line_distance:
                return False
            if radius > self.outer_radius - self._half_line_distance:
                self.pressed_type = PressedType.BORDER
                self._bias = radius - self.outer_radius
                return True

            first_radius = self.first.outer_radius
            for syllable in reversed(self.rest):
                if syllable.press(word_point.shift(-round(math.cos(syllable.direction) * first_radius),
                                                   -round(math.sin(syllable.direction) * first_radius))):
                    self.pressed_type = PressedType.CHILD
                    self._pressed = syllable
                    return True

            if self.first.press(word_point):
                if self.first.pressed_type == PressedType.PARENT:
                    self.pressed_type = PressedType.PARENT
                    self._bias = point - self.center
                else:
                    self.pressed_type = PressedType.CHILD
                    self._pressed = self.first
                return True

            self.pressed_type = PressedType.PARENT
            self._bias = point - self.center
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
                new_radius = math.sqrt(word_point.x * word_point.x + word_point.y * word_point.y) - self._bias
                self.scale = min(max(new_radius / OUTER_CIRCLE_RADIUS, WORD_SCALE_MIN), 1)
                self._update_image_properties()
                self.first.resize(self.scale)
            case PressedType.PARENT:
                self.center = point - self._bias

    def create_image(self, canvas: tk.Canvas):
        if not self.rest:
            self._draw.rectangle(((0, 0), self._image.size), fill=0)
            image = self.first.create_image()
            self._image.paste(image, (WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS,
                                      WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS), image)
            self._image_tk.paste(self._image)
            canvas.create_image(self.center.x, self.center.y, image=self._image_tk)
        else:
            # clear all
            self._draw.rectangle(((0, 0), self._image.size), fill=WORD_BG)
            image = self.first.create_image()
            self._image.paste(image, (WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS,
                                      WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS), image)
            first_radius = self.first.scale * OUTER_CIRCLE_RADIUS
            for s in self.rest:
                image = s.create_image()
                self._image.paste(image, (
                    round(math.cos(s.direction) * first_radius) + WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS,
                    round(math.sin(s.direction) * first_radius) + WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS), image)

            # paste the outer circle image
            self._image.paste(self._border_image, mask=self._mask_image)
            self._image_tk.paste(self._image)
            canvas.create_image(self.center.x, self.center.y, image=self._image_tk)

    def _create_outer_circle(self):
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._border_image.size), fill=1)
        if len(self.borders) == 1:
            left = WORD_IMAGE_RADIUS - self.outer_radius - self._half_widths[0]
            right = WORD_IMAGE_RADIUS + self.outer_radius + self._half_widths[0]
            self._border_draw.ellipse((left, left, right, right), outline=WORD_COLOR, width=self._widths[0])
            self._mask_draw.ellipse((left, left, right, right), outline=1, fill=0, width=self._widths[0])
        else:
            radius = self.outer_radius + self._half_line_distance
            left = WORD_IMAGE_RADIUS - radius - self._half_widths[0]
            right = WORD_IMAGE_RADIUS + radius + self._half_widths[0]
            self._border_draw.ellipse((left, left, right, right),
                                      outline=WORD_COLOR, fill=WORD_BG, width=self._widths[0])

            radius = max(self.outer_radius - self._half_line_distance, MIN_RADIUS)
            left = WORD_IMAGE_RADIUS - radius - self._half_widths[1]
            right = WORD_IMAGE_RADIUS + radius + self._half_widths[1]
            self._border_draw.ellipse((left, left, right, right), outline=WORD_COLOR, width=self._widths[1])
            self._mask_draw.ellipse((left, left, right, right), outline=1, fill=0, width=self._widths[1])
