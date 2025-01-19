import tkinter as tk
from typing import Callable

from . import DefaultFrame, ToolButton
from ..tools import AnimationProperties
from ...config import (CYCLE_MIN, CYCLE_MAX, CYCLE_STEP, DELAY_MIN, DELAY_MAX, DELAY_STEP,
                       ITEM_BG, PRESSED_BG, TEXT_COLOR, PADX, PADY, SECONDARY_FONT)

padx = (0, PADX)
pady = (0, PADY)


class AnimationFrame(DefaultFrame):
    """A frame that controls animation."""

    def __init__(self, win: tk.Misc, command: Callable[[bool], None]):
        super().__init__(win)

        button = ToolButton(self, 'Animation', command)
        cycle_bar = self._create_bar('Number of Frames', 'cycle', CYCLE_MIN, CYCLE_MAX, CYCLE_STEP)
        delay_bar = self._create_bar('Delay Time in ms', 'delay', DELAY_MIN, DELAY_MAX, DELAY_STEP)

        button.grid(row=0, column=0, padx=PADX, pady=PADY)
        cycle_bar.grid(row=1, column=0, sticky=tk.NSEW, padx=PADX, pady=pady)
        delay_bar.grid(row=2, column=0, sticky=tk.NSEW, padx=PADX, pady=pady)

    def _create_bar(self, label: str, attribute: str, from_: int, to: int, resolution: int) -> tk.Scale:
        bar = tk.Scale(self, label=label, font=SECONDARY_FONT, from_=from_, to=to, resolution=resolution,
                       bg=ITEM_BG, fg=TEXT_COLOR, activebackground=PRESSED_BG, troughcolor=PRESSED_BG,
                       orient=tk.HORIZONTAL, bd=2, relief=tk.SUNKEN, highlightthickness=0,
                       command=lambda value: self._change_value(value, attribute))
        bar.set(getattr(AnimationProperties, attribute))
        return bar

    @staticmethod
    def _change_value(value: str, attribute: str):
        setattr(AnimationProperties, attribute, int(value))
