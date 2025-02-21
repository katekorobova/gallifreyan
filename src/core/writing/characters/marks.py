
import math
from abc import ABC, abstractmethod
from random import uniform
from typing import Optional

from PIL.Image import Image
from PIL.ImageDraw import ImageDraw

from . import InteractiveCharacter, CharacterType
from ..common import DistanceInfo
from ..common.circles import OuterCircle, InnerCircle
from ...utils import Point, create_empty_image, PressedType
from ....config import (WORD_IMAGE_RADIUS, DEFAULT_WORD_RADIUS, SYLLABLE_COLOR, SYLLABLE_BG,
                        MARK_INITIAL_SCALE_MIN, MARK_INITIAL_SCALE_MAX,
                        MARK_SCALE_MIN, MARK_SCALE_MAX,
                        INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX,
                        INNER_CIRCLE_SCALE_MIN, INNER_CIRCLE_SCALE_MAX)


class Mark(InteractiveCharacter, ABC):
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    color = SYLLABLE_COLOR
    background = SYLLABLE_BG

    def __init__(self, text: str, character_type: CharacterType, borders: str):
        super().__init__(text, character_type)
        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(distance_info)
        self.inner_circle = InnerCircle(distance_info)
        self.outer_circle.initialize(borders)
        self.inner_circle.initialize(borders)

        self._image, self._draw = create_empty_image()
        self._image_ready = False

        # Scale, radius, and positioning attributes
        self._scale = 1.0
        self._inner_scale = uniform(INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX)

    # =============================================
    # Pressing
    # =============================================
    @abstractmethod
    def press(self, point: Point) -> Optional[PressedType]:
        return None

    def _handle_outer_border_press(self, distance: float) -> Optional[PressedType]:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self._pressed_type = PressedType.OUTER_CIRCLE
            self._distance_bias = distance - self.outer_circle.radius
            return self._pressed_type
        return None

    def _handle_inner_space_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events inside the inner circle."""
        if self.inner_circle.inside_circle(point.distance()):
            return self._handle_parent_press(point)
        return None

    def _handle_inner_border_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events on the inner border."""
        distance = point.distance()
        if self.inner_circle.on_circle(distance):
            self._pressed_type = PressedType.INNER_CIRCLE
            self._distance_bias = distance - self.inner_circle.radius
            return self._pressed_type
        return None

    def _handle_parent_press(self, point: Point) -> Optional[PressedType]:
        """Handle press events for the parent."""
        self._pressed_type = PressedType.SELF
        self._position_bias = point
        return self._pressed_type

    # =============================================
    # Repositioning
    # =============================================
    @abstractmethod
    def move(self, point: Point) -> None:
        pass

    # =============================================
    # Resizing
    # =============================================
    def _adjust_inner_scale(self, distance: float) -> None:
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        scale = new_radius / self.outer_circle.radius
        self._inner_scale = min(max(scale, INNER_CIRCLE_SCALE_MIN), INNER_CIRCLE_SCALE_MAX)
        self._update_after_changing_inner_circle()


    def _update_after_resizing(self):
        """Update properties after resizing."""
        self.distance_info.scale_distance(self._scale)
        self.outer_circle.scale_borders(self._scale)
        self.outer_circle.set_radius(self._scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)
        self._update_after_changing_inner_circle()

    def _update_after_changing_inner_circle(self):
        """Update properties after changing inner circle."""
        self.inner_circle.scale_borders(self._scale)
        self.inner_circle.set_radius(self._scale * self._inner_scale * DEFAULT_WORD_RADIUS)
        self.inner_circle.create_circle(self.color, self.background)
        self._image_ready = False

    # =============================================
    # Drawing
    # =============================================
    def _create_image(self) -> None:
        """Draw the mark."""
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)
        self.outer_circle.paste_circle(self._image)
        self.inner_circle.redraw_circle(self._draw)
        self._image_ready = True

    def apply_color_changes(self) -> None:
        self.outer_circle.create_circle(self.color, self.background)
        self.inner_circle.create_circle(self.color, self.background)
        self._image_ready = False



class PunctuationMark(Mark):
    def __init__(self, text: str, borders: str):
        super().__init__(text, CharacterType.PUNCTUATION_MARK, borders)
        self._set_scale(uniform(MARK_INITIAL_SCALE_MIN, MARK_INITIAL_SCALE_MAX))

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle press events at a given point."""
        distance = point.distance()
        if self.outer_circle.outside_circle(distance):
            return None

        return (self._handle_outer_border_press(distance) or
                self._handle_inner_space_press(point) or
                self._handle_inner_border_press(point) or
                self._handle_parent_press(point))

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point) -> None:
        """Move the mark based on the provided point and number group's radius."""
        distance = point.distance()
        match self._pressed_type:
            case PressedType.INNER_CIRCLE:
                self._adjust_inner_scale(distance)
            case PressedType.OUTER_CIRCLE:
                self._adjust_scale(distance)

    # =============================================
    # Resizing
    # =============================================
    def _set_scale(self, scale: float) -> None:
        """Set the personal scale of the object and update properties accordingly."""
        self._scale = scale
        self._update_after_resizing()

    def _adjust_scale(self, distance: float) -> None:
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        scale = new_radius / DEFAULT_WORD_RADIUS
        self._set_scale(min(max(scale, MARK_SCALE_MIN), MARK_SCALE_MAX))

    # =============================================
    # Drawing
    # =============================================
    def get_image(self) -> Image:
        if not self._image_ready:
            self._create_image()
        return self._image

    def redraw(self, image: Image, draw: ImageDraw) -> None:
        raise NotImplementedError()


class NumberMark(Mark):
    def __init__(self, text: str, borders: str):
        super().__init__(text, CharacterType.NUMBER_MARK, borders)

        self._center = Point()
        self._dependent = False
        self._parent_scale = 1.0
        self._personal_scale = 1.0
        self._parent_outer_circle: Optional[OuterCircle] = None
        self._set_personal_scale(uniform(MARK_INITIAL_SCALE_MIN, MARK_INITIAL_SCALE_MAX))

        self._direction = 0.0
        self._set_direction(uniform(-math.pi, math.pi))

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle press events at a given point."""
        shifted = point - self._center
        distance = shifted.distance()

        if self.outer_circle.outside_circle(distance):
            return None

        return (self._handle_outer_border_press(distance) or
                self._handle_inner_space_press(shifted) or
                self._handle_inner_border_press(shifted) or
                self._handle_parent_press(shifted))

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point) -> None:
        """Move the mark based on the provided point and number group's radius."""
        shifted = point - self._center
        distance = shifted.distance()
        match self._pressed_type:
            case PressedType.INNER_CIRCLE:
                self._adjust_inner_scale(distance)
            case PressedType.OUTER_CIRCLE:
                self._adjust_personal_scale(distance)
            case PressedType.SELF:
                self._adjust_direction(point)

    def _calculate_center(self) -> None:
        if self._dependent:
            radius = self._parent_outer_circle.radius
            self._center = Point(math.cos(self._direction) * radius, math.sin(self._direction) * radius)
        else:
            self._center = Point()

    # =============================================
    # Resizing
    # =============================================
    def initialize_parent(self, parent_outer_circle: Optional[OuterCircle], parent_scale: float) -> None:
        self._parent_outer_circle = parent_outer_circle
        self._parent_scale = parent_scale
        self._dependent = False
        self._calculate_center()
        self._update_after_resizing()

    def set_dependent(self, dependent: bool) -> None:
        if self._dependent != dependent:
            self._dependent = dependent
            self._calculate_center()
            self._update_after_resizing()

    def set_parent_scale(self, parent_scale: float) -> None:
        """Update the scale based on the parent scale."""
        self._parent_scale = parent_scale
        self._calculate_center()
        self._update_after_resizing()

    def _set_personal_scale(self, scale: float) -> None:
        """Set the personal scale of the object and update properties accordingly."""
        self._personal_scale = scale
        self._update_after_resizing()

    def _adjust_personal_scale(self, distance: float) -> None:
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        if self._dependent:
            scale = new_radius / DEFAULT_WORD_RADIUS / self._parent_scale
        else:
            scale = new_radius / DEFAULT_WORD_RADIUS
        self._set_personal_scale(min(max(scale, MARK_SCALE_MIN), MARK_SCALE_MAX))

    def _update_after_resizing(self):
        """Update properties after resizing."""
        if self._dependent:
            self._scale = self._parent_scale * self._personal_scale
        else:
            self._scale = self._personal_scale
        super()._update_after_resizing()

    # =============================================
    # Rotation
    # =============================================
    def _set_direction(self, direction: float):
        """Set the direction of the number mark."""
        self._direction = direction
        self._calculate_center()

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the number mark."""
        adjusted_point = point - self._position_bias
        self._set_direction(adjusted_point.direction())

    # =============================================
    # Drawing
    # =============================================
    def redraw(self, image: Image, draw: ImageDraw) -> None:
        if not self._image_ready:
            self._create_image()
        image.paste(self._image, self._center.tuple(), mask=self._image)

    def perform_animation(self, angle: float):
        self._set_direction(self._direction + angle)
