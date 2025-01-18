import tkinter as tk
from typing import Callable

from src.config import WINDOW_BG
from src.core.tools.common import ToolButton


class AnimationFrame(tk.Frame):
    def __init__(self, win: tk.Tk, command: Callable[[bool], None]):
        super().__init__(win, bg=WINDOW_BG)

        button = ToolButton(self, 'Animation', command)
        button.grid(row=0, column=0, sticky='nw')
