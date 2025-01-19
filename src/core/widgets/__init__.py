import tkinter as tk
from typing import Callable

from ...config import (FRAME_BG, ITEM_BG, PRESSED_BG, CANVAS_BG,
                       CANVAS_WIDTH, CANVAS_HEIGHT, BUTTON_HEIGHT,
                       TEXT_COLOR, LABEL_TEXT_COLOR, FONT)


class DefaultFrame(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg=FRAME_BG, bd=1, relief=tk.RAISED)


class DefaultLabel(tk.Label):
    def __init__(self, master: tk.Misc, text: str):
        super().__init__(master, bg=FRAME_BG, fg=LABEL_TEXT_COLOR, font=FONT, text=text)


class DefaultCanvas(tk.Canvas):
    def __init__(self, master: tk.Misc, bg: str = CANVAS_BG,
                 width: float = CANVAS_WIDTH, height: float = CANVAS_HEIGHT):
        super().__init__(master, bg=bg, bd=2, relief=tk.RAISED, highlightthickness=0,
                         width=width, height=height)


class ToolButton(tk.Label):
    OFF = ': Off'
    ON = ': On'

    """A custom button widget that toggles the state of the tool."""

    def __init__(self, master: tk.Frame, label: str, command: Callable[[bool], None]):
        text = label + self.OFF
        super().__init__(master, text=text, font=FONT, relief=tk.RAISED, fg=TEXT_COLOR, bg=ITEM_BG,
                         activeforeground=LABEL_TEXT_COLOR, activebackground=PRESSED_BG,
                         height=BUTTON_HEIGHT, width=len(text))
        self.text = label
        self.pressed = False

        self.bind("<ButtonPress-1>", lambda event: self._call_command(command))

    def _call_command(self, command: Callable[[bool], None]):
        """Toggles the state of the button and calls the command."""
        if self.pressed:
            self.configure(state=tk.NORMAL, relief=tk.RAISED, text=self.text + self.OFF)
        else:
            self.configure(state=tk.ACTIVE, relief=tk.SUNKEN, text=self.text + self.ON)

        self.pressed = not self.pressed
        command(self.pressed)
