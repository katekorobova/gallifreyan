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

padx = (0, PADX)
pady = (0, PADY)


class ColorScheme:
    def __init__(self):
        self.canvas_bg: str = CANVAS_BG
        self.word_bg: str = WORD_BG
        self.syllable_bg: str = SYLLABLE_BG

        self.word_color: str = WORD_COLOR
        self.syllable_color: str = SYLLABLE_COLOR
        self.vowel_color: str = VOWEL_COLOR
        self.dot_color: str = DOT_COLOR


class ColorSchemeWindow(tk.Toplevel):
    CENTER = Point(180, 180)

    def __init__(self, master: tk.Tk, color_scheme: ColorScheme, command: Callable[[ColorScheme], None]):
        super().__init__(master)
        self.withdraw()
        self.title("Color Scheme")
        self.transient(master)
        self.geometry("+200+200")
        self.resizable(False, False)
        self.color_scheme = copy.copy(color_scheme)

        canvas_frame = self._create_canvas_frame()
        word_frame = self._create_word_frame()
        syllable_frame = self._create_syllable_frame()
        vowel_frame = self._create_vowel_frame()
        dot_frame = self._create_dot_frame()

        self.canvas = tk.Canvas(self, bg=color_scheme.canvas_bg, width=self.CENTER[0] * 2, height=self.CENTER[1] * 2)
        self.apply_button = tk.Button(self, text="Apply", width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT,
                                      command=lambda: command(self.color_scheme))

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
        self._redraw()
        self.deiconify()

    def _create_canvas_frame(self) -> tk.Frame:
        frame = tk.Frame(self)
        label = tk.Label(frame, text='Canvas')

        preview = tk.Label(frame, bg=self.color_scheme.canvas_bg,
                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        button = tk.Button(frame, text='Change', command=lambda: self._choose_canvas_bg(preview),
                                width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        label.grid(row=0, column=0, columnspan=2)
        preview.grid(row=1, column=0, padx=padx)
        button.grid(row=1, column=1)
        return frame

    def _create_word_frame(self) -> tk.Frame:
        frame = tk.Frame(self)
        label = tk.Label(frame, text='Words')

        color_preview = tk.Label(frame, bg=self.color_scheme.word_color,
                                 width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        color_button = tk.Button(frame, text='Change', command=lambda: self._choose_word_color(color_preview),
                                 width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        bg_preview = tk.Label(frame, bg=self.color_scheme.word_bg,
                              width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        bg_button = tk.Button(frame, text='Change', command=lambda: self._choose_word_bg(bg_preview),
                                        width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        label.grid(row=0, column=0, columnspan=2,)
        color_preview.grid(row=1, column=0, padx=padx)
        color_button.grid(row=1, column=1)
        bg_preview.grid(row=2, column=0, padx=padx)
        bg_button.grid(row=2, column=1)
        return frame

    def _create_syllable_frame(self) -> tk.Frame:
        frame = tk.Frame(self)
        color_label = tk.Label(frame, text='Syllables')
        color_preview = tk.Label(frame, bg=self.color_scheme.syllable_color,
                                 width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        color_button = tk.Button(frame, text='Change', command=lambda: self._choose_syllable_color(color_preview),
                                 width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        bg_preview = tk.Label(frame, bg=self.color_scheme.syllable_bg,
                              width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        bg_button = tk.Button(frame, text='Change', command=lambda: self._choose_syllable_bg(bg_preview),
                                               width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        color_label.grid(row=0, column=0, columnspan=2)
        color_preview.grid(row=1, column=0, padx=padx)
        color_button.grid(row=1, column=1)
        bg_preview.grid(row=2, column=0, padx=padx)
        bg_button.grid(row=2, column=1)
        return frame

    def _create_vowel_frame(self) -> tk.Frame:
        frame = tk.Frame(self)
        label = tk.Label(frame, text='Vowels')
        preview = tk.Label(frame, bg=self.color_scheme.vowel_color,
                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        button = tk.Button(frame, text='Change', command=lambda: self._choose_vowel_color(preview),
                                            width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        label.grid(row=0, column=0, columnspan=2)
        preview.grid(row=1, column=0, padx=padx)
        button.grid(row=1, column=1)
        return frame

    def _create_dot_frame(self) -> tk.Frame:
        frame = tk.Frame(self)
        label = tk.Label(frame, text='Dots')
        preview = tk.Label(frame, bg=self.color_scheme.dot_color,
                           width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT, relief='raised')
        button = tk.Button(frame, text='Change', command=lambda: self._choose_dot_color(preview),
                                          width=BUTTON_WIDTH * 2, height=BUTTON_HEIGHT)

        label.grid(row=0, column=0, columnspan=2)
        preview.grid(row=1, column=0, padx=padx)
        button.grid(row=1, column=1)
        return frame

    def _initialize_word(self):
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

    def _choose_canvas_bg(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose canvas background", color=self.color_scheme.canvas_bg)
        if color:
            self.color_scheme.canvas_bg = color
            preview.config(bg=color)
            self.canvas.configure(bg=color)

        self.attributes('-disabled', False)

    def _choose_word_color(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose word color", color=self.color_scheme.word_color)
        if color:
            self.color_scheme.word_color = color
            preview.config(bg=color)

            self.word.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_word_bg(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose word background", color=self.color_scheme.word_bg)
        if color:
            self.color_scheme.word_bg = color
            preview.config(bg=color)

            self.word.background = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_syllable_color(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose syllable color", color=self.color_scheme.syllable_color)
        if color:
            self.color_scheme.syllable_color = color
            preview.config(bg=color)

            for syllable in self.word.syllables:
                syllable.color = color
            for consonant in self.consonants:
                consonant.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_syllable_bg(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose syllable background", color=self.color_scheme.syllable_bg)
        if color:
            self.color_scheme.syllable_bg = color
            preview.config(bg=color)

            for syllable in self.word.syllables:
                syllable.background = color
            for consonant in self.consonants:
                consonant.background = color
            for vowel in self.vowels:
                vowel.background = color
            for consonant in self.dots:
                consonant.background = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_vowel_color(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose vowel color", color=self.color_scheme.vowel_color)
        if color:
            self.color_scheme.vowel_color = color
            preview.config(bg=color)

            for vowel in self.vowels:
                vowel.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _choose_dot_color(self, preview: tk.Label):
        self.attributes('-disabled', True)

        _, color = colorchooser.askcolor(title="Choose dot color", color=self.color_scheme.dot_color)
        if color:
            self.color_scheme.dot_color = color
            preview.config(bg=color)

            for consonant in self.dots:
                consonant.color = color
            self._repaint()

        self.attributes('-disabled', False)

    def _redraw(self):
        self.word.put_image(self.canvas)

    def _repaint(self):
        self.word.apply_color_changes()
        self.word.put_image(self.canvas)
