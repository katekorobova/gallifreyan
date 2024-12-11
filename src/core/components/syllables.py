import math
import random
from typing import Dict, List, Optional

from PIL import Image, ImageDraw

from src.utils import Point, PressedType, half_line_distance, MIN_RADIUS, OUTER_CIRCLE_RADIUS, \
    SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG, \
    SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX, SYLLABLE_SCALE_MIN, SYLLABLE_SCALE_MAX, \
    INNER_INITIAL_SCALE_MIN, INNER_INITIAL_SCALE_MAX, INNER_SCALE_MIN, INNER_SCALE_MAX
from .consonants import Consonant
from .letters import Letter
from .vowels import Vowel, VowelDecoration


class Syllable:
    def __init__(self, cons1: Consonant, cons2: Optional[Consonant] = None, vowel: Optional[Vowel] = None):
        # Core attributes
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

        # Scales and radii
        self.inner_scale = random.uniform(INNER_INITIAL_SCALE_MIN, INNER_INITIAL_SCALE_MAX)
        self.scale = 0.0
        self.outer_radius = 0.0
        self.inner_radius = 0.0
        self.half_line_distance = 0.0
        self._update_syllable_properties()

        # Image properties
        self._image, self._draw = self._create_empty_image()
        self._border_image, self._border_draw = self._create_empty_image()
        self._mask_image, self._mask_draw = self._create_empty_image('1')
        self._inner_circle_arg_dict: List[Dict] = []
        self._image_ready = False

        for letter in self.letters:
            letter.set_image(self._draw)
        self._update_image_properties()

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Letter] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    @staticmethod
    def _create_empty_image(mode='RGBA') -> tuple[Image.Image, ImageDraw.Draw]:
        """Creates an empty image and its corresponding drawing object."""
        image = Image.new(mode, (2 * SYLLABLE_IMAGE_RADIUS, 2 * SYLLABLE_IMAGE_RADIUS))
        return image, ImageDraw.Draw(image)

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
        distance = point.distance()
        if distance > self.outer_radius + self.half_line_distance:
            return False
        if distance > self.outer_radius - self.half_line_distance:
            self.pressed_type = PressedType.BORDER
            self._distance_bias = distance - self.outer_radius
            return True
        if self.vowel and self.vowel.decoration_type is not VowelDecoration.HIDDEN and self.vowel.press(point):
            self.pressed_type = PressedType.CHILD
            self._pressed = self.vowel
            return True
        if self.inner_radius - self.half_line_distance < distance < self.inner_radius + self.half_line_distance:
            self.pressed_type = PressedType.INNER
            self._distance_bias = distance - self.inner_radius
            return True
        if distance <= self.inner_radius - self.half_line_distance:
            self.pressed_type = PressedType.PARENT
            self._point_bias = point
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
        self._point_bias = point
        return True

    def move(self, point: Point, radius=0.0):
        shifted = point.shift(-round(math.cos(self.direction) * radius),
                              -round(math.sin(self.direction) * radius))
        match self.pressed_type:
            case PressedType.INNER:
                new_radius = shifted.distance() - self._distance_bias
                self.inner_scale = min(max(new_radius / self.outer_radius, INNER_SCALE_MIN), INNER_SCALE_MAX)
                self._update_image_properties()
            case PressedType.BORDER:
                new_radius = shifted.distance() - self._distance_bias
                self._personal_scale = min(
                    max(new_radius / OUTER_CIRCLE_RADIUS / self._parent_scale, SYLLABLE_SCALE_MIN),
                    SYLLABLE_SCALE_MAX)
                self._update_image_properties()
                if self._following:
                    self._following.resize(self.scale)
            case PressedType.PARENT:
                if radius:
                    point = point - self._point_bias
                    self.direction = point.direction()
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
