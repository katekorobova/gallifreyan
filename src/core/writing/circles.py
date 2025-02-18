from itertools import repeat
from typing import Optional

from PIL import Image, ImageDraw

from ..utils import Point, create_empty_image, get_line_width, get_half_line_distance, ensure_min_radius


class DistanceInfo:
    def __init__(self):
        self.half_distance = 0.0

    def scale_distance(self, scale: float) -> None:
        self.half_distance = get_half_line_distance(scale)

class BorderInfo:
    def __init__(self, borders: str):
        self.borders = borders

        num_borders = len(borders)
        self.line_widths = list(repeat(0, num_borders))
        self.half_line_widths = list(repeat(0.0, num_borders))

    def scale_widths(self, scale: float) -> None:
        self.line_widths = [get_line_width(border, scale) for border in self.borders]
        self.half_line_widths = [width / 2 for width in self.line_widths]

class OuterCircle:
    def __init__(self, image_center: Point, distance_info: DistanceInfo):
        super().__init__()
        self.radius = 0.0
        self.distance_info = distance_info
        self.border_info: Optional[BorderInfo] = None

        self.__image_center = image_center
        self.__border_image, self.__border_draw = create_empty_image(image_center)
        self.__mask_image, self.__mask_draw = create_empty_image(image_center, '1')

    def initialize(self, borders: str):
        self.border_info = BorderInfo(borders)

    def num_borders(self):
        return len(self.border_info.borders)

    def outside_circle(self, distance: float) -> bool:
        if self.num_borders() > 1:
            return distance > self.radius + 2 * self.distance_info.half_distance
        return distance > self.radius + self.distance_info.half_distance

    def on_circle(self, distance: float) -> bool:
        if self.num_borders() > 1:
            return distance > self.radius
        return distance > self.radius - self.distance_info.half_distance

    def scale_borders(self, scale: float) -> None:
        self.border_info.scale_widths(scale)

    def set_radius(self, radius: float) -> None:
        self.radius = radius

    def create_circle(self, color: str, background: str) -> None:
        """Create the outer circle representation."""
        self.__border_draw.rectangle(((0, 0), self.__border_image.size), fill=0)
        self.__mask_draw.rectangle(((0, 0), self.__mask_image.size), fill=1)

        line_widths = self.border_info.line_widths
        half_line_widths = self.border_info.half_line_widths
        if self.num_borders() > 1:
            adjusted_radius = (self.radius + 2 * self.distance_info.half_distance + half_line_widths[0])
            start = self.__image_center.shift(-adjusted_radius).tuple()
            end = self.__image_center.shift(adjusted_radius).tuple()
            self.__border_draw.ellipse((start, end), outline=color, fill=background, width=line_widths[0])

            adjusted_radius = self.radius + half_line_widths[1]
            start = self.__image_center.shift(-adjusted_radius).tuple()
            end = self.__image_center.shift(adjusted_radius).tuple()
            self.__border_draw.ellipse((start, end), outline=color, width=line_widths[1])
            self.__mask_draw.ellipse((start, end), outline=1, fill=0, width=line_widths[1])
        else:
            adjusted_radius = self.radius + half_line_widths[0]
            start = self.__image_center.shift(-adjusted_radius).tuple()
            end = self.__image_center.shift(adjusted_radius).tuple()
            self.__border_draw.ellipse((start, end), outline=color, width=line_widths[0])
            self.__mask_draw.ellipse((start, end), outline=1, fill=0, width=line_widths[0])

    def paste_circle(self, image: Image.Image) -> None:
        image.paste(self.__border_image, mask=self.__mask_image)


class InnerCircle:
    def __init__(self, image_center: Point, distance_info: DistanceInfo):
        super().__init__()
        self.radius = 0.0
        self.distance_info = distance_info
        self.border_info: Optional[BorderInfo] = None

        self.__image_center = image_center
        self.__inner_circle_arg_dict: list[dict] = []

    def initialize(self, borders: str):
        self.border_info = BorderInfo(borders)

    def num_borders(self):
        return len(self.border_info.borders)

    def inside_circle(self, distance: float) -> bool:
        if self.num_borders() > 1:
            return distance < self.radius - 2 * self.distance_info.half_distance
        return distance < self.radius - self.distance_info.half_distance

    def on_circle(self, distance: float) -> bool:
        if self.num_borders() > 1:
            return distance < self.radius
        return distance < self.radius + self.distance_info.half_distance

    def set_radius(self, radius: float) -> None:
        self.radius = radius

    def scale_borders(self, scale: float) -> None:
        self.border_info.scale_widths(scale)

    def create_circle(self, color: str, background: str, mask_draw: ImageDraw.ImageDraw = None):
        """Prepare arguments for drawing inner circles."""
        line_widths = self.border_info.line_widths
        half_line_widths = self.border_info.half_line_widths

        adjusted_radius = self.radius + half_line_widths[0]
        bounds = self._get_bounds(adjusted_radius)
        width = line_widths[0]
        self.__inner_circle_arg_dict = [{'xy': bounds, 'outline': color, 'fill': background, 'width': width}]

        if self.num_borders() > 1:
            adjusted_radius = ensure_min_radius(
                self.radius - 2 * self.distance_info.half_distance + half_line_widths[1])
            bounds = self._get_bounds(adjusted_radius)
            width = line_widths[1]
            self.__inner_circle_arg_dict.append({'xy': bounds, 'outline': color, 'fill': background, 'width': width})

        if mask_draw:
            mask_draw.ellipse(bounds, outline=1, fill=0, width = width)

    def _get_bounds(self, adjusted_radius: float) -> tuple[tuple[int, int], tuple[int, int]]:
        """Generate circle arguments for drawing."""
        start = self.__image_center.shift(-adjusted_radius).tuple()
        end = self.__image_center.shift(adjusted_radius).tuple()
        return start, end

    def redraw_circle(self, draw: ImageDraw.ImageDraw):
        """Draw the inner circle using predefined arguments."""
        for args in self.__inner_circle_arg_dict:
            draw.ellipse(**args)


