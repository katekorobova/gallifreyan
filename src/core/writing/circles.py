from itertools import repeat

from PIL import Image

from ..utils import Point, create_empty_image, get_line_width, get_half_line_distance
from ...config import DEFAULT_WORD_RADIUS


class HasOuterCircle:
    def __init__(self, borders: str, image_center: Point):
        self.borders = borders
        self.outer_radius = 0.0
        self.half_line_distance = 0.0
        self.image_center = image_center

        num_borders = len(borders)
        self.line_widths = list(repeat(0, num_borders))
        self.half_line_widths = list(repeat(0.0, num_borders))

        self.__border_image, self.__border_draw = create_empty_image(image_center)
        self.__mask_image, self.__mask_draw = create_empty_image(image_center, '1')

    def beyond_border(self, distance: float) -> bool:
        if len(self.borders) == 1:
            return distance > self.outer_radius + self.half_line_distance
        return distance > self.outer_radius + 2 * self.half_line_distance

    def on_border(self, distance: float) -> bool:
        if len(self.borders) == 1:
            return distance > self.outer_radius - self.half_line_distance
        return distance > self.outer_radius

    def scale_lines(self, scale: float) -> None:
        self.line_widths = [get_line_width(border, scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]
        self.half_line_distance = get_half_line_distance(scale)

    def scale_outer_radius(self, scale: float) -> None:
        self.outer_radius = scale * DEFAULT_WORD_RADIUS

    def create_outer_circle(self, color: str, background: str) -> None:
        """Create the outer circle representation."""
        self.__border_draw.rectangle(((0, 0), self.__border_image.size), fill=0)
        self.__mask_draw.rectangle(((0, 0), self.__mask_image.size), fill=1)
        if len(self.borders) == 1:
            adjusted_radius = self.outer_radius + self.half_line_widths[0]
            start = self.image_center.shift(-adjusted_radius).tuple()
            end = self.image_center.shift(adjusted_radius).tuple()
            self.__border_draw.ellipse((start, end), outline=color, width=self.line_widths[0])
            self.__mask_draw.ellipse((start, end), outline=1, fill=0, width=self.line_widths[0])
        else:
            adjusted_radius = self.outer_radius + 2 * self.half_line_distance + self.half_line_widths[0]
            start = self.image_center.shift(-adjusted_radius).tuple()
            end = self.image_center.shift(adjusted_radius).tuple()
            self.__border_draw.ellipse((start, end), outline=color, fill=background,
                                       width=self.line_widths[0])

            adjusted_radius = self.outer_radius + self.half_line_widths[1]
            start = self.image_center.shift(-adjusted_radius).tuple()
            end = self.image_center.shift(adjusted_radius).tuple()
            self.__border_draw.ellipse((start, end), outline=color, width=self.line_widths[1])
            self.__mask_draw.ellipse((start, end), outline=1, fill=0, width=self.line_widths[1])

    def paste_outer_circle(self, image: Image.Image) -> None:
        image.paste(self.__border_image, mask=self.__mask_image)
