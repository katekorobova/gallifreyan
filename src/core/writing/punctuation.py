import tkinter as tk
from typing import Optional

from PIL import ImageTk
from PIL.Image import Image
from PIL.ImageDraw import ImageDraw

from .characters import Character, CharacterType
from .characters.marks import PunctuationMark
from .common import CanvasItem
from .words import InteractiveToken
from ..utils import Point, PressedType, random_position


class MarkItem(CanvasItem):
    def __init__(self, mark: PunctuationMark):
        super().__init__()
        self.mark = mark
        self.center = random_position()

        self._image_tk = ImageTk.PhotoImage(image=mark.get_image())
        self._canvas_item_id = None
        self._image_ready = False

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]) -> None:
        mark_image = self.mark.get_image()

        if self._image_ready:
            if self._canvas_item_id is None:
                self._image_tk.paste(mark_image)
                self._canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)
            else:
                canvas.tag_raise(self._canvas_item_id)
                to_be_removed.remove(self._canvas_item_id)
        else:
            self._image_tk.paste(mark_image)
            self._canvas_item_id = canvas.create_image(self.center.tuple(), image=self._image_tk)

    def paste_image(self, image: Image, position: Point) -> None:
        mark_image = self.mark.get_image()
        image.paste(mark_image, (self.center - self.mark.IMAGE_CENTER - position).tuple(), mark_image)

    def press(self, point: Point) -> Optional[PressedType]:
        item_point = point - self.center
        mark_pressed_type = self.mark.press(item_point)
        if mark_pressed_type:
            if mark_pressed_type == PressedType.SELF:
                self._position_bias = item_point
                self._pressed_type = PressedType.SELF
            else:
                self._pressed_type = PressedType.CHILD
            return self._pressed_type
        return None

    def move(self, point: Point) -> None:
        item_point = point - self.center
        match self._pressed_type:
            case PressedType.SELF:
                self.center = point - self._position_bias
            case PressedType.CHILD:
                self.mark.move(item_point)
            case _:
                return
        self._image_ready = False

    def redraw(self, image: Image, draw: ImageDraw) -> None:
        raise NotImplementedError()

    def apply_color_changes(self) -> None:
        self.mark.apply_color_changes()


class PunctuationToken(InteractiveToken):
    def __init__(self, characters: list[Character]):
        super().__init__()
        self.marks: list[MarkItem] = []
        self.insert_characters(0, characters)
        self._pressed_mark: Optional[MarkItem] = None

    def press(self, point: Point) -> Optional[PressedType]:
        for mark in reversed(self.marks):
            if mark.press(point):
                self._pressed_mark = mark
                self._pressed_type = PressedType.CHILD
                return self._pressed_type
        return None

    def move(self, point: Point):
        if self._pressed_mark:
            self._pressed_mark.move(point)

    def insert_characters(self, index: int, characters: list[Character]) -> bool:
        if not all(character.character_type == CharacterType.PUNCTUATION_MARK for character in characters):
            return False

        super().insert_characters(index, characters)
        # noinspection PyTypeChecker
        self.marks[index:index] = [MarkItem(character) for character in characters]
        return True

    def remove_characters(self, index: int, end_index: int) -> None:
        """Remove characters from the token."""
        super().remove_characters(index, end_index)
        self.marks[index:end_index] = []
        self._pressed_mark = None

    def remove_starting_with(self, index: int) -> None:
        """Remove characters from the token, updating properties accordingly."""
        super().remove_starting_with(index)
        self.marks[index:] = []
        self._pressed_mark = None

    def put_image(self, canvas: tk.Canvas, to_be_removed: list[int]) -> None:
        for mark in self.marks:
            mark.put_image(canvas, to_be_removed)

    def paste_image(self, image: Image, position: Point) -> None:
        for mark in self.marks:
            mark.paste_image(image, position)

    def redraw(self, image: Image, draw: ImageDraw) -> None:
        raise NotImplementedError()

    def apply_color_changes(self) -> None:
        for mark in self.marks:
            mark.apply_color_changes()

    def perform_animation(self, angle: float) -> None:
        pass