from __future__ import annotations

import copy
import tkinter as tk
from typing import Optional

from .config import WINDOW_BG, CYCLE, DELAY, PADX, PADY
from .core import repository
from .core.tools.colorscheme import ColorSchemeWindow, ColorScheme
from .core.tools.export import ProgressWindow, save_image
from .core.widgets.animation import AnimationFrame
from .core.widgets.canvas import CanvasFrame
from .core.widgets.keyboard import LettersFrame, SpecialCharactersFrame
from .core.writing.characters import LetterType
from .core.writing.consonants import Consonant, DotConsonant
from .core.writing.syllables import Syllable
from .core.writing.vowels import Vowel
from .core.writing.words import Word

# Padding settings for UI layout
padx = (0, PADX)
pady = (0, PADY)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._initialize_character_repository()
        self._configure_window()
        self._create_frames()

        self._animation_enabled = False
        self._animation_task_id: Optional[str] = None

        self._color_scheme = ColorScheme()
        self._color_scheme_window: Optional[tk.Toplevel] = None

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
            self._color_scheme_window = ColorSchemeWindow(self, self._color_scheme, self._apply_color_scheme)

    def _apply_color_scheme(self, color_scheme: ColorScheme):
        """Apply the updated color scheme to the application."""
        self.canvas_frame.canvas.configure(bg=color_scheme.canvas_background)
        Word.background = color_scheme.word_background
        Syllable.background = color_scheme.syllable_background
        Consonant.background = color_scheme.syllable_background
        Vowel.background = color_scheme.syllable_background
        DotConsonant.background = color_scheme.syllable_background

        Word.color = color_scheme.word_color
        Syllable.color = color_scheme.syllable_color
        Consonant.color = color_scheme.syllable_color
        Vowel.color = color_scheme.vowel_color
        DotConsonant.color = color_scheme.dot_color

        self._color_scheme = copy.copy(color_scheme)
        self.canvas_frame.apply_color_changes()

    @staticmethod
    def _initialize_character_repository():
        """Initialize the character repository from configuration files."""
        repository.initialize()

    def _create_frames(self):
        """Create all the frames used in the main window."""
        self.canvas_frame = CanvasFrame(self)
        consonants_frame = LettersFrame(LetterType.CONSONANT, self, self.canvas_frame.entry)
        vowels_frame = LettersFrame(LetterType.VOWEL, self, self.canvas_frame.entry)

        tools_frame = tk.Frame(self)
        tools_frame.configure(bg=WINDOW_BG)
        animation_frame = AnimationFrame(tools_frame, self._set_animation_state)
        special_characters_frame = SpecialCharactersFrame(tools_frame, self.canvas_frame.entry)
        animation_frame.grid(row=0, column=0, pady=pady, sticky='nw')
        special_characters_frame.grid(row=1, column=0, sticky='nw')

        consonants_frame.grid(row=0, column=0, columnspan=2, padx=PADX, pady=PADY, sticky='nw')
        vowels_frame.grid(row=1, column=0, padx=PADX, pady=pady, sticky='nw')
        tools_frame.grid(row=1, column=1, padx=PADX, pady=pady, sticky='nw')
        self.canvas_frame.grid(row=0, column=2, rowspan=2, padx=padx, pady=PADY, sticky='nw')

    def _animation_loop(self):
        """Recursively triggers the animation loop."""
        self.canvas_frame.perform_animation()
        self._animation_task_id = self.after(DELAY, self._animation_loop)

    def _set_animation_state(self, enabled: bool):
        """Starts or stops the animation loop based on the given state."""
        if enabled:
            if self._animation_task_id is None:
                self._animation_task_id = self.after(DELAY, self._animation_loop)
        else:
            if self._animation_task_id is not None:
                self.after_cancel(self._animation_task_id)
                self._animation_task_id = None
        self._animation_enabled = enabled

    def _save_png(self):
        """Save the current canvas content as a PNG file."""
        animation_enabled = self._animation_enabled
        self._set_animation_state(False)

        try:
            save_image(self.canvas_frame.sentence.get_image(),
                       self.canvas_frame.entry.get(), "png",
                       lambda image, filename: image.save(filename))
        finally:
            self._set_animation_state(animation_enabled)

    def _save_gif(self):
        """Save the current canvas content as an animated GIF."""
        progress_window: Optional[tk.Toplevel] = None

        animation_enabled = self._animation_enabled
        self._set_animation_state(False)

        def save_gif(image, filename):
            nonlocal progress_window
            progress_window = ProgressWindow(self)

            images = []
            for i in range(1, CYCLE):
                self.canvas_frame.sentence.perform_animation()
                images.append(self.canvas_frame.sentence.get_image())
                progress_window.configure_progress_label(i)

            image.save(filename, save_all=True, append_images=images, duration=DELAY, loop=0)

        try:
            save_image(self.canvas_frame.sentence.get_image(),
                       self.canvas_frame.entry.get(), "gif", save_gif)
        finally:
            if progress_window:
                progress_window.destroy()

            self._set_animation_state(animation_enabled)


if __name__ == '__main__':
    app = App()
    app.mainloop()
