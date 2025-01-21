from __future__ import annotations
import copy
import math
import tkinter as tk
from enum import Enum, auto
from tkinter import colorchooser
from typing import Callable

from .. import repository
from ..utils import Point
from ..widgets import DefaultCanvas, SecondaryLabel, DefaultFrame
from ..writing.consonants import DotConsonant
from ..writing.sentences import get_character
from ..writing.words import Word
from ...config import (WINDOW_BG, CANVAS_BG, WORD_BG, SYLLABLE_BG, ITEM_BG,
                       TEXT_COLOR, WORD_COLOR, SYLLABLE_COLOR, VOWEL_COLOR, DOT_COLOR,
                       SECONDARY_FONT, BUTTON_HEIGHT, PADX, PADY, SYLLABLE_INITIAL_SCALE_MAX)

# Padding settings for UI layout
padx = (0, PADX)
pady = (0, PADY)


class ColorSchemeComponent(Enum):
    CANVAS_BG = auto()
    WORD_BG = auto()
    SYLLABLE_BG = auto()

    WORD_COLOR = auto()
    SYLLABLE_COLOR = auto()
    VOWEL_COLOR = auto()
    DOT_COLOR = auto()


ColorScheme = dict[ColorSchemeComponent, str]

_default_color_scheme: ColorScheme = {
        ColorSchemeComponent.CANVAS_BG: CANVAS_BG,
        ColorSchemeComponent.WORD_BG: WORD_BG,
        ColorSchemeComponent.SYLLABLE_BG: SYLLABLE_BG,
        ColorSchemeComponent.WORD_COLOR: WORD_COLOR,
        ColorSchemeComponent.SYLLABLE_COLOR: SYLLABLE_COLOR,
        ColorSchemeComponent.VOWEL_COLOR: VOWEL_COLOR,
        ColorSchemeComponent.DOT_COLOR: DOT_COLOR
    }


def get_default_color_scheme():
    return copy.copy(_default_color_scheme)


def reset_color_scheme(color_scheme: ColorScheme):
    for key, value in _default_color_scheme.items():
        color_scheme[key] = value


class ColorSchemeSection(Enum):
    CANVAS = auto()
    WORDS = auto()
    SYLLABLES = auto()
    VOWELS = auto()
    DOTS = auto()


class ColorSchemeWindow(tk.Toplevel):
    """
    A GUI window for modifying the canvas's color scheme.
    Provides options to change colors for canvas, words, syllables, vowels, and dots.
    """
    CENTER = Point(250, 250)
    BUTTON_WIDTH = 8

    def __init__(self, master: tk.Tk, color_scheme: ColorScheme, command: Callable[[ColorScheme], None]):
        """Initializes the color scheme window."""
        super().__init__(master, bg=WINDOW_BG)
        self.title("Color Scheme")
        self.transient(master)
        self.geometry("+200+200")
        self.resizable(False, False)
        self.color_scheme = copy.copy(color_scheme)
        self.previews: dict[ColorSchemeComponent, tk.Label] = {}

        # Create UI frames for color selection
        canvas_color_frame = self._create_unary_frame(ColorSchemeSection.CANVAS)
        word_color_frame = self._create_binary_frame(ColorSchemeSection.WORDS)
        syllable_color_frame = self._create_binary_frame(ColorSchemeSection.SYLLABLES)
        vowel_color_frame = self._create_unary_frame(ColorSchemeSection.VOWELS)
        dot_color_frame = self._create_unary_frame(ColorSchemeSection.DOTS)

        button_frame = DefaultFrame(self)
        reset_button = self._create_button(button_frame, text='Reset', command=self._reset_scheme)
        apply_button = self._create_button(button_frame, text='Apply', command=lambda: command(self.color_scheme))
        reset_button.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=tk.NSEW)
        apply_button.grid(row=0, column=1, padx=padx, pady=PADY, sticky=tk.NSEW)

        # Tiny canvas for previewing the changes
        canvas_frame = DefaultFrame(self)
        self.canvas = DefaultCanvas(canvas_frame, bg=color_scheme[ColorSchemeComponent.CANVAS_BG],
                                    width=self.CENTER[0] * 2, height=self.CENTER[1] * 2)
        self.canvas.pack(padx=PADX, pady=PADY)

        # Grid layout positioning
        canvas_color_frame.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=tk.NSEW)
        word_color_frame.grid(row=1, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        syllable_color_frame.grid(row=2, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        vowel_color_frame.grid(row=3, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        dot_color_frame.grid(row=4, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        button_frame.grid(row=5, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        canvas_frame.grid(row=0, column=1, rowspan=6, padx=padx, pady=PADY, sticky=tk.NSEW)

        for i in range(len(ColorSchemeSection)):
            self.rowconfigure(i, weight=1)

        self._initialize_word()
        self._draw()

    def _create_unary_frame(self, section: ColorSchemeSection) -> tk.Frame:
        """Creates a frame containing a label, a color preview, and a button to change the color."""
        match section:
            case ColorSchemeSection.CANVAS:
                title = 'Canvas'
                component = ColorSchemeComponent.CANVAS_BG
            case ColorSchemeSection.VOWELS:
                title = 'Vowels'
                component = ColorSchemeComponent.VOWEL_COLOR
            case ColorSchemeSection.DOTS:
                title = 'Dots'
                component = ColorSchemeComponent.DOT_COLOR
            case _:
                raise ValueError(f"Unable to create a frame for section: '{section}'")

        frame = DefaultFrame(self)
        label = SecondaryLabel(frame, text=title)
        preview = self._create_preview(frame, self.color_scheme[component])
        button = self._create_button(frame, text='Change', command=lambda: self._choose_color(component))

        label.grid(row=0, column=0, columnspan=2, padx=PADX, sticky=tk.W)
        preview.grid(row=1, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        button.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.NSEW)
        frame.columnconfigure(tk.ALL, weight=1)

        self.previews[component] = preview
        return frame

    def _create_binary_frame(self, section: ColorSchemeSection) -> tk.Frame:
        """Creates a frame containing a label, two color preview labels, and buttons to change each color."""

        match section:
            case ColorSchemeSection.WORDS:
                title = 'Words'
                color_component = ColorSchemeComponent.WORD_COLOR
                background_component = ColorSchemeComponent.WORD_BG
            case ColorSchemeSection.SYLLABLES:
                title = 'Syllables'
                color_component = ColorSchemeComponent.SYLLABLE_COLOR
                background_component = ColorSchemeComponent.SYLLABLE_BG
            case _:
                raise ValueError(f"Unable to create a frame for section: '{section}'")

        frame = DefaultFrame(self)
        label = SecondaryLabel(frame, text=title)
        color_preview = self._create_preview(frame, self.color_scheme[color_component])
        color_button = self._create_button(frame, text='Change', command=lambda: self._choose_color(color_component))
        background_preview = self._create_preview(frame, self.color_scheme[background_component])
        background_button = self._create_button(frame, text='Change',
                                                command=lambda: self._choose_color(background_component))

        label.grid(row=0, column=0, columnspan=2, padx=PADX, sticky=tk.W)
        color_preview.grid(row=1, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        color_button.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.NSEW)
        background_preview.grid(row=2, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)
        background_button.grid(row=2, column=1, padx=padx, pady=pady, sticky=tk.NSEW)
        frame.columnconfigure(tk.ALL, weight=1)

        self.previews[color_component] = color_preview
        self.previews[background_component] = background_preview
        return frame

    def _create_preview(self, master: tk.Misc, color: str):
        return tk.Label(master, bg=color, font=SECONDARY_FONT, relief=tk.RAISED,
                        width=self.BUTTON_WIDTH, height=BUTTON_HEIGHT)

    def _create_button(self, master: tk.Misc, text: str, command: Callable[[], None]):
        return tk.Button(master, text=text, command=command,
                         bg=ITEM_BG, fg=TEXT_COLOR, font=SECONDARY_FONT,
                         width=self.BUTTON_WIDTH, height=BUTTON_HEIGHT)

    def _initialize_word(self):
        """Initializes the word preview."""
        self.word = Word(self.CENTER, [get_character(char, *repository.get().all[char]) for char in 'wʌz'])
        self.word.syllables[0].set_direction(0)
        self.word.syllables[1].set_direction(math.pi)

        self.dots = []
        self.vowels = []
        self.consonants = []
        for syllable in self.word.syllables:
            syllable.set_scale(SYLLABLE_INITIAL_SCALE_MAX)
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

    def _choose_color(self, component: ColorSchemeComponent):
        """Opens a color picker to change the color."""
        match component:
            case ColorSchemeComponent.CANVAS_BG:
                name = 'Canvas Background'
                command = self._set_canvas_background
            case ColorSchemeComponent.WORD_BG:
                name = 'Word Background'
                command = self._set_word_background
            case ColorSchemeComponent.SYLLABLE_BG:
                name = 'Syllable Background'
                command = self._set_syllable_background
            case ColorSchemeComponent.WORD_COLOR:
                name = 'Word Color'
                command = self._set_word_color
            case ColorSchemeComponent.SYLLABLE_COLOR:
                name = 'Syllable Color'
                command = self._set_syllable_color
            case ColorSchemeComponent.VOWEL_COLOR:
                name = 'Vowel Color'
                command = self._set_vowel_color
            case ColorSchemeComponent.DOT_COLOR:
                name = 'Dot Color'
                command = self._set_dot_color
            case _:
                raise ValueError(f"Unable to create a frame for a component: '{component}'")

        self.attributes('-disabled', True)
        _, color = colorchooser.askcolor(title=f'Choose {name}', color=self.color_scheme[component])
        if color:
            command(color)
            if color != ColorSchemeComponent.CANVAS_BG:
                self._redraw()
        self.attributes('-disabled', False)

    def _set_canvas_background(self, color: str):
        self.color_scheme[ColorSchemeComponent.CANVAS_BG] = color
        self.previews[ColorSchemeComponent.CANVAS_BG].config(bg=color)
        self.canvas.configure(bg=color)

    def _set_word_background(self, color: str):
        self.color_scheme[ColorSchemeComponent.WORD_BG] = color
        self.previews[ColorSchemeComponent.WORD_BG].config(bg=color)
        self.word.background = color

    def _set_syllable_background(self, color: str):
        self.color_scheme[ColorSchemeComponent.SYLLABLE_BG] = color
        self.previews[ColorSchemeComponent.SYLLABLE_BG].config(bg=color)

        for syllable in self.word.syllables:
            syllable.background = color
        for consonant in self.consonants:
            consonant.background = color
        for vowel in self.vowels:
            vowel.background = color
        for consonant in self.dots:
            consonant.background = color

    def _set_word_color(self, color: str):
        self.color_scheme[ColorSchemeComponent.WORD_COLOR] = color
        self.previews[ColorSchemeComponent.WORD_COLOR].config(bg=color)
        self.word.color = color

    def _set_syllable_color(self, color: str):
        self.color_scheme[ColorSchemeComponent.SYLLABLE_COLOR] = color
        self.previews[ColorSchemeComponent.SYLLABLE_COLOR].config(bg=color)

        for syllable in self.word.syllables:
            syllable.color = color
        for consonant in self.consonants:
            consonant.color = color

    def _set_vowel_color(self, color: str):
        self.color_scheme[ColorSchemeComponent.VOWEL_COLOR] = color
        self.previews[ColorSchemeComponent.VOWEL_COLOR].config(bg=color)

        for vowel in self.vowels:
            vowel.color = color

    def _set_dot_color(self, color: str):
        self.color_scheme[ColorSchemeComponent.DOT_COLOR] = color
        self.previews[ColorSchemeComponent.DOT_COLOR].config(bg=color)

        for consonant in self.dots:
            consonant.color = color

    def _reset_scheme(self):
        """Return to the default color scheme."""
        reset_color_scheme(self.color_scheme)
        self._set_canvas_background(self.color_scheme[ColorSchemeComponent.CANVAS_BG])
        self._set_word_background(self.color_scheme[ColorSchemeComponent.WORD_BG])
        self._set_syllable_background(self.color_scheme[ColorSchemeComponent.SYLLABLE_BG])
        self._set_word_color(self.color_scheme[ColorSchemeComponent.WORD_COLOR])
        self._set_syllable_color(self.color_scheme[ColorSchemeComponent.SYLLABLE_COLOR])
        self._set_vowel_color(self.color_scheme[ColorSchemeComponent.VOWEL_COLOR])
        self._set_dot_color(self.color_scheme[ColorSchemeComponent.DOT_COLOR])
        self._redraw()

    def _draw(self):
        """Draws the word preview on the canvas."""
        self.word.put_image(self.canvas)

    def _redraw(self):
        """Applies the selected color changes and updates the preview."""
        self.word.apply_color_changes()
        self._draw()
