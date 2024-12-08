import json
import math
import random
import tkinter as tk
from typing import Dict, List, Tuple

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

        self.consonant_table: List[List[str]]
        self.vowel_table: List[List[str]]
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
    def __init__(self, cons1: Consonant, cons2: Consonant = None, vowel: Vowel = None):
        self.cons1, self.cons2, self.vowel = cons1, cons2, vowel
        self.direction = random.uniform(-math.pi, math.pi)
        self.__parent_scale = 1
        self.__personal_scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)

        self.__inner: Consonant | None = None
        self.offset, self.__following = None, None
        self.consonants: List[Consonant] = []
        self.letters: List[Letter] = []
        self.text = ''
        self.__update_syllable_properties()

        self.inner_scale = random.uniform(INNER_INITIAL_SCALE_MIN, INNER_INITIAL_SCALE_MAX)
        self.scale, self.outer_radius, self.inner_radius = None, None, None
        self.half_line_distance = None

        self.__image_ready = False
        self.__image = Image.new('RGBA', (2 * SYLLABLE_IMAGE_RADIUS, 2 * SYLLABLE_IMAGE_RADIUS))
        self.__draw = ImageDraw.Draw(self.__image)

        self.__border_image = Image.new('RGBA', self.__image.size)
        self.__border_draw = ImageDraw.Draw(self.__border_image)

        self.__mask_image = Image.new('1', self.__image.size)
        self.__mask_draw = ImageDraw.Draw(self.__mask_image)

        self.__inner_circle_arg_dict: List[Dict] = []

        for letter in self.letters:
            letter.set_image(self.__draw)
        self.__update_image_properties()

        self.pressed_type: PressedType | None = None
        self.__pressed: Letter | None = None
        self.__bias = None

    def __update_syllable_properties(self):
        self.__inner = self.cons2 or self.cons1
        self.consonants = sorted(filter(None, (self.cons1, self.cons2)), key=lambda l: l.decoration_type.group)
        self.letters = list(filter(None, (self.cons1, self.cons2, self.vowel)))
        self.text = ''.join(map(lambda l: l.text, self.letters))

    def __update_image_properties(self):
        self.scale = self.__parent_scale * self.__personal_scale
        self.outer_radius = OUTER_CIRCLE_RADIUS * self.scale
        self.inner_radius = self.outer_radius * self.inner_scale
        self.half_line_distance = half_line_distance(self.scale)
        self.offset = ((len(self.cons1.borders) - 1) * self.half_line_distance,
                       (len(self.__inner.borders) - 1) * self.half_line_distance)
        for letter in self.letters:
            letter.update_syllable_properties(self)

        if len(self.__inner.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS - self.inner_radius - self.__inner.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self.inner_radius + self.__inner.half_widths[0]
            self.__inner_circle_arg_dict = [{'xy': (left, left, right, right), 'outline': SYLLABLE_COLOR,
                                             'fill': SYLLABLE_BG, 'width': self.__inner.widths[0]}]
        else:
            self.__inner_circle_arg_dict = []
            radius = self.inner_radius + self.half_line_distance
            left = SYLLABLE_IMAGE_RADIUS - radius - self.__inner.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + radius + self.__inner.half_widths[0]
            self.__inner_circle_arg_dict.append({'xy': (left, left, right, right), 'outline': SYLLABLE_COLOR,
                                                 'fill': SYLLABLE_BG, 'width': self.__inner.widths[0]})

            radius = max(self.inner_radius - self.half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS - radius - self.__inner.half_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + radius + self.__inner.half_widths[1]
            self.__inner_circle_arg_dict.append({'xy': (left, left, right, right), 'outline': SYLLABLE_COLOR,
                                                 'fill': SYLLABLE_BG, 'width': self.__inner.widths[1]})

        self.__create_outer_circle()
        self.__image_ready = False

    def remove_starting_with(self, letter: Letter):
        if self.cons2 is letter:
            self.cons2 = None
            self.vowel = None
        elif self.vowel is letter:
            self.vowel = None
        else:
            raise ValueError(f'There is no letter {letter.text} in syllable {self.text}')
        self.__update_syllable_properties()
        self.__image_ready = False

    def add(self, letter: Letter):
        match letter.letter_type:
            case LetterType.VOWEL:
                if self.vowel:
                    return False
                self.vowel = letter
                letter.set_image(self.__draw)
                letter.update_syllable_properties(self)
            case LetterType.CONSONANT:
                if self.cons2 or self.vowel or not Consonant.compatible(self.cons1, letter):
                    return False
                self.cons2 = letter
                letter.set_image(self.__draw)
                letter.update_syllable_properties(self)
            case _:
                raise ValueError(f'No such letter type: {letter.letter_type} (letter={letter.text})')
        self.__update_syllable_properties()
        self.__image_ready = False
        return True

    def press(self, point: Point):
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        if radius > self.outer_radius + self.half_line_distance:
            return False
        if radius > self.outer_radius - self.half_line_distance:
            self.pressed_type = PressedType.BORDER
            self.__bias = radius - self.outer_radius
            return True
        if self.vowel and self.vowel.decoration_type is not VowelDecoration.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self.__pressed = self.vowel
            return True
        if self.inner_radius - self.half_line_distance < radius < self.inner_radius + self.half_line_distance:
            self.pressed_type = PressedType.INNER
            self.__bias = radius - self.inner_radius
            return True
        if radius <= self.inner_radius - self.half_line_distance:
            self.pressed_type = PressedType.PARENT
            self.__bias = point
            return True
        for cons in reversed(self.consonants):
            if cons.press(point):
                self.pressed_type = PressedType.CHILD
                self.__pressed = cons
                return True
        if self.vowel and self.vowel.decoration_type is VowelDecoration.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self.__pressed = self.vowel
            return True
        self.pressed_type = PressedType.PARENT
        self.__bias = point
        return True

    def move(self, point: Point, radius=0):
        shifted = point.shift(-round(math.cos(self.direction) * radius),
                              -round(math.sin(self.direction) * radius))
        match self.pressed_type:
            case PressedType.INNER:
                new_radius = math.sqrt(shifted.x * shifted.x + shifted.y * shifted.y) - self.__bias
                self.inner_scale = min(max(new_radius / self.outer_radius, INNER_SCALE_MIN), INNER_SCALE_MAX)
                self.__update_image_properties()
            case PressedType.BORDER:
                new_radius = math.sqrt(shifted.x * shifted.x + shifted.y * shifted.y) - self.__bias
                self.__personal_scale = min(
                    max(new_radius / OUTER_CIRCLE_RADIUS / self.__parent_scale, SYLLABLE_SCALE_MIN),
                    SYLLABLE_SCALE_MAX)
                self.__update_image_properties()
                if self.__following:
                    self.__following.resize(self.scale)
            case PressedType.PARENT:
                if radius:
                    point = point - self.__bias
                    self.direction = math.atan2(point.y, point.x)
                    self.__update_image_properties()
            case PressedType.CHILD:
                self.__pressed.move(shifted)
                self.__image_ready = False

    def resize(self, parent_scale: float = None, personal_scale: float = None):
        if parent_scale is not None:
            self.__parent_scale = parent_scale
        if personal_scale is not None:
            self.__personal_scale = max(self.__personal_scale * personal_scale, SYLLABLE_SCALE_MIN)
        self.__update_image_properties()

        if self.__following:
            self.__following.resize(self.scale)

    def set_following(self, following):
        self.__following = following

    def create_image(self) -> Image:
        if self.__image_ready:
            return self.__image
        # clear all
        self.__draw.rectangle(((0, 0), self.__image.size), fill=SYLLABLE_BG)
        if self.vowel and self.vowel.decoration_type is VowelDecoration.HIDDEN:
            self.vowel.draw_decoration()
        self.__draw_cons_decoration()
        self.__draw_inner_circle()
        if self.vowel and self.vowel.decoration_type is not VowelDecoration.HIDDEN:
            self.vowel.draw_decoration()
        # paste the outer circle image
        self.__image.paste(self.__border_image, mask=self.__mask_image)
        self.__image_ready = True
        return self.__image

    def __draw_cons_decoration(self):
        for cons in self.consonants:
            cons.draw_decoration()

    def __draw_inner_circle(self):
        for args in self.__inner_circle_arg_dict:
            self.__draw.ellipse(**args)

    def __create_outer_circle(self):
        self.__border_draw.rectangle(((0, 0), self.__border_image.size), fill=0)
        self.__mask_draw.rectangle(((0, 0), self.__mask_image.size), fill=1)
        if len(self.cons1.borders) == 1:
            left = SYLLABLE_IMAGE_RADIUS - self.outer_radius - self.cons1.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + self.outer_radius + self.cons1.half_widths[0]
            self.__border_draw.ellipse((left, left, right, right), outline=SYLLABLE_COLOR, width=self.cons1.widths[0])
            self.__mask_draw.ellipse((left, left, right, right), outline=1, fill=0, width=self.cons1.widths[0])

        else:
            radius = self.outer_radius + self.half_line_distance
            left = SYLLABLE_IMAGE_RADIUS - radius - self.cons1.half_widths[0]
            right = SYLLABLE_IMAGE_RADIUS + radius + self.cons1.half_widths[0]
            self.__border_draw.ellipse((left, left, right, right),
                                       outline=SYLLABLE_COLOR, fill=SYLLABLE_BG, width=self.cons1.widths[0])

            radius = max(self.outer_radius - self.half_line_distance, MIN_RADIUS)
            left = SYLLABLE_IMAGE_RADIUS - radius - self.cons1.half_widths[1]
            right = SYLLABLE_IMAGE_RADIUS + radius + self.cons1.half_widths[1]
            self.__border_draw.ellipse((left, left, right, right), outline=SYLLABLE_COLOR, width=self.cons1.widths[1])
            self.__mask_draw.ellipse((left, left, right, right), outline=1, fill=0, width=self.cons1.widths[1])


class Word:
    def __init__(self, center: Point, syllables: List[Syllable]):
        self.center = center
        self.outer_radius = None
        self.borders = '21'
        self.__widths, self.__half_widths = [], []
        self.__half_line_distance = None

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

        self.__image = Image.new('RGBA', (2 * WORD_IMAGE_RADIUS, 2 * WORD_IMAGE_RADIUS))
        self.__draw = ImageDraw.Draw(self.__image)

        self.__border_image = Image.new('RGBA', self.__image.size)
        self.__border_draw = ImageDraw.Draw(self.__border_image)

        self.__mask_image = Image.new('1', self.__image.size)
        self.__mask_draw = ImageDraw.Draw(self.__mask_image)

        self.__image_tk = ImageTk.PhotoImage(image=self.__image.mode, size=self.__image.size)
        self.__update_image_properties()

        self.pressed_type: PressedType | None = None
        self.__pressed: Syllable | None = None
        self.__bias = None

    def __update_image_properties(self):
        self.outer_radius = OUTER_CIRCLE_RADIUS * self.scale
        self.__widths = list(map(lambda x: line_width(x, self.scale), self.borders))
        self.__half_widths = list(map(lambda x: x / 2, self.__widths))
        self.__half_line_distance = half_line_distance(self.scale)
        self.__create_outer_circle()

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
            self.__update_image_properties()
        self.syllables = syllables
        self.text = ''.join(map(lambda s: s.text, syllables))

    def press(self, point: Point):
        word_point = point - self.center
        if not len(self.rest):
            if self.first.press(word_point):
                if self.first.pressed_type == PressedType.PARENT:
                    self.pressed_type = PressedType.PARENT
                    self.__bias = point - self.center
                else:
                    self.pressed_type = PressedType.CHILD
                    self.__pressed = self.first
                return True
            else:
                return False
        else:
            radius = math.sqrt(word_point.x * word_point.x + word_point.y * word_point.y)
            if radius > self.outer_radius + self.__half_line_distance:
                return False
            if radius > self.outer_radius - self.__half_line_distance:
                self.pressed_type = PressedType.BORDER
                self.__bias = radius - self.outer_radius
                return True

            first_radius = self.first.outer_radius
            for syllable in reversed(self.rest):
                if syllable.press(word_point.shift(-round(math.cos(syllable.direction) * first_radius),
                                                   -round(math.sin(syllable.direction) * first_radius))):
                    self.pressed_type = PressedType.CHILD
                    self.__pressed = syllable
                    return True

            if self.first.press(word_point):
                if self.first.pressed_type == PressedType.PARENT:
                    self.pressed_type = PressedType.PARENT
                    self.__bias = point - self.center
                else:
                    self.pressed_type = PressedType.CHILD
                    self.__pressed = self.first
                return True

            self.pressed_type = PressedType.PARENT
            self.__bias = point - self.center
            return True

    def move(self, point: Point):
        word_point = point - self.center
        match self.pressed_type:
            case PressedType.CHILD:
                if self.__pressed is self.first:
                    self.first.move(word_point)
                else:
                    first_radius = self.first.outer_radius
                    self.__pressed.move(word_point, first_radius)
            case PressedType.BORDER:
                new_radius = math.sqrt(word_point.x * word_point.x + word_point.y * word_point.y) - self.__bias
                self.scale = min(max(new_radius / OUTER_CIRCLE_RADIUS, WORD_SCALE_MIN), 1)
                self.__update_image_properties()
                self.first.resize(self.scale)
            case PressedType.PARENT:
                self.center = point - self.__bias

    def create_image(self, canvas: tk.Canvas):
        if not self.rest:
            self.__draw.rectangle(((0, 0), self.__image.size), fill=0)
            image = self.first.create_image()
            self.__image.paste(image, (WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS,
                                       WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS), image)
            self.__image_tk.paste(self.__image)
            canvas.create_image(self.center.x, self.center.y, image=self.__image_tk)
        else:
            # clear all
            self.__draw.rectangle(((0, 0), self.__image.size), fill=WORD_BG)
            image = self.first.create_image()
            self.__image.paste(image, (WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS,
                                       WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS), image)
            first_radius = self.first.scale * OUTER_CIRCLE_RADIUS
            for s in self.rest:
                image = s.create_image()
                self.__image.paste(image, (
                    round(math.cos(s.direction) * first_radius) + WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS,
                    round(math.sin(s.direction) * first_radius) + WORD_IMAGE_RADIUS - SYLLABLE_IMAGE_RADIUS), image)

            # paste the outer circle image
            self.__image.paste(self.__border_image, mask=self.__mask_image)
            self.__image_tk.paste(self.__image)
            canvas.create_image(self.center.x, self.center.y, image=self.__image_tk)

    def __create_outer_circle(self):
        self.__border_draw.rectangle(((0, 0), self.__border_image.size), fill=0)
        self.__mask_draw.rectangle(((0, 0), self.__border_image.size), fill=1)
        if len(self.borders) == 1:
            left = WORD_IMAGE_RADIUS - self.outer_radius - self.__half_widths[0]
            right = WORD_IMAGE_RADIUS + self.outer_radius + self.__half_widths[0]
            self.__border_draw.ellipse((left, left, right, right), outline=WORD_COLOR, width=self.__widths[0])
            self.__mask_draw.ellipse((left, left, right, right), outline=1, fill=0, width=self.__widths[0])
        else:
            radius = self.outer_radius + self.__half_line_distance
            left = WORD_IMAGE_RADIUS - radius - self.__half_widths[0]
            right = WORD_IMAGE_RADIUS + radius + self.__half_widths[0]
            self.__border_draw.ellipse((left, left, right, right),
                                       outline=WORD_COLOR, fill=WORD_BG, width=self.__widths[0])

            radius = max(self.outer_radius - self.__half_line_distance, MIN_RADIUS)
            left = WORD_IMAGE_RADIUS - radius - self.__half_widths[1]
            right = WORD_IMAGE_RADIUS + radius + self.__half_widths[1]
            self.__border_draw.ellipse((left, left, right, right), outline=WORD_COLOR, width=self.__widths[1])
            self.__mask_draw.ellipse((left, left, right, right), outline=1, fill=0, width=self.__widths[1])
