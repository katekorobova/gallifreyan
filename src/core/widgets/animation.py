import tkinter as tk
from typing import Callable

from . import ToolButton, DefaultWindow
from ..tools import AnimationProperties
from ...config import (CYCLE_MIN, CYCLE_MAX, CYCLE_STEP, DELAY_MIN, DELAY_MAX, DELAY_STEP,
                       ITEM_BG, PRESSED_BG, TEXT_COLOR, PADX, PADY, SECONDARY_FONT)

padx = (0, PADX)
pady = (0, PADY)


class AnimationWindow(DefaultWindow):
    """A frame that controls animation."""

    def __init__(self, win: tk.Tk, command: Callable[[bool], None]):
        super().__init__(win, 'Animation')
        self.protocol('WM_DELETE_WINDOW', lambda: self._destroy(command))

        button = ToolButton(self, 'Animation', command)
        cycle_scale = self._create_scale('cycle')
        delay_scale = self._create_scale('delay')

        button.grid(row=0, column=0, padx=PADX, pady=PADY)
        cycle_scale.grid(row=1, column=0, sticky=tk.NSEW, padx=PADX, pady=pady)
        delay_scale.grid(row=2, column=0, sticky=tk.NSEW, padx=PADX, pady=pady)

    def _create_scale(self, attribute: str) -> tk.Scale:
        match attribute:
            case 'cycle':
                label = 'Number of Frames'
                from_ = CYCLE_MIN
                to = CYCLE_MAX
                resolution = CYCLE_STEP
            case 'delay':
                label = 'Delay Time in ms'
                from_ = DELAY_MIN
                to = DELAY_MAX
                resolution = DELAY_STEP
            case _:
                raise ValueError(f"Unable to create a scale for attribute: '{attribute}'")

        scale = tk.Scale(self, label=label, font=SECONDARY_FONT,
                         from_=from_, to=to, resolution=resolution,
                         bg=ITEM_BG, fg=TEXT_COLOR,
                         activebackground=PRESSED_BG, troughcolor=PRESSED_BG,
                         orient=tk.HORIZONTAL, bd=2, relief=tk.SUNKEN, highlightthickness=0,
                         command=lambda value: self._change_value(value, attribute))
        scale.set(getattr(AnimationProperties, attribute))
        return scale

    def _destroy(self, command: Callable[[bool], None]):
        command(False)
        self.destroy()


    @staticmethod
    def _change_value(value: str, attribute: str):
        setattr(AnimationProperties, attribute, int(value))
