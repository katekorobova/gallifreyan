import tkinter as tk
from typing import Callable

from ...config import BUTTON_HEIGHT, FONT, BUTTON_WIDTH


class ToolButton(tk.Button):
    """A custom button widget that toggles the state of the tool."""
    def __init__(self, master: tk.Frame, text: str, command: Callable[[bool], None]):
        super().__init__(master, text=text, font=FONT,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH * 3,
                         command=lambda: self._call_command(command))
        self.pressed = False

    def _call_command(self, command: Callable[[bool], None]):
        """Toggles the state of the button and calls the command."""
        if self.pressed:
            self.configure(relief='raised')
            self.pressed = False
        else:
            self.configure(relief='sunken')
            self.pressed = True
        command(self.pressed)
