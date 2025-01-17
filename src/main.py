from __future__ import annotations

import copy
import tkinter as tk
from typing import Optional

from .config import WINDOW_BG, CYCLE, DELAY, PADX, PADY, ICON_FILE
from .core import repository
from .core.components.characters import LetterType
from .core.components.consonants import Consonant, DotConsonant
from .core.components.syllables import Syllable
from .core.components.vowels import Vowel
from .core.components.words import Word
from .core.frames import LettersFrame, CanvasFrame, SpecialCharactersFrame, ToolsFrame
from .core.tools.colorscheme import ColorSchemeWindow, ColorScheme
from .core.tools.export import ProgressWindow, save_image


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.color_scheme = ColorScheme()
        self.animation_enabled = False
        self.animation_task_id: Optional[str] = None

        self._initialize_character_repository()
        self._create_frames()
        self._layout_frames()
        self._configure_window()

        self._color_scheme_window: Optional[tk.Toplevel] = None

    def _configure_window(self):
        """Set up the main application window."""
        icon = tk.PhotoImage(file=ICON_FILE)
        self.iconphoto(False, icon)

        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export as PNG", command=self._save_png)
        file_menu.add_command(label="Export as GIF", command=self._save_gif)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Color Scheme", command=self._open_color_scheme_window)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        self.title('Gallifreyan')
        self.config(menu=menu_bar, bg=WINDOW_BG)
        self.update_idletasks()

        window_width = self.winfo_width()
        window_height = self.winfo_height()
        menu_height = self.winfo_rooty() - self.winfo_y()
        self.geometry(f"{window_width}x{window_height + menu_height}")

    def _open_color_scheme_window(self):
        """Open the color scheme window."""
        if self._color_scheme_window and self._color_scheme_window.winfo_exists():
            self._color_scheme_window.deiconify()
        else:
            self._color_scheme_window = ColorSchemeWindow(self, self.color_scheme, self.apply_color_scheme)

    def apply_color_scheme(self, color_scheme: ColorScheme):
        """Apply the updated color scheme to the application."""
        Word.color = color_scheme.word_color
        Syllable.color = color_scheme.syllable_color
        Consonant.color = color_scheme.syllable_color
        Vowel.color = color_scheme.vowel_color
        DotConsonant.color = color_scheme.dot_color

        self.color_scheme = copy.copy(color_scheme)
        self.canvas_frame.apply_color_changes()

    @staticmethod
    def _initialize_character_repository():
        """Initialize the character repository from configuration files."""
        repository.initialize()

    def _create_frames(self):
        """Create all the frames used in the application."""
        self.canvas_frame = CanvasFrame(self)
        self.consonants_frame = LettersFrame(LetterType.CONSONANT, self, self.canvas_frame.entry)
        self.vowels_frame = LettersFrame(LetterType.VOWEL, self, self.canvas_frame.entry)
        self.special_characters_frame = SpecialCharactersFrame(self, self.canvas_frame.entry)
        self.tools_frame = ToolsFrame(self, self._set_animation_state)

    def _layout_frames(self):
        """Place the frames in the application window using a grid layout."""
        self.consonants_frame.grid(row=0, column=0, columnspan=2, padx=PADX, pady=PADY, sticky='nw')
        self.vowels_frame.grid(row=1, column=0, rowspan=2, padx=PADX, pady=PADY, sticky='nw')
        self.special_characters_frame.grid(row=2, column=1, padx=PADX, pady=PADY, sticky='nw')
        self.canvas_frame.grid(row=0, column=2, rowspan=3, padx=PADX, pady=PADY, sticky='nw')

        self.tools_frame.grid(row=1, column=1, padx=PADX, pady=PADY, sticky='nw')
        self.rowconfigure(2, weight=1)
        self.columnconfigure(1, weight=1)

    def _animation_loop(self):
        self.canvas_frame.perform_animation()
        self.animation_task_id = self.after(DELAY, self._animation_loop)

    def _set_animation_state(self, enabled: bool):
        if enabled:
            if self.animation_task_id is None:
                self.animation_task_id = self.after(DELAY, self._animation_loop)
        else:
            if self.animation_task_id is not None:
                self.after_cancel(self.animation_task_id)
                self.animation_task_id = None
        self.animation_enabled = enabled

    def _save_png(self):
        """Save the current canvas content as a PNG file."""
        animation_enabled = self.animation_enabled
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

        animation_enabled = self.animation_enabled
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
