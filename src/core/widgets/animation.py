import tkinter as tk
from typing import Callable

from ...config import WINDOW_BG
from ...core.tools.common import ToolButton


class AnimationFrame(tk.Frame):
    """A frame that controls animation."""

    def __init__(self, win: tk.Misc, command: Callable[[bool], None]):
        super().__init__(win, bg=WINDOW_BG)

        button = ToolButton(self, 'Animation', command)
        button.grid(row=0, column=0, sticky='news')
