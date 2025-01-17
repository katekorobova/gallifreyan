import copy
import math
import tkinter as tk
from tkinter import colorchooser
from typing import Callable

from .. import repository
from ..components.consonants import DotConsonant
from ..components.sentences import get_character
from ..components.words import Word
from ..utils import Point
from ...config import (CANVAS_BG, SYLLABLE_INITIAL_SCALE_MIN, ICON_FILE,
                       WORD_COLOR, SYLLABLE_COLOR, VOWEL_COLOR, DOT_COLOR,
                       BUTTON_WIDTH, BUTTON_HEIGHT, PADX, PADY)


class ColorScheme:
    def __init__(self):
        self.word_color: str = WORD_COLOR
        self.syllable_color: str = SYLLABLE_COLOR
        self.vowel_color: str = VOWEL_COLOR
        self.dot_color: str = DOT_COLOR


class ColorSchemeWindow(tk.Toplevel):
    CENTER = Point(180, 180)

    def __init__(self, master: tk.Tk, color_scheme: ColorScheme, command: Callable[[ColorScheme], None]):
        super().__init__(master)
        icon = tk.PhotoImage(file=ICON_FILE)
        self.iconphoto(False, icon)

        self.transient(master)
        self.geometry("+200+200")
        self.title("Color Scheme")
        self.resizable(False, False)
        self.color_scheme = copy.copy(color_scheme)
        self._color_chooser_is_opened = False

        word_color_frame = self._get_word_color_frame()
        syllable_color_frame = self._get_syllable_color_frame()
        vowel_color_frame = self._get_vowel_color_frame()
        dot_color_frame = self._get_dot_color_frame()

        self.canvas = tk.Canvas(self, bg=CANVAS_BG, width=self.CENTER[0] * 2, height=self.CENTER[1] * 2)
        self.apply_button = tk.Button(self, text="Apply", width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT,
                                      command=lambda: command(self.color_scheme))

        padx = (0, PADX)
        pady = (0, PADY)
        word_color_frame.grid(row=0, column=0, padx=PADX, pady=pady)
        syllable_color_frame.grid(row=1, column=0, padx=PADX, pady=pady)
        vowel_color_frame.grid(row=2, column=0, padx=PADX, pady=pady)
        dot_color_frame.grid(row=3, column=0, padx=PADX, pady=pady)

        self.apply_button.grid(row=4, column=0, sticky='s', padx=PADX, pady=pady)
        self.canvas.grid(row=0, column=2, rowspan=5, padx=padx, pady=PADY)
        self.grid_rowconfigure(4, weight=1)

        self._initialize_word()
        self._redraw()

    def _get_word_color_frame(self) -> tk.Frame:
        word_color_frame = tk.Frame(self)
        word_color_label = tk.Label(word_color_frame, text='Words')
        self.word_color_preview = tk.Label(word_color_frame, bg=self.color_scheme.word_color,
                                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        self.word_color_button = tk.Button(word_color_frame, text='Change', command=self._choose_word_color,
                                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        word_color_label.grid(row=0, column=0, columnspan=2)
        self.word_color_preview.grid(row=1, column=0, padx=(0, PADX))
        self.word_color_button.grid(row=1, column=1)
        return word_color_frame

    def _get_syllable_color_frame(self) -> tk.Frame:
        syllable_color_frame = tk.Frame(self)
        syllable_color_label = tk.Label(syllable_color_frame, text='Syllables')
        self.syllable_color_preview = tk.Label(syllable_color_frame, bg=self.color_scheme.syllable_color,
                                               width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        self.syllable_color_button = tk.Button(syllable_color_frame, text='Change', command=self._choose_syllable_color,
                                               width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        syllable_color_label.grid(row=0, column=0, columnspan=2)
        self.syllable_color_preview.grid(row=1, column=0, padx=(0, PADX))
        self.syllable_color_button.grid(row=1, column=1)
        return syllable_color_frame

    def _get_vowel_color_frame(self) -> tk.Frame:
        vowel_color_frame = tk.Frame(self)
        vowel_color_label = tk.Label(vowel_color_frame, text='Vowels')
        self.vowel_color_preview = tk.Label(vowel_color_frame, bg=self.color_scheme.vowel_color,
                                            width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        self.vowel_color_button = tk.Button(vowel_color_frame, text='Change', command=self._choose_vowel_color,
                                            width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        vowel_color_label.grid(row=0, column=0, columnspan=2)
        self.vowel_color_preview.grid(row=1, column=0, padx=(0, PADX))
        self.vowel_color_button.grid(row=1, column=1)
        return vowel_color_frame

    def _get_dot_color_frame(self) -> tk.Frame:
        dot_color_frame = tk.Frame(self)
        dot_color_label = tk.Label(dot_color_frame, text='Dots')
        self.dot_color_preview = tk.Label(dot_color_frame, bg=self.color_scheme.dot_color,
                                            width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        self.dot_color_button = tk.Button(dot_color_frame, text='Change', command=self._choose_dot_color,
                                            width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        dot_color_label.grid(row=0, column=0, columnspan=2)
        self.dot_color_preview.grid(row=1, column=0, padx=(0, PADX))
        self.dot_color_button.grid(row=1, column=1)
        return dot_color_frame

    def _initialize_word(self):
        self.word = Word(self.CENTER, [get_character(char, *repository.get().all[char]) for char in 'wʌz'])
        self.word.syllables[0].set_direction(0)
        self.word.syllables[1].set_direction(math.pi)

        self.dots = []
        self.vowels = []
        self.consonants = []
        for syllable in self.word.syllables:
            syllable.set_scale(SYLLABLE_INITIAL_SCALE_MIN)

            if syllable.vowel:
                syllable.vowel.set_direction(0)
                self.vowels.append(syllable.vowel)

            for consonant in syllable.consonants:
                consonant.set_direction(0)
                if isinstance(consonant, DotConsonant):
                    self.dots.append(consonant)
                else:
                    self.consonants.append(consonant)

        self.word.update_image_properties()

    def _choose_word_color(self):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose word color", color=self.color_scheme.word_color)
        if color:
            self.color_scheme.word_color = color
            self.word_color_preview.config(bg=color)
            self.word.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_syllable_color(self):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose syllable color", color=self.color_scheme.syllable_color)
        if color:
            self.color_scheme.syllable_color = color
            self.syllable_color_preview.config(bg=color)
            for syllable in self.word.syllables:
                syllable.color = color
            for consonant in self.consonants:
                consonant.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_vowel_color(self):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose vowel color", color=self.color_scheme.vowel_color)
        if color:
            self.color_scheme.vowel_color = color
            self.vowel_color_preview.config(bg=color)
            for vowel in self.vowels:
                vowel.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_dot_color(self):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose dot color", color=self.color_scheme.dot_color)
        if color:
            self.color_scheme.dot_color = color
            self.dot_color_preview.config(bg=color)
            for consonant in self.dots:
                consonant.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _redraw(self):
        self.word.put_image(self.canvas)

    def _repaint(self):
        self.word.apply_color_changes()
        self.word.put_image(self.canvas)
