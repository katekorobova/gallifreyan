import copy
import math
import tkinter as tk
from tkinter import colorchooser
from typing import Callable

from .. import repository
from ..utils import Point
from ..writing.consonants import DotConsonant
from ..writing.sentences import get_character
from ..writing.words import Word
from ...config import (SYLLABLE_INITIAL_SCALE_MIN, CANVAS_BG, WORD_BG, SYLLABLE_BG,
                       WORD_COLOR, SYLLABLE_COLOR, VOWEL_COLOR, DOT_COLOR,
                       BUTTON_WIDTH, BUTTON_HEIGHT, PADX, PADY)

# Padding settings for UI layout
padx = (0, PADX)
pady = (0, PADY)


class ColorScheme:
    """
    Represents the color scheme used for the canvas.
    Stores background and foreground colors for various elements.
    """

    def __init__(self):
        self.canvas_background: str = CANVAS_BG
        self.word_background: str = WORD_BG
        self.syllable_background: str = SYLLABLE_BG

        self.word_color: str = WORD_COLOR
        self.syllable_color: str = SYLLABLE_COLOR
        self.vowel_color: str = VOWEL_COLOR
        self.dot_color: str = DOT_COLOR


class ColorSchemeWindow(tk.Toplevel):
    """
    A GUI window for modifying the canvas's color scheme.
    Provides options to change colors for canvas, words, syllables, vowels, and dots.
    """
    CENTER = Point(180, 180)

    def __init__(self, master: tk.Tk, color_scheme: ColorScheme, command: Callable[[ColorScheme], None]):
        """
        Initializes the color scheme window.
        :param master: The parent Tkinter window.
        :param color_scheme: The current color scheme.
        :param command: Callback function to apply the updated color scheme.
        """
        super().__init__(master)
        self.withdraw()
        self.title("Color Scheme")
        self.transient(master)
        self.geometry("+200+200")
        self.resizable(False, False)
        self.color_scheme = copy.copy(color_scheme)

        # Create UI frames for color selection
        canvas_frame = self._create_unary_frame('Canvas',
                                                self.color_scheme.canvas_background, self._choose_canvas_background)
        word_frame = self._create_binary_frame('Words', self.color_scheme.word_color, self._choose_word_color,
                                               self.color_scheme.word_background, self._choose_word_background)
        syllable_frame = self._create_binary_frame('Syllables',
                                                   self.color_scheme.syllable_color, self._choose_syllable_color,
                                                   self.color_scheme.syllable_background,
                                                   self._choose_syllable_background)
        vowel_frame = self._create_unary_frame('Vowels', self.color_scheme.vowel_color, self._choose_vowel_color)
        dot_frame = self._create_unary_frame('Dots', self.color_scheme.dot_color, self._choose_dot_color)

        # Tiny canvas for previewing the changes
        self.canvas = tk.Canvas(self, bg=color_scheme.canvas_background,
                                width=self.CENTER[0] * 2, height=self.CENTER[1] * 2)

        # Apply button to save changes
        self.apply_button = tk.Button(self, text="Apply", width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT,
                                      command=lambda: command(self.color_scheme))

        # Grid layout positioning
        canvas_frame.grid(row=0, column=0, padx=PADX, pady=pady)
        word_frame.grid(row=1, column=0, padx=PADX, pady=pady)
        syllable_frame.grid(row=2, column=0, padx=PADX, pady=pady)
        vowel_frame.grid(row=3, column=0, padx=PADX, pady=pady)
        dot_frame.grid(row=4, column=0, padx=PADX, pady=pady)

        self.apply_button.grid(row=5, column=0, sticky='s', padx=PADX, pady=pady)
        self.canvas.grid(row=0, column=2, rowspan=6, padx=padx, pady=PADY)
        self.grid_rowconfigure('all', weight=1)
        self.grid_columnconfigure('all', weight=1)

        self._initialize_word()
        self._draw()
        self.deiconify()

    def _create_unary_frame(self, title: str, color: str, command: Callable[[tk.Label], None]) -> tk.Frame:
        """Creates a frame containing a label, a color preview, and a button to change the color."""
        frame = tk.Frame(self)
        label = tk.Label(frame, text=title)

        preview = tk.Label(frame, bg=color, relief='raised',
                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)
        button = tk.Button(frame, text='Change',
                           command=lambda: command(preview),
                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        label.grid(row=0, column=0, columnspan=2)
        preview.grid(row=1, column=0, padx=padx)
        button.grid(row=1, column=1)
        return frame

    def _create_binary_frame(self, title: str, color: str, color_command: Callable[[tk.Label], None],
                             background: str, background_command: Callable[[tk.Label], None]) -> tk.Frame:
        """Creates a frame containing a label, two color preview labels, and buttons to change each color."""
        frame = tk.Frame(self)
        label = tk.Label(frame, text=title)

        color_preview = tk.Label(frame, bg=color, relief='raised',
                                 width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)
        color_button = tk.Button(frame, text='Change',
                                 command=lambda: color_command(color_preview),
                                 width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        background_preview = tk.Label(frame, bg=background, relief='raised',
                                      width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)
        background_button = tk.Button(frame, text='Change',
                                      command=lambda: background_command(background_preview),
                                      width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        label.grid(row=0, column=0, columnspan=2, )
        color_preview.grid(row=1, column=0, padx=padx)
        color_button.grid(row=1, column=1)
        background_preview.grid(row=2, column=0, padx=padx)
        background_button.grid(row=2, column=1)
        return frame

    def _initialize_word(self):
        """Initializes the word preview."""
        self.word = Word(self.CENTER, [get_character(char, *repository.get().all[char]) for char in 'wʌz'])
        self.word.syllables[0].set_direction(0)
        self.word.syllables[1].set_direction(math.pi)

        self.dots = []
        self.vowels = []
        self.consonants = []
        for syllable in self.word.syllables:
            syllable.set_scale(SYLLABLE_INITIAL_SCALE_MIN)
            syllable.set_inner_scale(0.5)

            if syllable.vowel:
                syllable.vowel.set_direction(0)
                self.vowels.append(syllable.vowel)

            for consonant in syllable.consonants:
                consonant.set_direction(0)
                if isinstance(consonant, DotConsonant):
                    self.dots.append(consonant)
                else:
                    self.consonants.append(consonant)

        self.word.update_properties_after_resizing()

    def _choose_canvas_background(self, preview: tk.Label):
        """Opens a color picker to change the canvas background color."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Canvas Background", color=self.color_scheme.canvas_background)
        if color:
            self.color_scheme.canvas_background = color
            preview.config(bg=color)
            self.canvas.configure(bg=color)

        self.attributes('-disabled', False)

    def _choose_word_color(self, preview: tk.Label):
        """Opens a color picker to change the word color."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Word Color", color=self.color_scheme.word_color)
        if color:
            self.color_scheme.word_color = color
            preview.config(bg=color)

            self.word.color = color
            self._redraw()

        self.attributes('-disabled', False)

    def _choose_word_background(self, preview: tk.Label):
        """Opens a color picker to change the word background."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Word Background", color=self.color_scheme.word_background)
        if color:
            self.color_scheme.word_background = color
            preview.config(bg=color)

            self.word.background = color
            self._redraw()

        self.attributes('-disabled', False)

    def _choose_syllable_color(self, preview: tk.Label):
        """Opens a color picker to change the syllable color."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Syllable Color", color=self.color_scheme.syllable_color)
        if color:
            self.color_scheme.syllable_color = color
            preview.config(bg=color)

            for syllable in self.word.syllables:
                syllable.color = color
            for consonant in self.consonants:
                consonant.color = color
            self._redraw()

        self.attributes('-disabled', False)

    def _choose_syllable_background(self, preview: tk.Label):
        """Opens a color picker to change the syllable background."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Syllable Background",
                                         color=self.color_scheme.syllable_background)
        if color:
            self.color_scheme.syllable_background = color
            preview.config(bg=color)

            for syllable in self.word.syllables:
                syllable.background = color
            for consonant in self.consonants:
                consonant.background = color
            for vowel in self.vowels:
                vowel.background = color
            for consonant in self.dots:
                consonant.background = color
            self._redraw()

        self.attributes('-disabled', False)

    def _choose_vowel_color(self, preview: tk.Label):
        """Opens a color picker to change the vowel color."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Vowel Color", color=self.color_scheme.vowel_color)
        if color:
            self.color_scheme.vowel_color = color
            preview.config(bg=color)

            for vowel in self.vowels:
                vowel.color = color
            self._redraw()

        self.attributes('-disabled', False)

    def _choose_dot_color(self, preview: tk.Label):
        """Opens a color picker to change the dot color."""
        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title="Choose Dot Color", color=self.color_scheme.dot_color)
        if color:
            self.color_scheme.dot_color = color
            preview.config(bg=color)

            for consonant in self.dots:
                consonant.color = color
            self._redraw()

        self.attributes('-disabled', False)

    def _draw(self):
        """Draws the word preview on the canvas."""
        self.word.put_image(self.canvas)

    def _redraw(self):
        """Applies the selected color changes and updates the preview."""
        self.word.apply_color_changes()
        self._draw()
