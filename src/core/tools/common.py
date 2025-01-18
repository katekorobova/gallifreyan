import tkinter as tk
from typing import Callable

from src.config import BUTTON_HEIGHT, FONT, BUTTON_WIDTH


class ToolButton(tk.Button):
    def __init__(self, master: tk.Frame, text: str, command: Callable[[bool], None]):
        super().__init__(master, text=text, font=FONT,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH * 3,
                         command=lambda: self._call_command(command))
        self.pressed = False

    def _call_command(self, command: Callable[[bool], None]):
        if self.pressed:
            self.configure(relief='raised')
            self.pressed = False
        else:
            self.configure(relief='sunken')
            self.pressed = True
        command(self.pressed)