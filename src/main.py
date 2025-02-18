from __future__ import annotations

import copy
import tkinter as tk
from typing import Optional

from PIL import Image

from .config import WINDOW_BG, PADX, PADY, SCREEN_OFFSET_X, SCREEN_OFFSET_Y
from .core import repository
from .core.tools import AnimationProperties
from .core.tools.colorscheme import (ColorSchemeWindow, ColorScheme, ColorSchemeComponent)
from .core.tools.export import ProgressWindow, save_image
from .core.utils import get_default_color_scheme, Point
from .core.widgets.animation import AnimationWindow
from .core.widgets.canvas import CanvasFrame
from .core.widgets.keyboard import SpecialCharactersWindow, ConsonantsWindow, NumbersWindow, VowelsWindow
from .core.writing.characters.consonants import Consonant, DotConsonant
from .core.writing.characters.digits import Digit
from .core.writing.characters.vowels import Vowel
from .core.writing.numbers import NumberGroup, NumberMark
from .core.writing.syllables import Syllable
from .core.writing.words import Word

# Padding settings for UI layout
padx = (0, PADX)
pady = (0, PADY)


class App(tk.Tk):
    """The main application class"""
    def __init__(self):
        super().__init__()
        repository.initialize()
        self._configure_window()

        self._animation_enabled = False
        self._animation_task_id: Optional[str] = None

        self._color_scheme = get_default_color_scheme()
        self._apply_color_scheme(self._color_scheme)

        self._color_scheme_selector_window: Optional[tk.Toplevel] = None
        self._consonants_window: Optional[ConsonantsWindow] = None
        self._vowels_window: Optional[VowelsWindow] = None
        self._numbers_window: Optional[NumbersWindow] = None
        self._special_characters_window: Optional[SpecialCharactersWindow] = None
        self._animation_window: Optional[AnimationWindow] = None
        self._place_tool_windows()

    def _configure_window(self):
        """Set up the main application window."""
        self.title('Gallifreyan')
        self.iconphoto(True, tk.PhotoImage(file='src/assets/icon.png'))

        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export as PNG", command=self._save_png)
        file_menu.add_command(label="Export as GIF", command=self._save_gif)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Consonants", command=self._open_consonants_window)
        tools_menu.add_command(label="Vowels", command=self._open_vowels_window)
        tools_menu.add_command(label="Numbers", command=self._open_numbers_window)
        tools_menu.add_command(label="Special Characters", command=self._open_special_characters_window)
        tools_menu.add_separator()

        tools_menu.add_command(label="Animation", command=self._open_animation_window)
        tools_menu.add_separator()

        tools_menu.add_command(label="Color Scheme Selector", command=self._open_color_scheme_selector_window)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        self.canvas_frame = CanvasFrame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.config(menu=menu_bar, bg=WINDOW_BG)
        self.state('zoomed')

    def _open_color_scheme_selector_window(self):
        """Open the color scheme window."""
        if self._color_scheme_selector_window and self._color_scheme_selector_window.winfo_exists():
            self._color_scheme_selector_window.focus()
        else:
            self._color_scheme_selector_window = ColorSchemeWindow(
                self, self._color_scheme, self._apply_color_scheme)

    def _open_consonants_window(self):
        if self._consonants_window and self._consonants_window.winfo_exists():
            self._consonants_window.focus()
        else:
            self._consonants_window = ConsonantsWindow(self, self.canvas_frame.entry)

    def _open_vowels_window(self):
        if self._vowels_window and self._vowels_window.winfo_exists():
            self._vowels_window.focus()
        else:
            self._vowels_window = VowelsWindow(self, self.canvas_frame.entry)

    def _open_numbers_window(self):
        if self._numbers_window and self._numbers_window.winfo_exists():
            self._numbers_window.focus()
        else:
            self._numbers_window = NumbersWindow(self, self.canvas_frame.entry)

    def _open_special_characters_window(self):
        if self._special_characters_window and self._special_characters_window.winfo_exists():
            self._special_characters_window.focus()
        else:
            self._special_characters_window = SpecialCharactersWindow(self, self.canvas_frame.entry)

    def _open_animation_window(self):
        if self._animation_window and self._animation_window.winfo_exists():
            self._animation_window.focus()
        else:
            self._animation_window = AnimationWindow(self, self._set_animation_state)

    def _apply_color_scheme(self, color_scheme: ColorScheme):
        """Apply the updated color scheme to the application."""
        canvas_background = color_scheme[ColorSchemeComponent.CANVAS_BG]
        word_background = color_scheme[ColorSchemeComponent.WORD_BG]
        syllable_background = color_scheme[ColorSchemeComponent.SYLLABLE_BG]

        word_color = color_scheme[ColorSchemeComponent.WORD_COLOR]
        syllable_color = color_scheme[ColorSchemeComponent.SYLLABLE_COLOR]
        vowel_color = color_scheme[ColorSchemeComponent.VOWEL_COLOR]
        dot_color = color_scheme[ColorSchemeComponent.DOT_COLOR]

        self.canvas_frame.configure_background(bg=canvas_background)
        Word.background = word_background
        Syllable.background = syllable_background
        Consonant.background = syllable_background
        Vowel.background = syllable_background
        DotConsonant.background = syllable_background
        NumberGroup.background = syllable_background
        Digit.background = syllable_background
        NumberMark.background = syllable_background

        Word.color = word_color
        Syllable.color = syllable_color
        Consonant.color = syllable_color
        NumberGroup.color = syllable_color
        Digit.color = syllable_color
        NumberMark.color = syllable_color

        Vowel.color = vowel_color
        DotConsonant.color = dot_color

        self._color_scheme = copy.copy(color_scheme)
        self.canvas_frame.apply_color_changes()

    def _place_tool_windows(self):
        """Initialize the tool windows."""
        self.update_idletasks()
        start_x, start_y = self.winfo_screenwidth() - SCREEN_OFFSET_X, SCREEN_OFFSET_Y

        position = Point(start_x, start_y)
        self._vowels_window = VowelsWindow(self, self.canvas_frame.entry, position=position)

        position.y = start_y
        self._consonants_window = ConsonantsWindow(self, self.canvas_frame.entry, position=position)

        start_y = position.y
        position.x = start_x
        self._numbers_window = NumbersWindow(self, self.canvas_frame.entry, position=position)

        position.y = start_y
        self._special_characters_window = SpecialCharactersWindow(self, self.canvas_frame.entry, position=position)

        position.y = start_y
        self._animation_window = AnimationWindow(self, self._set_animation_state, position=position)

    def _animation_loop(self):
        """Recursively triggers the animation loop."""
        self.canvas_frame.perform_animation()
        # noinspection PyTypeChecker
        self._animation_task_id = self.after(AnimationProperties.delay, self._animation_loop)

    def _set_animation_state(self, enabled: bool):
        """Starts or stops the animation loop based on the given state."""
        if enabled:
            if self._animation_task_id is None:
                # noinspection PyTypeChecker
                self._animation_task_id = self.after(
                    AnimationProperties.delay, self._animation_loop)
        else:
            if self._animation_task_id is not None:
                self.after_cancel(self._animation_task_id)
                self._animation_task_id = None
        self._animation_enabled = enabled

    def _save_png(self):
        """Save the current canvas content as a PNG file."""
        animation_enabled = self._animation_enabled
        self._set_animation_state(False)

        def save_png(image: Image.Image, filename: str):
            bbox = image.getchannel("A").getbbox()
            cropped_image = image.crop(bbox)
            cropped_image.save(filename)

        try:
            save_image(image=self.canvas_frame.get_image(),
                       name=self.canvas_frame.entry.get(), extension='png', callback=save_png)
        finally:
            self._set_animation_state(animation_enabled)

    def _save_gif(self):
        """Save the current canvas content as an animated GIF."""
        progress_window: Optional[ProgressWindow] = None

        animation_enabled = self._animation_enabled
        self._set_animation_state(False)

        def save_gif(image: Image.Image, filename: str):
            nonlocal progress_window
            progress_window = ProgressWindow(self)

            bbox = image.getchannel("A").getbbox()
            cropped_image = image.crop(bbox)

            images = []
            for i in range(1, AnimationProperties.cycle):
                self.canvas_frame.sentence.perform_animation()
                images.append(self.canvas_frame.get_image().crop(bbox))
                progress_window.configure_progress_label(i)
            self.canvas_frame.sentence.perform_animation()
            cropped_image.save(filename, save_all=True, append_images=images,
                               duration=AnimationProperties.delay, loop=0)

        try:
            save_image(image=self.canvas_frame.get_image(),
                       name=self.canvas_frame.entry.get(), extension='gif', callback=save_gif)
        finally:
            if progress_window:
                progress_window.destroy()

            self._set_animation_state(animation_enabled)


if __name__ == '__main__':
    app = App()
    app.mainloop()
