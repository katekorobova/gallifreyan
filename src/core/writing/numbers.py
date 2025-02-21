from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from itertools import repeat, count
from random import uniform
from typing import Optional

from PIL import ImageTk
from PIL.Image import Image
from PIL.ImageDraw import ImageDraw

from .characters import Character, CharacterType, InteractiveCharacter, TokenType
from .characters.digits import Digit
from .characters.marks import NumberMark
from .common import CanvasItem
from .common.circles import OuterCircle, DistanceInfo
from .words import InteractiveToken
from ..utils import Point, PressedType, create_empty_image, ensure_min_radius, random_position, IMAGE_CENTER
from ...config import (SYLLABLE_COLOR, SYLLABLE_BG, WORD_IMAGE_RADIUS, DEFAULT_WORD_RADIUS, MINUS_SIGN,
                       SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX,
                       SYLLABLE_SCALE_MAX, SYLLABLE_SCALE_MIN, NUMBER_BORDERS)


@dataclass
class _RedistributionState:
    """Represents the state during number group redistribution."""
    group: Optional[NumberGroup] = None
    completed = False


def unique_groups(items: list[NumberGroup]) -> list[NumberGroup]:
    """Return a list of unique number groups while preserving order."""
    seen = set()
    return [item for item in items if not (item in seen or seen.add(item))]


class NumberGroup(CanvasItem):
    IMAGE_CENTER = Point(WORD_IMAGE_RADIUS, WORD_IMAGE_RADIUS)
    background = SYLLABLE_BG
    color = SYLLABLE_COLOR

    def __init__(self, character: Character):
        super().__init__()
        distance_info = DistanceInfo()
        self.distance_info = distance_info
        self.outer_circle = OuterCircle(distance_info)
        self.outer_circle.initialize(NUMBER_BORDERS)

        self.center = random_position()
        self.digits: list[Digit] = []
        self._minus_sign: Optional[NumberMark] = None
        self._number_mark: Optional[NumberMark] = None
        self._proper_number = False

        # Image-related attributes
        self._image, self._draw = create_empty_image()
        self._image_tk = ImageTk.PhotoImage(image=self._image)
        self._canvas_item_id = None
        self._image_ready = False

        # Scale, radius, and positioning attributes
        self._scale = uniform(SYLLABLE_INITIAL_SCALE_MIN, SYLLABLE_INITIAL_SCALE_MAX)
        self._update_after_resizing()
        self.add(character)

        # Interaction properties
        self._pressed_character: Optional[InteractiveCharacter] = None

    def _set_proper_number(self):
        proper_number = bool(self.digits or self._minus_sign and self._number_mark)
        self._proper_number = proper_number
        if self._minus_sign:
            self._minus_sign.set_dependent(proper_number)
        if self._number_mark:
            self._number_mark.set_dependent(proper_number)

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
            character.scale_borders(self._scale)
            self._update_digits()
        elif isinstance(character, NumberMark):
            if character.text == MINUS_SIGN:
                if self._minus_sign or self.digits or self._number_mark:
                    return False
                character.initialize_parent(self.outer_circle, self._scale)
                self._minus_sign = character
            else:
                if self._number_mark or self._minus_sign and not self.digits:
                    return False
                character.initialize_parent(self.outer_circle, self._scale)
                self._number_mark = character
        else:
            return False

        self._image_ready = False
        self._set_proper_number()
        self._update_text()
        return True

    # =============================================
    # Deletion
    # =============================================
    def remove_starting_with(self, character: Character):
        """Remove a character from the number group, updating properties accordingly."""
        if character == self._minus_sign:
            self._minus_sign = None
            self._number_mark = None
            self.digits = []
            self._update_digits()
        elif character == self._number_mark:
            self._number_mark = None
        elif character in self.digits:
            self._number_mark = None
            index = self.digits.index(character)
            self.digits[index:] = []
            self._update_digits()
        else:
            raise ValueError(f"Letter '{character.text}' not found in syllable '{self.text}'")

        self._image_ready = False
        self._set_proper_number()
        self._update_text()

    def set_scale(self, scale: float):
        """Set the scale of the number group and update properties accordingly."""
        self._scale = scale
        self._update_after_resizing()

    def _adjust_scale(self, distance: float):
        """Adjust the outer scale based on the moved distance."""
        new_radius = distance - self._distance_bias
        self.set_scale(min(max(new_radius / DEFAULT_WORD_RADIUS, SYLLABLE_SCALE_MIN), SYLLABLE_SCALE_MAX))

    def _update_after_resizing(self):
        """Update properties after resizing."""
        self.distance_info.scale_distance(self._scale)
        self.outer_circle.scale_borders(self._scale)
        self.outer_circle.set_radius(self._scale * DEFAULT_WORD_RADIUS)
        self.outer_circle.create_circle(self.color, self.background)

        if self._minus_sign:
            self._minus_sign.set_parent_scale(self._scale)

        if self._number_mark:
            self._number_mark.set_parent_scale(self._scale)

        for digit in self.digits:
            digit.scale_borders(self._scale)
        self._update_digits()
        self._image_ready = False

    def _update_digits(self) -> None:
        if not self.digits:
            return

        line_distance = 2 * self.distance_info.half_distance
        double_border_digits = [digit for digit in self.digits if digit.inner_circle.num_borders() > 1]
        border_space_width = len(double_border_digits) * line_distance
        base_inner_radius = 0.0
        for i, digit in enumerate(reversed(self.digits)):
            base_stripe_width = ensure_min_radius(
                self.outer_circle.radius - base_inner_radius - border_space_width) / (len(self.digits) - i + 1)
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

    def press(self, point: Point) -> Optional[PressedType]:
        number_point = point - self.center
        distance = number_point.distance()
        if self._proper_number:
            if self.outer_circle.outside_circle(distance):
                return None

            return (self._handle_outer_border_press(distance) or
                    self._handle_number_mark_press(number_point) or
                    self._handle_minus_sign_press(number_point) or
                    self._handle_digit_press(number_point) or
                    self._handle_parent_press(number_point))
        else:
            return (self._handle_number_mark_press(number_point) or
                    self._handle_minus_sign_press(number_point))

    def _handle_outer_border_press(self, distance: float) -> Optional[PressedType]:
        """Handle press events on the outer border."""
        if self.outer_circle.on_circle(distance):
            self._distance_bias = distance - self.outer_circle.radius
            self._pressed_type = PressedType.OUTER_CIRCLE
            return self._pressed_type
        return None

    def _handle_number_mark_press(self, number_point: Point) -> Optional[PressedType]:
        """Attempt to press the number mark."""
        if self._number_mark:
            return self._handle_mark_press(number_point, self._number_mark)
        return None

    def _handle_minus_sign_press(self, number_point: Point) -> Optional[PressedType]:
        """Attempt to press the minus sign."""
        if self._minus_sign:
            return self._handle_mark_press(number_point, self._minus_sign)
        return None

    def _handle_mark_press(self, number_point: Point, mark: NumberMark) -> Optional[PressedType]:
        """Attempt to press the number mark."""
        if self._proper_number:
            if mark.press(number_point):
                self._pressed_character = mark
                self._pressed_type = PressedType.CHILD
                return self._pressed_type
        else:
            mark_pressed_type = mark.press(number_point)
            if mark_pressed_type:
                if mark_pressed_type == PressedType.SELF:
                    self._position_bias = number_point
                    self._pressed_type = PressedType.SELF
                else:
                    self._pressed_character = mark
                    self._pressed_type = PressedType.CHILD
                return self._pressed_type
        return None

    def _handle_digit_press(self, word_point: Point) -> Optional[PressedType]:
        """Attempt to press a digit."""
        for digit in reversed(self.digits):
            if digit.press(word_point):
                self._pressed_character = digit
                self._pressed_type = PressedType.CHILD
                return self._pressed_type
        return None

    def _handle_parent_press(self, word_point: Point) -> Optional[PressedType]:
        """Handle press events for the parent."""
        self._pressed_type = PressedType.SELF
        self._position_bias = word_point
        return self._pressed_type

    # =============================================
    # Repositioning
    # =============================================
    def move(self, point: Point):
        """Handle move events."""
        word_point = point - self.center
        distance = word_point.distance()
        match self._pressed_type:
            case PressedType.OUTER_CIRCLE:
                self._adjust_scale(distance)
            case PressedType.SELF:
                self.center = point - self._position_bias
            case PressedType.CHILD:
                self._move_child(word_point)
            case _:
                return
        self._image_ready = False

    def _move_child(self, number_point: Point) -> None:
        """Move a pressed child syllable."""
        self._pressed_character.move(number_point)
        if self._pressed_character.character_type == CharacterType.DIGIT:
            self._update_digits()

    # =============================================
    # Helper Functions for Updating Image Arguments
    # =============================================
    def _create_circle_args(self, adjusted_radius: float, width: float) -> dict:
        """Generate circle arguments for drawing."""
        start = IMAGE_CENTER.shift(-adjusted_radius).tuple()
        end = IMAGE_CENTER.shift(adjusted_radius).tuple()
        return {'xy': (start, end), 'outline': self.color, 'fill': self.background, 'width': width}

    # =============================================
    # Drawing
    # =============================================
    def _create_image(self):
        """Generate the syllable image."""
        if self._proper_number:
            # Clear the image
            self._draw.rectangle(((0, 0), self._image.size), fill=self.background)

            for digit in reversed(self.digits):
                digit.redraw(self._image, self._draw)

            if self._minus_sign:
                self._minus_sign.redraw(self._image, self._draw)

            if self._number_mark:
                self._number_mark.redraw(self._image, self._draw)

            # Paste the outer circle image
            self.outer_circle.paste_circle(self._image)
        else:
            self._draw.rectangle(((0, 0), self._image.size), fill=0)

            if self._minus_sign:
                self._minus_sign.redraw(self._image, self._draw)

            if self._number_mark:
                self._number_mark.redraw(self._image, self._draw)
        self._image_ready = True

    def paste_image(self, image: Image, position: Point):
        """Create and display the number group image on the canvas."""
        if not self._image_ready:
            self._create_image()
        image.paste(self._image, (self.center - IMAGE_CENTER - position).tuple(), self._image)

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]):
        """Create and display the number group image on the canvas."""
        if self._image_ready:
            if self._canvas_item_id is None:
                self._image_tk.paste(self._image)
                self._canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)
            else:
                canvas.tag_raise(self._canvas_item_id)
                to_be_removed.remove(self._canvas_item_id)
        else:
            self._create_image()
            self._image_tk.paste(self._image)
            self._canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)

    def redraw(self, image: Image, draw: ImageDraw) -> None:
        raise NotImplementedError()

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

    def perform_animation(self, angle: float):
        """Perform an animation step, changing the digits' directions."""
        if self._proper_number:
            if self._minus_sign:
                self._minus_sign.perform_animation(angle)

            if self._number_mark:
                self._number_mark.perform_animation(-angle)

            digit_angle = 2 * angle
            for digit in self.digits:
                digit.perform_animation(digit_angle)
                digit_angle = -digit_angle

            self._image_ready = False


class Number(InteractiveToken):
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
    def press(self, point: Point) -> Optional[PressedType]:
        """Handle press events."""
        for group in reversed(self.groups):
            if group.press(point):
                self._pressed_group = group
                self._pressed_type = PressedType.SELF
                return self._pressed_type
        return None

    def move(self, point: Point):
        """Handle move events."""
        self._pressed_group.move(point)

    # =============================================
    # Insertion and Deletion
    # =============================================
    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        """Insert characters at the specified index and update syllables."""
        if not all(character.character_type.token_type == TokenType.NUMBER for character in characters):
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
        if not (state.group and state.group.add(digit)):
            if self.groups_by_indices[index]:
                state.completed = True
                return
            else:
                state.group = NumberGroup(digit)

        self.groups_by_indices[index] = state.group

    def _process_minus(self, index: int, minus: NumberMark, state: _RedistributionState) -> None:
        """Process minus character and update state."""
        if self.groups_by_indices[index]:
            state.completed = True
            return

        state.group = NumberGroup(minus)
        self.groups_by_indices[index] = state.group

    def _process_mark(self, index: int, mark: NumberMark, state: _RedistributionState) -> None:
        """Process number mark and update state."""
        if not (state.group and state.group.add(mark)):
            if self.groups_by_indices[index]:
                state.completed = True
                return
            else:
                state.group = NumberGroup(mark)
                state.group.add(mark)

        self.groups_by_indices[index] = state.group
        state.group = None

    def paste_image(self, image: Image, position: Point):
        """Paste the number onto the given image."""
        for group in self.groups:
            group.paste_image(image, position)

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]):
        """Display the number on the canvas."""
        for group in self.groups:
            group.put_image(canvas, to_be_removed)

    def redraw(self, image: Image, draw: ImageDraw) -> None:
        raise NotImplementedError()

    def apply_color_changes(self):
        """Apply color changes to the number."""
        for group in self.groups:
            group.apply_color_changes()

    # =============================================
    # Animation
    # =============================================
    def perform_animation(self, angle: float):
        """Perform an animation step, changing number groups' directions."""
        for group in self.groups:
            group.perform_animation(angle)
            angle = -angle
