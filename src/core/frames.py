import logging
import tkinter as tk
from typing import Optional

from PIL import Image, ImageTk

from . import repository
from .components.consonants import Consonant
from .components.characters import CharacterType, LetterType, Separator, Character
from .components.vowels import Vowel
from .components.words import Word
from .utils import Point
from ..config import (FONT, WINDOW_BG, BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_IMAGE_SIZE,
                      CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_BG, WORD_INITIAL_POSITION, BUTTON_BG)


def get_character(text: str, typ: CharacterType, args: Optional[list]) -> Character:
    def get_letter(letter_text: str, letter_type: LetterType, *letter_args):
        if letter_type == LetterType.CONSONANT:
            return Consonant.get_consonant(letter_text, *letter_args)
        elif letter_type == LetterType.VOWEL:
            return Vowel.get_vowel(letter_text, *letter_args)
        else:
            raise ValueError(f'There is no such letter type: {letter_type} (symbol={letter_text})')

    if typ == CharacterType.LETTER:
        return get_letter(text, *args)
    elif typ == CharacterType.SEPARATOR:
        return Separator(text)
    else:
        raise ValueError(f'There is no such character type: {typ} (symbol={text})')


class LetterButton(tk.Button):
    def __init__(self, master: tk.Frame, letter: str, entry: tk.Entry):
        super().__init__(master, text=letter, font=FONT,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH,
                         command=lambda: entry.insert(tk.INSERT, letter))


class LetterFrame(tk.Frame):
    def __init__(self, typ: LetterType, win: tk.Tk, entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
        self.buttons: dict[str, tk.Button] = {}
        self._initialize_grid(typ, entry)

    def _initialize_grid(self, letter_type: LetterType, entry: tk.Entry):
        tk.Label(self, relief='raised', bg=BUTTON_BG).grid(row=0, column=0, sticky='news')
        rep = repository.get()
        borders = rep.borders[letter_type]
        types = rep.types[letter_type]
        letters = rep.tables[letter_type]
        disabled = rep.disabled[letter_type]

        letter_type_str = 'consonants' if letter_type == LetterType.CONSONANT else 'vowels'
        for i, border in enumerate(borders):
            self._add_label(f'src/assets/images/borders/{border}.png', row=i + 1, column=0)

        for j, typ in enumerate(types):
            self._add_label(f'src/assets/images/types/{letter_type_str}/{typ}.png', row=0, column=j + 1)

        self._add_buttons(letters, disabled, entry)

    def _add_label(self, path: str, row: int, column: int):
        image = Image.open(path).resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
        image_tk = ImageTk.PhotoImage(image)
        self.images.append(image_tk)
        tk.Label(self, image=image_tk, bg=BUTTON_BG, relief='raised').grid(row=row, column=column, sticky='news')

    def _add_buttons(self, letters: list[list[str]], disabled: list[str], entry: tk.Entry):
        for i, row in enumerate(letters):
            for j, letter in enumerate(row):
                button = LetterButton(self, letter, entry)
                self.buttons[letter] = button
                button.grid(row=i + 1, column=j + 1, sticky='news')

                if letter in disabled:
                    button.config(state='disabled')


class SeparatorFrame(tk.Frame):
    def __init__(self, character: str, win: tk.Tk, entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
        self.button: tk.Button = tk.Button(self, text=character, font=FONT,
                                            height=BUTTON_HEIGHT, width=BUTTON_WIDTH,
                                            command=lambda: entry.insert(tk.INSERT, character))

        self.button.grid(row=0, column=0, sticky='news')


class CanvasFrame(tk.Frame):

    def __init__(self, win: tk.Tk):
        super().__init__(win, bg=WINDOW_BG)
        self.word: Optional[Word] = None
        self.pressed: Optional[Word] = None

        # Entry widget with validation
        self.entry = tk.Entry(
            self, font=FONT, validate='key',
            validatecommand=(self.register(self._attempt_action), '%d', '%i', '%S'),
        )
        self.entry.grid(row=0, column=0, sticky='news')

        # Canvas for drawing
        self.canvas = tk.Canvas(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=CANVAS_BG)
        self.canvas.grid(row=1, column=0)

        # Canvas event bindings
        self._bind_canvas_events()

    def _bind_canvas_events(self):
        """Bind mouse events to canvas actions."""
        self.canvas.bind('<Button-1>', self._press)
        self.canvas.bind('<B1-Motion>', self._move)
        self.canvas.bind('<ButtonRelease-1>', self._release)

    def _press(self, event: tk.Event):
        """Handle mouse button press on canvas."""
        if self.word and self.word.press(Point(event.x, event.y)):
            self.pressed = self.word

    def _move(self, event: tk.Event):
        """Handle mouse drag movement."""
        if self.pressed:
            self.pressed.move(Point(event.x, event.y))
            self._redraw()

    def _release(self, _):
        """Handle mouse button release."""
        self.pressed = None

    def _redraw(self):
        # self.canvas.delete('all')
        if self.word:
            self.word.create_image(self.canvas)

    def _attempt_action(self, action: str, str_index: str, inserted: str) -> bool:
        try:
            index = int(str_index)
            match action:
                case '0':  # Deletion
                    self._remove_characters(index, inserted)
                    return True

                case '1':  # Insertion
                    valid = all(i in repository.get().all for i in inserted)
                    if valid:
                        self._insert_characters(index, inserted)
                        return True
                    else:
                        return False

                case _:
                    return False

        except Exception as e:
            logging.exception(e)
            return False

    def _remove_characters(self, index: int, deleted: str):
        """Remove letters from the word and update syllables."""
        if self.word:
            self.word.remove_characters(index, deleted)
            if not self.word.syllables_by_indices:
                self.canvas.delete(self.word.canvas_item_id)
                self.word = None
                self.pressed = None

            self._redraw()

    def _insert_characters(self, index: int, inserted: str):
        """Insert characters at a specific index and update syllables."""
        characters = [get_character(character, *repository.get().all[character])
                      for character in inserted]
        if self.word:
            self.word.insert_characters(index, characters)
        else:
            self.word = Word(Point(*WORD_INITIAL_POSITION), characters)
        self._redraw()

    def get_image(self):
        if self.word:
            return self.word.get_image()
