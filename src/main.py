from __future__ import annotations

import copy
import tkinter as tk
from typing import Optional

from PIL import Image

from .core.writing.characters import CharacterType
from .config import WINDOW_BG, PADX, PADY
from .core import repository
from .core.tools import AnimationProperties
from .core.tools.colorscheme import (ColorSchemeWindow, ColorScheme, ColorSchemeComponent,
                                     get_default_color_scheme)
from .core.tools.export import ProgressWindow, save_image
from .core.widgets.animation import AnimationFrame
from .core.widgets.canvas import CanvasFrame
from .core.widgets.keyboard import CharactersFrame, SpecialCharactersFrame
from .core.writing.consonants import Consonant, DotConsonant
from .core.writing.syllables import Syllable
from .core.writing.vowels import Vowel
from .core.writing.words import Word

# Padding settings for UI layout
padx = (0, PADX)
pady = (0, PADY)


class App(tk.Tk):
    """The main application class"""
    def __init__(self):
        super().__init__()
        self._initialize_character_repository()
        self._configure_window()
        self._create_frames()

        self._animation_enabled = False
        self._animation_task_id: Optional[str] = None

        self._color_scheme = get_default_color_scheme()
        self._color_scheme_window: Optional[tk.Toplevel] = None
        self._apply_color_scheme(self._color_scheme)

    def _configure_window(self):
        """Set up the main application window."""
        self.title('Gallifreyan')
        self.iconphoto(True, tk.PhotoImage(file='src/assets/icon.png'))

        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export as PNG", command=self._save_png)
        file_menu.add_command(label="Export as GIF", command=self._save_gif)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Color Scheme", command=self._open_color_scheme_window)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.config(menu=menu_bar, bg=WINDOW_BG)

    def _open_color_scheme_window(self):
        """Open the color scheme window."""
        if self._color_scheme_window and self._color_scheme_window.winfo_exists():
            self._color_scheme_window.focus()
        else:
            self._color_scheme_window = ColorSchemeWindow(
                self, self._color_scheme, self._apply_color_scheme)

    def _apply_color_scheme(self, color_scheme: ColorScheme):
        """Apply the updated color scheme to the application."""
        canvas_background = color_scheme[ColorSchemeComponent.CANVAS_BG]
        word_background = color_scheme[ColorSchemeComponent.WORD_BG]
        syllable_background = color_scheme[ColorSchemeComponent.SYLLABLE_BG]

        word_color = color_scheme[ColorSchemeComponent.WORD_COLOR]
        syllable_color = color_scheme[ColorSchemeComponent.SYLLABLE_COLOR]
        vowel_color = color_scheme[ColorSchemeComponent.VOWEL_COLOR]
        dot_color = color_scheme[ColorSchemeComponent.DOT_COLOR]

        self.canvas_frame.canvas.configure(bg=canvas_background)
        Word.background = word_background
        Syllable.background = syllable_background
        Consonant.background = syllable_background
        Vowel.background = syllable_background
        DotConsonant.background = syllable_background

        Word.color = word_color
        Syllable.color = syllable_color
        Consonant.color = syllable_color
        Vowel.color = vowel_color
        DotConsonant.color = dot_color

        self._color_scheme = copy.copy(color_scheme)
        self.canvas_frame.apply_color_changes()

    @staticmethod
    def _initialize_character_repository():
        """Initialize the character repository from configuration files."""
        repository.initialize()

    def _create_frames(self):
        """Create all the frames used in the main window."""
        self.canvas_frame = CanvasFrame(self)
        consonants_frame = CharactersFrame(CharacterType.CONSONANT, self, self.canvas_frame.entry)
        vowels_frame = CharactersFrame(CharacterType.VOWEL, self, self.canvas_frame.entry)

        tools_frame = tk.Frame(self)
        tools_frame.configure(bg=WINDOW_BG)
        special_characters_frame = SpecialCharactersFrame(tools_frame, self.canvas_frame.entry)
        animation_frame = AnimationFrame(tools_frame, self._set_animation_state)
        special_characters_frame.grid(row=0, column=0, pady=pady, sticky=tk.NW)
        animation_frame.grid(row=1, column=0, sticky=tk.NW)

        consonants_frame.grid(row=0, column=0, columnspan=2, padx=PADX, pady=PADY, sticky=tk.NW)
        vowels_frame.grid(row=1, column=0, padx=PADX, pady=pady, sticky=tk.NW)
        tools_frame.grid(row=1, column=1, padx=PADX, pady=pady, sticky=tk.NW)
        self.canvas_frame.grid(row=0, column=2, rowspan=2, padx=padx, pady=PADY, sticky=tk.NW)

    def _animation_loop(self):
        """Recursively triggers the animation loop."""
        self.canvas_frame.perform_animation()
        self._animation_task_id = self.after(AnimationProperties.delay, self._animation_loop)

    def _set_animation_state(self, enabled: bool):
        """Starts or stops the animation loop based on the given state."""
        if enabled:
            if self._animation_task_id is None:
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
            save_image(image=self.canvas_frame.sentence.get_image(),
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
                images.append(self.canvas_frame.sentence.get_image().crop(bbox))
                progress_window.configure_progress_label(i)

            cropped_image.save(filename, save_all=True, append_images=images,
                               duration=AnimationProperties.delay, loop=0)

        try:
            save_image(image=self.canvas_frame.sentence.get_image(),
                       name=self.canvas_frame.entry.get(), extension='gif', callback=save_gif)
        finally:
            if progress_window:
                progress_window.destroy()

            self._set_animation_state(animation_enabled)


if __name__ == '__main__':
    app = App()
    app.mainloop()
