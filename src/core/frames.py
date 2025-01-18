import logging
import tkinter as tk

from PIL import Image, ImageTk

from . import repository
from .writing.characters import LetterType
from .writing.sentences import Sentence
from ..config import (WINDOW_BG, CANVAS_BG, BUTTON_BG,
                      BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_IMAGE_SIZE,
                      CANVAS_WIDTH, CANVAS_HEIGHT, FONT)


class CharacterButton(tk.Button):
    def __init__(self, master: tk.Frame, character: str, entry: tk.Entry):
        super().__init__(master, text=character, font=FONT,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH,
                         command=lambda: entry.insert(tk.INSERT, character))


class LettersFrame(tk.Frame):
    def __init__(self, typ: LetterType, win: tk.Tk, entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
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
                button = CharacterButton(self, letter, entry)
                button.grid(row=i + 1, column=j + 1, sticky='news')

                if letter in disabled:
                    button.config(state='disabled')


class SpecialCharactersFrame(tk.Frame):
    def __init__(self, win: tk.Tk, entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self._add_buttons(['-', ' '], entry)

    def _add_buttons(self, characters: list[str], entry: tk.Entry):
        for i, character in enumerate(characters):
            button = CharacterButton(self, character, entry)
            button.grid(row=0, column=i, sticky='news')


class CanvasFrame(tk.Frame):

    def __init__(self, win: tk.Tk):
        super().__init__(win, bg=WINDOW_BG)
        self.sentence = Sentence()

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

    def perform_animation(self):
        self.sentence.perform_animation()
        self._redraw()

    def _bind_canvas_events(self):
        """Bind mouse events to canvas actions."""
        self.canvas.bind('<Button-1>', self._press)
        self.canvas.bind('<B1-Motion>', self._move)
        self.canvas.bind('<ButtonRelease-1>', self._release)

    def _press(self, event: tk.Event):
        """Handle mouse button press on canvas."""
        self.sentence.press(event)

    def _move(self, event: tk.Event):
        """Handle mouse drag movement."""
        if self.sentence.move(event):
            self._redraw()

    def _release(self, _):
        """Handle mouse button release."""
        self.sentence.release()

    def _redraw(self):
        self.sentence.put_image(self.canvas)

    def apply_color_changes(self):
        self.sentence.apply_color_changes()
        self.sentence.put_image(self.canvas)

    def _attempt_action(self, action: str, str_index: str, inserted: str) -> bool:
        try:
            index = int(str_index)
            match action:
                case '0':  # Deletion
                    self.sentence.remove_characters(index, inserted)
                    self._redraw()
                    return True

                case '1':  # Insertion
                    valid = all(i in repository.get().all for i in inserted)
                    if valid:
                        self.sentence.insert_characters(index, inserted)
                        self._redraw()
                        return True
                    else:
                        return False

                case _:
                    return False

        except Exception as e:
            logging.exception(e)
            return False
