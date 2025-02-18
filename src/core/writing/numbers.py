from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass
from itertools import repeat, count
from typing import Optional

from PIL import Image, ImageTk

from .characters import Character, CharacterType
from .circles import OuterCircle, DistanceInfo, InnerCircle
from .digits import Digit
from .words import Token
from ..tools import AnimationProperties
from ..utils import Point, PressedType, create_empty_image, ensure_min_radius
from ...config import (SYLLABLE_COLOR, SYLLABLE_BG, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT,
                       WORD_IMAGE_RADIUS, DEFAULT_WORD_RADIUS, MINUS_SIGN,
                       SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX,
                       SYLLABLE_SCALE_MAX, SYLLABLE_SCALE_MIN,
                       INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX,
                       INNER_CIRCLE_SCALE_MIN, INNER_CIRCLE_SCALE_MAX, NUMBER_BORDERS)


@dataclass
class _RedistributionState:
    """Represents the state during number group redistribution."""
    group: Optional[NumberGroup] = None
    completed = False


def unique_groups(items: list[NumberGroup]) -> list[NumberGroup]:
    """Return a list of unique number groups while preserving order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item))]


class NumberMark(Character):
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    color = SYLLABLE_COLOR
    background = SYLLABLE_BG

    def __init__(self, text: str, borders: str):
        super().__init__(text, CharacterType.NUMBER_MARK)
        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(self.IMAGE_CENTER, distance_info)
        self.inner_circle = InnerCircle(self.IMAGE_CENTER, distance_info)
        self.outer_circle.initialize(borders)
        self.inner_circle.initialize(borders)
        self._image, self._draw = create_empty_image(self.IMAGE_CENTER)

        # Scale, radius, and positioning attributes
        self.scale = 0.0
        self._parent_scale = 1.0
        self._personal_scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self._inner_scale = random.uniform(INNER_CIRCLE_INITIAL_SCALE_MIN, INNER_CIRCLE_INITIAL_SCALE_MAX)
        self._update_after_resizing()

        self.direction = 0
        self._set_direction(random.uniform(-math.pi, math.pi))

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    # =============================================
    # Pressing
    # =============================================
    def press(self, point: Point) -> bool:
        """Handle press events at a given point."""
        distance = point.distance()
        if self.outer_circle.outside_circle(distance):
            return False

        return (self._handle_outer_border_press(distance) or
                self._handle_inner_space_press(point) or
                self._handle_inner_border_press(point) or
                self._handle_parent_press(point))

    def _handle_outer_border_press(self, distance: float) -> bool:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self.pressed_type = PressedType.BORDER
            self._distance_bias = distance - self.outer_circle.radius
            return True
        return False

    def _handle_inner_space_press(self, point: Point) -> bool:
        """Handle press events inside the inner circle."""
        if self.inner_circle.inside_circle(point.distance()):
            return self._handle_parent_press(point)
        return False

    def _handle_inner_border_press(self, point: Point) -> bool:
        """Handle press events on the inner border."""
        distance = point.distance()
        if self.inner_circle.on_circle(distance):
            self.pressed_type = PressedType.INNER
            self._distance_bias = distance - self.inner_circle.radius
            return True
        return False

    def _handle_parent_press(self, point: Point) -> bool:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = point
        return True

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point, radius=0.0) -> None:
        """Move the object based on the provided point and number's radius."""
        shifted = point - Point(math.cos(self.direction) * radius, math.sin(self.direction) * radius)
        distance = shifted.distance()

        match self.pressed_type:
            case PressedType.INNER:
                self._adjust_inner_scale(distance)
            case PressedType.BORDER:
                self._adjust_scale(distance)
            case PressedType.PARENT:
                if radius:
                    self._adjust_direction(point)

    # =============================================
    # Resizing
    # =============================================
    def set_scale(self, scale: float) -> None:
        """Set the personal scale of the object and update properties accordingly."""
        self._personal_scale = scale
        self._update_after_resizing()

    def update_scale(self, parent_scale=1.0) -> None:
        """Update the scale based on the parent scale."""
        self._parent_scale = parent_scale
        self._update_after_resizing()

    def _adjust_scale(self, distance: float) -> None:
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_scale(min(max(new_radius / DEFAULT_WORD_RADIUS / self._parent_scale,
                               SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def _adjust_inner_scale(self, distance: float) -> None:
        """Adjust the inner scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self._inner_scale = min(max(new_radius / self.outer_circle.radius, INNER_CIRCLE_SCALE_MIN), INNER_CIRCLE_SCALE_MAX)
        self._update_after_changing_inner_circle()

    def _update_after_resizing(self):
        """Update properties after resizing."""
        self.scale = self._parent_scale * self._personal_scale
        self.distance_info.scale_distance(self.scale)
        self.outer_circle.scale_borders(self.scale)
        self.outer_circle.set_radius(self.scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)
        self._update_after_changing_inner_circle()

    def _update_after_changing_inner_circle(self):
        """Update properties after changing inner circle."""
        self.inner_circle.scale_borders(self.scale)
        self.inner_circle.set_radius(self.scale * self._inner_scale * DEFAULT_WORD_RADIUS)
        self.inner_circle.create_circle(self.color, self.background)
        self._redraw()

    # =============================================
    # Rotation
    # =============================================
    def _set_direction(self, direction: float):
        """Set the direction of the number mark."""
        self.direction = direction

    def _adjust_direction(self, point: Point):
        """Adjust the direction of the number mark."""
        adjusted_point = point - self._point_bias
        self._set_direction(adjusted_point.direction())

    # =============================================
    # Drawing
    # =============================================
    def get_image(self) -> Image.Image:
        return self._image

    def _redraw(self):
        """Draw the mark."""
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)
        self.outer_circle.paste_circle(self._image)
        self.inner_circle.redraw_circle(self._draw)

    def apply_color_changes(self):
        self.outer_circle.create_circle(self.color, self.background)
        self.inner_circle.create_circle(self.color, self.background)
        self._redraw()

    def perform_animation(self, direction_sign: int):
        delta = direction_sign * 2 * math.pi / AnimationProperties.cycle
        self._set_direction(self.direction + delta)


class NumberGroup:
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    background = SYLLABLE_BG
    color = SYLLABLE_COLOR

    def __init__(self, digits: list[Digit]):
        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(self.IMAGE_CENTER, distance_info)
        self.outer_circle.initialize(NUMBER_BORDERS)

        self.center = Point(random.randint(DEFAULT_WORD_RADIUS, DEFAULT_CANVAS_WIDTH - DEFAULT_WORD_RADIUS),
                            random.randint(DEFAULT_WORD_RADIUS, DEFAULT_CANVAS_HEIGHT - DEFAULT_WORD_RADIUS))
        self.digits = digits
        self._minus_sign: Optional[NumberMark] = None
        self._number_mark: Optional[NumberMark] = None
        self._update_text()

        # Image-related attributes
        self._image, self._draw = create_empty_image(self.IMAGE_CENTER)
        self._image_tk = ImageTk.PhotoImage(image=self._image)
        self.canvas_item_id = None
        self._image_ready = False

        # Scale, radius, and positioning attributes
        self.scale = random.uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self.inner_scale = 1
        self._update_after_resizing()

        # Interaction properties
        self.pressed_type: Optional[PressedType] = None
        self._pressed: Optional[Digit | NumberMark] = None
        self._distance_bias = 0.0
        self._point_bias = Point()

    def _update_text(self) -> None:
        """Update the number group's text representation based on its characters."""
        self.text = ((self._minus_sign.text if self._minus_sign else '') +
                     (''.join(digit.text for digit in self.digits)) +
                     (self._number_mark.text if self._number_mark else ''))

    def add(self, character: Character) -> bool:
        if isinstance(character, Digit):
            if self._number_mark:
                return False

            self.digits.append(character)
            character.scale_borders(self.scale)
            self._update_digits()

        elif isinstance(character, NumberMark):
            if character.text == MINUS_SIGN:
                if self._minus_sign or self.digits or self._number_mark:
                    return False
                self._minus_sign = character
                self._minus_sign.update_scale(self.scale)
            else:
                if self._number_mark:
                    return False
                self._number_mark = character
                self._number_mark.update_scale(self.scale)
            self._image_ready = False
        else:
            return False

        self._update_text()
        return True

    # =============================================
    # Deletion
    # =============================================
    def remove_starting_with(self, character: Character):
        """Remove a character from the number group, updating properties accordingly."""
        if character == self._minus_sign:
            self.digits = []
            self._minus_sign = None
            self._number_mark = None
            self._update_digits()
        elif character == self._number_mark:
            self._number_mark = None
            self._image_ready = False
        elif character in self.digits:
            index = self.digits.index(character)
            self._number_mark = None
            self.digits[index:] = []
            self._update_digits()
        else:
            raise ValueError(f"Letter '{character.text}' not found in syllable '{self.text}'")
        self._update_text()

    def set_scale(self, scale: float):
        """Set the scale of the number group and update properties accordingly."""
        self.scale = scale
        self._update_after_resizing()

    def _adjust_scale(self, distance: float):
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_scale(min(max(new_radius / DEFAULT_WORD_RADIUS, SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def _update_after_resizing(self):
        """Update properties after resizing."""
        self.distance_info.scale_distance(self.scale)
        self.outer_circle.scale_borders(self.scale)
        self.outer_circle.set_radius(self.scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)

        if self._minus_sign:
            self._minus_sign.update_scale(self.scale)

        if self._number_mark:
            self._number_mark.update_scale(self.scale)

        for digit in self.digits:
            digit.scale_borders(self.scale)
        self._update_digits()

    def _update_digits(self) -> None:
        if not self.digits:
            return

        line_distance = 2 * self.distance_info.half_distance
        double_border_digits = [digit for digit in self.digits if digit.inner_circle.num_borders() > 1]
        border_space_width = len(double_border_digits) * line_distance
        base_inner_radius = 0.0
        for i, digit in enumerate(reversed(self.digits)):
            base_stripe_width = ensure_min_radius(self.outer_circle.radius - base_inner_radius - border_space_width) / (len(self.digits) - i + 1)
            digit.update_inner_radius(base_inner_radius, base_stripe_width)
            base_inner_radius = digit.inner_circle.radius
            if digit in double_border_digits:
                border_space_width -= line_distance

        outer_radius = self.outer_circle.radius
        border_info = self.outer_circle.border_info
        for digit in self.digits:
            digit.update_outer_radius(outer_radius, border_info)
            outer_radius = digit.inner_circle.radius
            border_info = digit.inner_circle.border_info
            if digit in double_border_digits:
                outer_radius = ensure_min_radius(outer_radius - line_distance)

        self._image_ready = False

    def press(self, point: Point) -> bool:
        syllable_point = point - self.center
        if self.outer_circle.outside_circle(syllable_point.distance()):
            return False

        return (self._handle_outer_border_press(syllable_point) or
                self._handle_number_mark_press(syllable_point) or
                self._handle_minus_sign_press(syllable_point) or
                self._handle_digit_press(syllable_point) or
                self._handle_parent_press(syllable_point))

    def _handle_outer_border_press(self, point: Point) -> bool:
        """Handle press events on the outer border."""
        distance = point.distance()
        if self.outer_circle.on_circle(distance):
            self.pressed_type = PressedType.BORDER
            self._distance_bias = distance - self.outer_circle.radius
            return True
        return False

    def _handle_number_mark_press(self, word_point: Point) -> bool:
        """Attempt to press the number mark."""
        if self._number_mark:
            return self._handle_mark_press(word_point, self._number_mark)
        return False

    def _handle_minus_sign_press(self, word_point: Point) -> bool:
        """Attempt to press the minus sign."""
        if self._minus_sign:
            return self._handle_mark_press(word_point, self._minus_sign)
        return False

    def _handle_mark_press(self, word_point: Point, mark: NumberMark) -> bool:
        """Attempt to press the number mark."""
        offset_point = word_point - Point(math.cos(mark.direction) * self.outer_circle.radius,
                                          math.sin(mark.direction) * self.outer_circle.radius)
        if mark.press(offset_point):
            self._pressed = mark
            self.pressed_type = PressedType.CHILD
            return True
        return False

    def _handle_digit_press(self, word_point: Point) -> bool:
        """Attempt to press a digit."""
        for digit in reversed(self.digits):
            if digit.press(word_point):
                self._pressed = digit
                self.pressed_type = PressedType.CHILD
                return True
        return False

    def _handle_parent_press(self, word_point: Point) -> bool:
        """Handle press events for the parent."""
        self.pressed_type = PressedType.PARENT
        self._point_bias = word_point
        return True

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point):
        """Handle move events."""
        word_point = point - self.center
        distance = word_point.distance()
        match self.pressed_type:
            case PressedType.BORDER:
                self._adjust_scale(distance)
            case PressedType.PARENT:
                self.center = point - self._point_bias
            case PressedType.CHILD:
                self._move_child(word_point)
            case _:
                return
        self._image_ready = False

    def _move_child(self, word_point: Point):
        """Move a pressed child syllable."""
        if isinstance(self._pressed, NumberMark):
            self._pressed.move(word_point, self.outer_circle.radius)
        else:
            self._pressed.move(word_point)
            self._update_digits()

    # =============================================
    # Helper Functions for Updating Image Arguments
    # =============================================
    def _create_circle_args(self, adjusted_radius: float, width: float) -> dict:
        """Generate circle arguments for drawing."""
        start = self.IMAGE_CENTER.shift(-adjusted_radius).tuple()
        end = self.IMAGE_CENTER.shift(adjusted_radius).tuple()
        return {'xy': (start, end), 'outline': self.color, 'fill': self.background, 'width': width}

    # =============================================
    # Drawing
    # =============================================
    def _create_image(self):
        """Generate the syllable image."""
        # Clear the image
        self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

        for digit in reversed(self.digits):
            digit.paste_image(self._image)

        if self._minus_sign:
            self._paste_mark(self._minus_sign)

        if self._number_mark:
            self._paste_mark(self._number_mark)

        # Paste the outer circle image
        self.outer_circle.paste_circle(self._image)
        self._image_ready = True

    def _paste_mark(self, mark: NumberMark):
        mark_image = mark.get_image()
        xy = (self.IMAGE_CENTER - mark.IMAGE_CENTER +
              Point(math.cos(mark.direction) * self.outer_circle.radius,
                    math.sin(mark.direction) * self.outer_circle.radius)).tuple()
        self._image.paste(mark_image, xy, mark_image)

    def paste_image(self, image: Image.Image, position: Point):
        """Create and display the number group image on the canvas."""
        if not self._image_ready:
            self._create_image()
        image.paste(self._image, (self.center - self.IMAGE_CENTER - position).tuple(), self._image)

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]):
        """Create and display the number group image on the canvas."""
        if self._image_ready:
            if self.canvas_item_id is None:
                self._image_tk.paste(self._image)
                self.canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)
            else:
                canvas.tag_raise(self.canvas_item_id)
                to_be_removed.remove(self.canvas_item_id)
        else:
            self._create_image()
            self._image_tk.paste(self._image)
            self.canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)

    def apply_color_changes(self):
        """Apply color changes to the number group."""
        self.outer_circle.create_circle(self.color, self.background)
        for digit in self.digits:
            digit.apply_color_changes()
        if self._minus_sign:
            self._minus_sign.apply_color_changes()
        if self._number_mark:
            self._number_mark.apply_color_changes()
        self._image_ready = False

    def perform_animation(self, direction_sign: int):
        """Perform an animation step, changing the digits' directions."""
        new_direction_sign = direction_sign
        for digit in self.digits:
            digit.perform_animation(new_direction_sign)
            new_direction_sign = -new_direction_sign

        if self._minus_sign:
            self._minus_sign.perform_animation(direction_sign)

        if self._number_mark:
            self._number_mark.perform_animation(-direction_sign)

        self._image_ready = False


class Number(Token):
    def __init__(self, characters: list[Character]):
        """Initialize a Number instance with characters."""
        super().__init__()

        # Initialize syllables and their relationships
        self.groups: list[NumberGroup] = []
        self.groups_by_indices: list[Optional[NumberGroup]] = []
        self.insert_characters(0, characters)

        # Interaction properties
        self._pressed_group: Optional[NumberGroup] = None

    # =============================================
    # Interaction
    # =============================================
    def press(self, point: Point) -> bool:
        """Handle press events."""
        for group in reversed(self.groups):
            if group.press(point):
                self._pressed_group = group
                return True
        return False

    def move(self, point: Point):
        """Handle move events."""
        self._pressed_group.move(point)

    # =============================================
    # Insertion and Deletion
    # =============================================
    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index and update syllables."""
        if not all(character.character_type & CharacterType.NUMBER for character in characters):
            return False

        self._split_group(index)

        super().insert_characters(index, characters)
        self.groups_by_indices[index: index] = repeat(None, len(characters))

        start = self._absorb_following(index)
        self._redistribute(start)
        self.groups = unique_groups(self.groups_by_indices)
        return True

    def remove_characters(self, index: int, end_index: int):
        """Remove characters from the word and update syllables."""
        self._split_group(index)
        self._split_group(end_index)

        super().remove_characters(index, end_index)
        self.groups_by_indices[index: end_index] = []

        start = self._absorb_following(index)
        self._redistribute(start)
        self.groups = unique_groups(self.groups_by_indices)

    def remove_starting_with(self, index: int):
        """Remove characters from the number, updating properties accordingly."""
        self._split_group(index)

        super().remove_starting_with(index)
        self.groups_by_indices[index:] = []
        self.groups = unique_groups(self.groups_by_indices)

    def _split_group(self, index: int):
        """Split the number group at the specified index."""
        if index > 0:
            group = self.groups_by_indices[index - 1]
            if index < len(self.characters) and group and group is self.groups_by_indices[index]:
                group.remove_starting_with(self.characters[index])
                for i in range(index, len(self.characters)):
                    if group is self.groups_by_indices[i]:
                        self.groups_by_indices[i] = None
                    else:
                        break

    def _absorb_following(self, index: int) -> int:
        """Absorb newly inserted characters into existing number groups."""
        start = index
        if index > 0:
            group = self.groups_by_indices[index - 1]
            for i in range(index, len(self.characters)):
                if group.add(self.characters[i]):
                    self.groups_by_indices[i] = group
                    start = i + 1
                else:
                    break
        return start

    def _redistribute(self, start: int) -> None:
        """Redistribute number groups starting from a given index."""
        state = _RedistributionState()
        for i, character in zip(count(start), self.characters[start:]):
            if isinstance(character, Digit):
                self._process_digit(i, character, state)
            elif isinstance(character, NumberMark):
                if character.text == MINUS_SIGN:
                    self._process_minus(i, character, state)
                else:
                    self._process_mark(i, character, state)
            else:
                raise ValueError(f"No such character: '{character.text}'")
            if state.completed:
                break

    def _process_digit(self, index: int, digit: Digit, state: _RedistributionState) -> None:
        """Process digit and update state."""
        if state.group:
            state.group.add(digit)
        else:
            if self.groups_by_indices[index]:
                state.completed = True
                return

            state.group = NumberGroup([digit])
        self.groups_by_indices[index] = state.group

    def _process_minus(self, index: int, minus: NumberMark, state: _RedistributionState) -> None:
        """Process minus character and update state."""
        if self.groups_by_indices[index]:
            state.completed = True
            return

        state.group = NumberGroup([])
        state.group.add(minus)
        self.groups_by_indices[index] = state.group

    def _process_mark(self, index: int, mark: NumberMark, state: _RedistributionState) -> None:
        """Process number mark and update state."""
        if not state.group:
            if self.groups_by_indices[index]:
                state.completed = True
                return

            state.group = NumberGroup([])

        state.group.add(mark)
        self.groups_by_indices[index] = state.group
        state.group = None

    def paste_image(self, image: Image.Image, position: Point):
        """Paste the number onto the given image."""
        for group in self.groups:
            group.paste_image(image, position)

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]):
        """Display the number on the canvas."""
        for group in self.groups:
            group.put_image(canvas, to_be_removed)

    def apply_color_changes(self):
        """Apply color changes to the number."""
        for group in self.groups:
            group.apply_color_changes()

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self, direction_sign: int):
        """Perform an animation step, changing number groups' directions."""
        for group in self.groups:
            group.perform_animation(direction_sign)
            direction_sign = -direction_sign
