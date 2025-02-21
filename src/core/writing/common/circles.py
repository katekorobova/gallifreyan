from typing import Optional

from PIL.Image import Image
from PIL.ImageDraw import ImageDraw

from . import DistanceInfo, BorderInfo
from ...utils import create_empty_image, ensure_min_radius, IMAGE_CENTER, get_bounds


class OuterCircle:
    def __init__(self, distance_info: DistanceInfo):
        super().__init__()
        self.radius = 0.0
        self.distance_info = distance_info
        self.border_info: Optional[BorderInfo] = None

        self._border_image, self._border_draw = create_empty_image()
        self._mask_image, self._mask_draw = create_empty_image('1')

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
        self._border_draw.rectangle(((0, 0), self._border_image.size), fill=0)
        self._mask_draw.rectangle(((0, 0), self._mask_image.size), fill=1)

        line_widths = self.border_info.line_widths
        half_line_widths = self.border_info.half_line_widths
        if self.num_borders() > 1:
            adjusted_radius = (self.radius + 2 * self.distance_info.half_distance + half_line_widths[0])
            xy = get_bounds(IMAGE_CENTER, adjusted_radius)
            self._border_draw.ellipse(xy=xy, outline=color, fill=background, width=line_widths[0])

            adjusted_radius = self.radius + half_line_widths[1]
            xy = get_bounds(IMAGE_CENTER, adjusted_radius)
            self._border_draw.ellipse(xy=xy, outline=color, width=line_widths[1])
            self._mask_draw.ellipse(xy=xy, outline=1, fill=0, width=line_widths[1])
        else:
            adjusted_radius = self.radius + half_line_widths[0]
            xy = get_bounds(IMAGE_CENTER, adjusted_radius)
            self._border_draw.ellipse(xy=xy, outline=color, width=line_widths[0])
            self._mask_draw.ellipse(xy=xy, outline=1, fill=0, width=line_widths[0])

    def paste_circle(self, image: Image) -> None:
        image.paste(self._border_image, mask=self._mask_image)


class InnerCircle:
    def __init__(self, distance_info: DistanceInfo):
        super().__init__()
        self.radius = 0.0
        self.distance_info = distance_info
        self.border_info: Optional[BorderInfo] = None
        self._inner_circle_arg_dict: list[dict] = []

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

    def create_circle(self, color: str, background: str, mask_draw: ImageDraw = None):
        """Prepare arguments for drawing inner circles."""
        line_widths = self.border_info.line_widths
        half_line_widths = self.border_info.half_line_widths

        adjusted_radius = self.radius + half_line_widths[0]
        xy = get_bounds(IMAGE_CENTER, adjusted_radius)
        width = line_widths[0]
        self._inner_circle_arg_dict = [{'xy': xy, 'outline': color, 'fill': background, 'width': width}]

        if self.num_borders() > 1:
            adjusted_radius = ensure_min_radius(
                self.radius - 2 * self.distance_info.half_distance + half_line_widths[1])
            xy = get_bounds(IMAGE_CENTER, adjusted_radius)
            width = line_widths[1]
            self._inner_circle_arg_dict.append({'xy': xy, 'outline': color, 'fill': background, 'width': width})

        if mask_draw:
            mask_draw.ellipse(xy, outline=1, fill=0, width = width)

    def redraw_circle(self, draw: ImageDraw):
        """Draw the inner circle using predefined arguments."""
        for args in self._inner_circle_arg_dict:
            draw.ellipse(**args)


