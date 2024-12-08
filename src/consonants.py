import math
from enum import Enum
from typing import List, Dict

from letters import Letter, LetterType
from utils import Point, line_width, MIN_RADIUS, DOT_RADIUS, \
    SYLLABLE_IMAGE_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG
from collections import Counter


class ConsonantDecoration(Enum):
    STRAIGHT_ANGLE = ('sa', 2)
    OBTUSE_ANGLE = ('oa', 2)
    REFLEX_ANGLE = ('ra', 2)
    BENT_LINE = ('bl', 1)
    RADIAL_LINE = ('rl', 1)
    DIAMETRAL_LINE = ('dl', 1)
    CIRCLE = ('cl', 3)
    SIMILAR_DOTS = ('sd', 4)
    DIFFERENT_DOTS = ('dd', 4)
    WHITE_DOT = ('wd', 4)
    BLACK_DOT = ('bd', 4)

    def __init__(self, code: str, group: int):
        self.code = code
        self.group = group

    @staticmethod
    def get_by_code(code: str):
        return next(filter(lambda x: x.code == code, ConsonantDecoration))


class Consonant(Letter):

    def __init__(self, text: str, borders: str, decoration_type: ConsonantDecoration):
        super().__init__(text, LetterType.CONSONANT, borders)
        self.decoration_type = decoration_type

    @staticmethod
    def get_consonant(text: str, border: str, decoration_code: str):
        decoration_type = ConsonantDecoration.get_by_code(decoration_code)
        match decoration_type:
            case ConsonantDecoration.STRAIGHT_ANGLE:
                return StraightAngleConsonant(text, border)
            case ConsonantDecoration.OBTUSE_ANGLE:
                return ObtuseAngleConsonant(text, border)
            case ConsonantDecoration.REFLEX_ANGLE:
                return ReflexAngleConsonant(text, border)
            case ConsonantDecoration.BENT_LINE:
                return BentLineConsonant(text, border)
            case ConsonantDecoration.RADIAL_LINE:
                return RadialLineConsonant(text, border)
            case ConsonantDecoration.DIAMETRAL_LINE:
                return DiametralLineConsonant(text, border)
            case ConsonantDecoration.CIRCLE:
                return CircleConsonant(text, border)
            case ConsonantDecoration.SIMILAR_DOTS:
                return SimilarDotsConsonant(text, border)
            case ConsonantDecoration.DIFFERENT_DOTS:
                return DifferentDotsConsonant(text, border)
            case ConsonantDecoration.WHITE_DOT:
                return WhiteDotConsonant(text, border)
            case ConsonantDecoration.BLACK_DOT:
                return BlackDotConsonant(text, border)
            case _:
                raise ValueError(f'No such consonant decoration: {decoration_type} (letter={text})')

    @staticmethod
    def compatible(cons1, cons2) -> bool:
        full_data = ConsonantDecoration.RADIAL_LINE,
        unknown_order = ConsonantDecoration.DIAMETRAL_LINE,
        min_border = ConsonantDecoration.BENT_LINE, ConsonantDecoration.STRAIGHT_ANGLE, \
            ConsonantDecoration.OBTUSE_ANGLE, ConsonantDecoration.REFLEX_ANGLE, \
            ConsonantDecoration.CIRCLE

        if cons1.decoration_type in full_data or cons2.decoration_type in full_data:
            return cons1.borders != cons2.borders
        if cons1.decoration_type in unknown_order or cons2.decoration_type in unknown_order:
            return Counter(cons1.borders) != Counter(cons2.borders)
        if cons1.decoration_type in min_border or cons2.decoration_type in min_border:
            return min(cons1.borders) != min(cons2.borders)
        return False


class StraightAngleConsonant(Consonant):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.STRAIGHT_ANGLE)
        self.__width, self.__half_width = None, None

        self.__radius, self.__distance = None, None
        self.__start, self.__end = None, None
        self.__first, self.__bias = None, None

        self.__line_arg_dict: Dict | None = None
        self.__arc_arg_dict: Dict | None = None

    def press(self, point: Point) -> bool:
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        angle = math.atan2(point.y, point.x)
        angle -= self.direction
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if -self._half_line_distance < rotated.y < self._half_line_distance:
            if 0 < rotated.x < self.__distance:
                self.__first = True
                self.__bias = point - self.__start
                return True
            if -self.__distance < rotated.x < 0:
                self.__first = False
                self.__bias = point - self.__end
                return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction - math.pi
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        inner_radius = syllable.inner_radius

        self.__width = line_width(min(self.borders), syllable.scale)
        self.__half_width = self.__width / 2
        self.__distance = syllable.outer_radius
        self.__radius = inner_radius + syllable.offset[1] + 2 * self._half_line_distance
        self._update_image_properties()

    def _update_image_properties(self):
        self.__start = Point(math.cos(self.direction) * self.__distance,
                             math.sin(self.direction) * self.__distance)
        self.__end = Point(math.cos(self.direction + math.pi) * self.__distance,
                           math.sin(self.direction + math.pi) * self.__distance)

        left = SYLLABLE_IMAGE_RADIUS - self.__radius - self.__half_width
        right = SYLLABLE_IMAGE_RADIUS + self.__radius + self.__half_width

        dir1 = math.degrees(self.direction)
        dir2 = dir1 + 180

        self.__line_arg_dict = {'xy': (SYLLABLE_IMAGE_RADIUS + self.__start.x, SYLLABLE_IMAGE_RADIUS + self.__start.y,
                                       SYLLABLE_IMAGE_RADIUS + self.__end.x, SYLLABLE_IMAGE_RADIUS + self.__end.y),
                                'fill': SYLLABLE_COLOR, 'width': self.__width}
        self.__arc_arg_dict = {'xy': (left, left, right, right), 'start': dir1, 'end': dir2,
                               'fill': SYLLABLE_COLOR, 'width': self.__width}

    def draw_decoration(self):
        if self.__line_arg_dict:
            self._image.line(**self.__line_arg_dict)
        if self.__arc_arg_dict:
            self._image.arc(**self.__arc_arg_dict)


class ObtuseAngleConsonant(Consonant):
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.OBTUSE_ANGLE)
        self.__width, self.__half_width = None, None

        self.__distance, self.__radius = None, None
        self.__end1, self.__end2 = None, None
        self.__first = True
        self.__bias = None

        self.__line_arg_dicts: List[Dict] = []
        self.__arc_arg_dict: Dict | None = None

    def press(self, point: Point) -> bool:
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        angle = math.atan2(point.y, point.x)
        angle -= self.direction
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__first = True
            self.__bias = point - self.__end1
            return True

        angle -= self.ANGLE
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__first = False
            self.__bias = point - self.__end2
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction - self.ANGLE
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        inner_radius = syllable.inner_radius

        self.__width = line_width(min(self.borders), syllable.scale)
        self.__half_width = self.__width / 2
        self.__distance = syllable.outer_radius
        self.__radius = inner_radius + syllable.offset[1] + 2 * self._half_line_distance
        self._update_image_properties()

    def _update_image_properties(self):
        self.__end1 = Point(math.cos(self.direction) * self.__distance,
                            math.sin(self.direction) * self.__distance)
        self.__end2 = Point(math.cos(self.direction + self.ANGLE) * self.__distance,
                            math.sin(self.direction + self.ANGLE) * self.__distance)

        left = SYLLABLE_IMAGE_RADIUS - self.__radius - self.__half_width
        right = SYLLABLE_IMAGE_RADIUS + self.__radius + self.__half_width

        dir1 = math.degrees(self.direction)
        dir2 = math.degrees(self.direction + self.ANGLE)

        self.__line_arg_dicts = [{'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                                         SYLLABLE_IMAGE_RADIUS + self.__end1.x, SYLLABLE_IMAGE_RADIUS + self.__end1.y),
                                  'fill': SYLLABLE_COLOR, 'width': self.__width},
                                 {'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                                         SYLLABLE_IMAGE_RADIUS + self.__end2.x, SYLLABLE_IMAGE_RADIUS + self.__end2.y),
                                  'fill': SYLLABLE_COLOR, 'width': self.__width}]
        self.__arc_arg_dict = {'xy': (left, left, right, right), 'start': dir1, 'end': dir2,
                               'fill': SYLLABLE_COLOR, 'width': self.__width}

    def draw_decoration(self):
        for args in self.__line_arg_dicts:
            self._image.line(**args)
        if self.__arc_arg_dict:
            self._image.arc(**self.__arc_arg_dict)


class ReflexAngleConsonant(Consonant):
    ANGLE = 1.4 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.REFLEX_ANGLE)
        self.__width, self.__half_width = None, None

        self.__distance, self.__radius = None, None
        self.__end1, self.__end2 = None, None
        self.__first = True
        self.__bias = None

        self.__line_arg_dicts: List[Dict] = []
        self.__arc_arg_dict: Dict | None = None

    def press(self, point: Point) -> bool:
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        angle = math.atan2(point.y, point.x)
        angle -= self.direction
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__first = True
            self.__bias = point - self.__end1
            return True

        angle -= self.ANGLE
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__first = False
            self.__bias = point - self.__end2
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction - self.ANGLE
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        inner_radius = syllable.inner_radius

        self.__width = line_width(min(self.borders), syllable.scale)
        self.__half_width = self.__width / 2
        self.__distance = syllable.outer_radius
        self.__radius = inner_radius + syllable.offset[1] + 2 * self._half_line_distance
        self._update_image_properties()

    def _update_image_properties(self):
        self.__end1 = Point(math.cos(self.direction) * self.__distance,
                            math.sin(self.direction) * self.__distance)
        self.__end2 = Point(math.cos(self.direction + self.ANGLE) * self.__distance,
                            math.sin(self.direction + self.ANGLE) * self.__distance)

        left = SYLLABLE_IMAGE_RADIUS - self.__radius - self.__half_width
        right = SYLLABLE_IMAGE_RADIUS + self.__radius + self.__half_width

        dir1 = math.degrees(self.direction)
        dir2 = math.degrees(self.direction + self.ANGLE)

        self.__line_arg_dicts = [{'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                                         SYLLABLE_IMAGE_RADIUS + self.__end1.x, SYLLABLE_IMAGE_RADIUS + self.__end1.y),
                                  'fill': SYLLABLE_COLOR, 'width': self.__width},
                                 {'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                                         SYLLABLE_IMAGE_RADIUS + self.__end2.x, SYLLABLE_IMAGE_RADIUS + self.__end2.y),
                                  'fill': SYLLABLE_COLOR, 'width': self.__width}]
        self.__arc_arg_dict = {'xy': (left, left, right, right), 'start': dir1, 'end': dir2,
                               'fill': SYLLABLE_COLOR, 'width': self.__width}

    def draw_decoration(self):
        for args in self.__line_arg_dicts:
            self._image.line(**args)
        if self.__arc_arg_dict:
            self._image.arc(**self.__arc_arg_dict)


class BentLineConsonant(Consonant):
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.BENT_LINE)
        self.__width = None

        self.__end1, self.__end2 = None, None
        self.__distance = None
        self.__first, self.__bias = None, None

        self.__line_arg_dicts: List[Dict] = []

    def press(self, point: Point) -> bool:
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        angle = math.atan2(point.y, point.x)
        angle -= self.direction
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__first = True
            self.__bias = point - self.__end1
            return True

        angle -= self.ANGLE
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__first = False
            self.__bias = point - self.__end2
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction - self.ANGLE
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        self.__width = line_width(min(self.borders), syllable.scale)
        self.__distance = syllable.outer_radius
        self._update_image_properties()

    def _update_image_properties(self):
        self.__end1 = Point(math.cos(self.direction) * self.__distance,
                            math.sin(self.direction) * self.__distance)
        self.__end2 = Point(math.cos(self.direction + self.ANGLE) * self.__distance,
                            math.sin(self.direction + self.ANGLE) * self.__distance)

        self.__line_arg_dicts = [{'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                                         SYLLABLE_IMAGE_RADIUS + self.__end1.x, SYLLABLE_IMAGE_RADIUS + self.__end1.y),
                                  'fill': SYLLABLE_COLOR, 'width': self.__width},
                                 {'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                                         SYLLABLE_IMAGE_RADIUS + self.__end2.x, SYLLABLE_IMAGE_RADIUS + self.__end2.y),
                                  'fill': SYLLABLE_COLOR, 'width': self.__width}]

    def draw_decoration(self):
        for args in self.__line_arg_dicts:
            self._image.line(**args)


class RadialLineConsonant(Consonant):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.RADIAL_LINE)

        self.__end = None
        self.__distance = None
        self.__bias = None

        self.__polygon_arg_dict: Dict = {}
        self.__line_arg_dicts: List[Dict] = []

    def press(self, point: Point) -> bool:
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        angle = math.atan2(point.y, point.x)
        angle -= self.direction
        rotated = Point(math.cos(angle) * radius, math.sin(angle) * radius)
        if 0 < rotated.x < self.__distance and -self._half_line_distance < rotated.y < self._half_line_distance:
            self.__bias = point - self.__end
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        self.direction = math.atan2(point.y, point.x)
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        self.__distance = syllable.outer_radius
        self._update_image_properties()

    def _update_image_properties(self):
        self.__end = Point(math.cos(self.direction) * self.__distance,
                           math.sin(self.direction) * self.__distance)

        if len(self.borders) == 1:
            self.__polygon_arg_dict = {}
            self.__line_arg_dicts = [
                {'xy': (SYLLABLE_IMAGE_RADIUS, SYLLABLE_IMAGE_RADIUS,
                        SYLLABLE_IMAGE_RADIUS + self.__end.x, SYLLABLE_IMAGE_RADIUS + self.__end.y),
                 'fill': SYLLABLE_COLOR, 'width': self.widths[0]}]
        else:
            dx = math.cos(self.direction + math.pi / 2) * self._half_line_distance
            dy = math.sin(self.direction + math.pi / 2) * self._half_line_distance
            start1 = SYLLABLE_IMAGE_RADIUS - dx, SYLLABLE_IMAGE_RADIUS - dy
            end1 = SYLLABLE_IMAGE_RADIUS + self.__end.x - dx, SYLLABLE_IMAGE_RADIUS + self.__end.y - dy
            start2 = SYLLABLE_IMAGE_RADIUS + dx, SYLLABLE_IMAGE_RADIUS + dy
            end2 = SYLLABLE_IMAGE_RADIUS + self.__end.x + dx, SYLLABLE_IMAGE_RADIUS + self.__end.y + dy

            self.__polygon_arg_dict = {'xy': (start1, end1, end2, start2), 'outline': SYLLABLE_BG, 'fill': SYLLABLE_BG}
            self.__line_arg_dicts = [{'xy': (start1, end1), 'fill': SYLLABLE_COLOR, 'width': self.widths[0]},
                                     {'xy': (start2, end2), 'fill': SYLLABLE_COLOR, 'width': self.widths[1]}]

    def draw_decoration(self):
        if self.__polygon_arg_dict:
            self._image.polygon(**self.__polygon_arg_dict)
        for args in self.__line_arg_dicts:
            self._image.line(**args)


class DiametralLineConsonant(Consonant):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.DIAMETRAL_LINE)

        self.__start, self.__end = None, None
        self.__distance = None
        self.__first, self.__bias = None, None

        self.__polygon_arg_dict: Dict | None = None
        self.__line_arg_dicts: List[Dict] = []

    def press(self, point: Point) -> bool:
        radius = math.sqrt(point.x * point.x + point.y * point.y)
        angle = math.atan2(point.y, point.x)
        angle -= self.direction
        rotated = Point(math.cos(angle) * radius,
                        math.sin(angle) * radius)
        if -self._half_line_distance < rotated.y < self._half_line_distance:
            if 0 < rotated.x < self.__distance:
                self.__first = True
                self.__bias = point - self.__start
                return True
            if -self.__distance < rotated.x <= 0:
                self.__first = False
                self.__bias = point - self.__end
                return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction + math.pi
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        self.__distance = syllable.outer_radius
        self._update_image_properties()

    def _update_image_properties(self):
        self.__start = Point(math.cos(self.direction) * self.__distance,
                             math.sin(self.direction) * self.__distance)
        self.__end = Point(math.cos(self.direction + math.pi) * self.__distance,
                           math.sin(self.direction + math.pi) * self.__distance)

        if len(self.borders) == 1:
            self.__polygon_arg_dict = None
            self.__line_arg_dicts = [
                {'xy': (SYLLABLE_IMAGE_RADIUS + self.__start.x, SYLLABLE_IMAGE_RADIUS + self.__start.y,
                        SYLLABLE_IMAGE_RADIUS + self.__end.x, SYLLABLE_IMAGE_RADIUS + self.__end.y),
                 'fill': SYLLABLE_COLOR, 'width': self.widths[0]}]
        else:
            dx = math.cos(self.direction + math.pi / 2) * self._half_line_distance
            dy = math.sin(self.direction + math.pi / 2) * self._half_line_distance
            start1 = SYLLABLE_IMAGE_RADIUS + self.__start.x - dx, SYLLABLE_IMAGE_RADIUS + self.__start.y - dy
            end1 = SYLLABLE_IMAGE_RADIUS + self.__end.x - dx, SYLLABLE_IMAGE_RADIUS + self.__end.y - dy
            start2 = SYLLABLE_IMAGE_RADIUS + self.__start.x + dx, SYLLABLE_IMAGE_RADIUS + self.__start.y + dy
            end2 = SYLLABLE_IMAGE_RADIUS + self.__end.x + dx, SYLLABLE_IMAGE_RADIUS + self.__end.y + dy

            self.__polygon_arg_dict = {'xy': (start1, end1, end2, start2), 'outline': SYLLABLE_BG, 'fill': SYLLABLE_BG}
            self.__line_arg_dicts = [{'xy': (start1, end1), 'fill': SYLLABLE_COLOR, 'width': self.widths[0]},
                                     {'xy': (start2, end2), 'fill': SYLLABLE_COLOR, 'width': self.widths[1]}]

    def draw_decoration(self):
        if self.__polygon_arg_dict:
            self._image.polygon(**self.__polygon_arg_dict)
        for args in self.__line_arg_dicts:
            self._image.line(**args)


class CircleConsonant(Consonant):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.CIRCLE)
        self.__width, self.__half_width = None, None

        self.__radius, self.__distance, self.__center = None, None, None
        self.__bias = None

        self.__ellipse_arg_dict: Dict = {}

    def press(self, point: Point) -> bool:
        delta = point - self.__center
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        self.direction = direction
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self.__width = line_width(min(self.borders), syllable.scale)
        self.__half_width = self.__width / 2
        self.__radius = max((outer_radius - offset[0] - inner_radius - offset[1]) / 4, MIN_RADIUS)
        self.__distance = inner_radius + offset[1] + self.__radius
        self._update_image_properties()

    def _update_image_properties(self):
        self.__center = Point(math.cos(self.direction) * self.__distance,
                              math.sin(self.direction) * self.__distance)

        left = SYLLABLE_IMAGE_RADIUS + self.__center.x - self.__radius - self.__half_width
        right = SYLLABLE_IMAGE_RADIUS + self.__center.x + self.__radius + self.__half_width
        top = SYLLABLE_IMAGE_RADIUS + self.__center.y - self.__radius - self.__half_width
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center.y + self.__radius + self.__half_width

        self.__ellipse_arg_dict = {'xy': (left, top, right, bottom),
                                   'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.__width}

    def draw_decoration(self):
        self._image.ellipse(**self.__ellipse_arg_dict)


class SimilarDotsConsonant(Consonant):
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.SIMILAR_DOTS)
        self.__width = None

        self.__distance = None
        self.__center1, self.__center2 = None, None
        self.__radius = None
        self.__bias, self.__first = None, True

        self.__ellipse_arg_dicts: List[Dict] = []

    def press(self, point: Point) -> bool:
        delta = point - self.__center1
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            self.__first = True
            return True

        delta = point - self.__center2
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            self.__first = False
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction - self.ANGLE
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self.__width = line_width('1', syllable.scale)
        self.__distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)
        self.__radius = syllable.scale * DOT_RADIUS
        self._update_image_properties()

    def _update_image_properties(self):
        self.__ellipse_arg_dicts = []
        self.__center1 = Point(math.cos(self.direction) * self.__distance,
                               math.sin(self.direction) * self.__distance)
        left = SYLLABLE_IMAGE_RADIUS + self.__center1.x - self.__radius
        right = SYLLABLE_IMAGE_RADIUS + self.__center1.x + self.__radius
        top = SYLLABLE_IMAGE_RADIUS + self.__center1.y - self.__radius
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center1.y + self.__radius

        self.__ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                         'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.__width})

        self.__center2 = Point(math.cos(self.direction + self.ANGLE) * self.__distance,
                               math.sin(self.direction + self.ANGLE) * self.__distance)
        left = SYLLABLE_IMAGE_RADIUS + self.__center2.x - self.__radius
        right = SYLLABLE_IMAGE_RADIUS + self.__center2.x + self.__radius
        top = SYLLABLE_IMAGE_RADIUS + self.__center2.y - self.__radius
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center2.y + self.__radius

        self.__ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                         'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.__width})

    def draw_decoration(self):
        for args in self.__ellipse_arg_dicts:
            self._image.ellipse(**args)


class DifferentDotsConsonant(Consonant):
    ANGLE = 0.6 * math.pi

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.DIFFERENT_DOTS)
        self.__width = None

        self.__distance = None
        self.__center1, self.__center2 = None, None
        self.__radius = None
        self.__bias, self.__first = None, True

        self.__ellipse_arg_dicts: List[Dict] = []

    def press(self, point: Point) -> bool:
        delta = point - self.__center1
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            self.__first = True
            return True

        delta = point - self.__center2
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            self.__first = False
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        direction = math.atan2(point.y, point.x)
        if self.__first:
            self.direction = direction
        else:
            self.direction = direction - self.ANGLE
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self.__width = line_width('1', syllable.scale)
        self.__distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)
        self.__radius = syllable.scale * DOT_RADIUS
        self._update_image_properties()

    def _update_image_properties(self):
        self.__ellipse_arg_dicts = []
        self.__center1 = Point(math.cos(self.direction) * self.__distance,
                               math.sin(self.direction) * self.__distance)
        left = SYLLABLE_IMAGE_RADIUS + self.__center1.x - self.__radius
        right = SYLLABLE_IMAGE_RADIUS + self.__center1.x + self.__radius
        top = SYLLABLE_IMAGE_RADIUS + self.__center1.y - self.__radius
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center1.y + self.__radius

        self.__ellipse_arg_dicts.append({'xy': (left, top, right, bottom), 'fill': SYLLABLE_COLOR})

        self.__center2 = Point(math.cos(self.direction + self.ANGLE) * self.__distance,
                               math.sin(self.direction + self.ANGLE) * self.__distance)
        left = SYLLABLE_IMAGE_RADIUS + self.__center2.x - self.__radius
        right = SYLLABLE_IMAGE_RADIUS + self.__center2.x + self.__radius
        top = SYLLABLE_IMAGE_RADIUS + self.__center2.y - self.__radius
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center2.y + self.__radius

        self.__ellipse_arg_dicts.append({'xy': (left, top, right, bottom),
                                         'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.__width})

    def draw_decoration(self):
        for args in self.__ellipse_arg_dicts:
            self._image.ellipse(**args)


class WhiteDotConsonant(Consonant):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.WHITE_DOT)
        self.__width = None

        self.__distance = None
        self.__center, self.__radius = None, None
        self.__bias = None

        self.__ellipse_arg_dict: Dict | None = None

    def press(self, point: Point) -> bool:
        delta = point - self.__center
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        self.direction = math.atan2(point.y, point.x)
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self.__width = line_width('1', syllable.scale)
        self.__distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)
        self.__radius = syllable.scale * DOT_RADIUS
        self._update_image_properties()

    def _update_image_properties(self):
        self.__center = Point(math.cos(self.direction) * self.__distance,
                              math.sin(self.direction) * self.__distance)
        left = SYLLABLE_IMAGE_RADIUS + self.__center.x - self.__radius
        right = SYLLABLE_IMAGE_RADIUS + self.__center.x + self.__radius
        top = SYLLABLE_IMAGE_RADIUS + self.__center.y - self.__radius
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center.y + self.__radius

        self.__ellipse_arg_dict = {'xy': (left, top, right, bottom),
                                   'outline': SYLLABLE_COLOR, 'fill': SYLLABLE_BG, 'width': self.__width}

    def draw_decoration(self):
        if self.__ellipse_arg_dict:
            self._image.ellipse(**self.__ellipse_arg_dict)


class BlackDotConsonant(Consonant):

    def __init__(self, text: str, borders: str):
        super().__init__(text, borders, ConsonantDecoration.BLACK_DOT)

        self.__distance = None
        self.__center, self.__radius = None, None
        self.__bias = None

        self.__ellipse_arg_dict: Dict | None = None

    def press(self, point: Point) -> bool:
        delta = point - self.__center
        radius = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if radius < self.__radius:
            self.__bias = delta
            return True
        return False

    def move(self, point: Point):
        point = point - self.__bias
        self.direction = math.atan2(point.y, point.x)
        self._update_image_properties()

    def update_syllable_properties(self, syllable):
        super().update_syllable_properties(syllable)

        outer_radius = syllable.outer_radius
        inner_radius = syllable.inner_radius
        offset = syllable.offset

        self.__distance = max((outer_radius - offset[0] + inner_radius + offset[1]) / 2, MIN_RADIUS)
        self.__radius = syllable.scale * DOT_RADIUS
        self._update_image_properties()

    def _update_image_properties(self):
        self.__center = Point(math.cos(self.direction) * self.__distance,
                              math.sin(self.direction) * self.__distance)
        left = SYLLABLE_IMAGE_RADIUS + self.__center.x - self.__radius
        right = SYLLABLE_IMAGE_RADIUS + self.__center.x + self.__radius
        top = SYLLABLE_IMAGE_RADIUS + self.__center.y - self.__radius
        bottom = SYLLABLE_IMAGE_RADIUS + self.__center.y + self.__radius

        self.__ellipse_arg_dict = {'xy': (left, top, right, bottom), 'fill': SYLLABLE_COLOR}

    def draw_decoration(self):
        if self.__ellipse_arg_dict:
            self._image.ellipse(**self.__ellipse_arg_dict)
