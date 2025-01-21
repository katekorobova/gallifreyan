import tkinter as tk

from PIL import Image, ImageTk

from . import DefaultFrame, DefaultLabel
from ...config import (PRESSED_BG, FRAME_BG, ITEM_BG, FONT, PADX, PADY,
                       BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_IMAGE_SIZE,
                       TEXT_COLOR, DISABLED_TEXT_COLOR, LABEL_TEXT_COLOR)
from ...core import repository
from ...core.writing.characters import LetterType

padx = (0, PADX)
pady = (0, PADY)


class CharacterButton(tk.Button):
    """A button representing a single character."""

    def __init__(self, master: tk.Frame, character: str, entry: tk.Entry):
        super().__init__(master, text=character, font=FONT, fg=TEXT_COLOR, bg=ITEM_BG,
                         activeforeground=LABEL_TEXT_COLOR, activebackground=PRESSED_BG,
                         disabledforeground=DISABLED_TEXT_COLOR,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH,
                         command=lambda: entry.insert(tk.INSERT, character))


class LettersFrame(DefaultFrame):
    """A frame containing buttons for letter input."""

    def __init__(self, typ: LetterType, win: tk.Tk, entry: tk.Entry):
        super().__init__(win)
        self.images = []
        label = DefaultLabel(self, text='Consonants' if typ == LetterType.CONSONANT else 'Vowels')
        table = self._create_table(typ, entry)

        label.grid(row=0, column=0, padx=PADX, sticky=tk.W)
        table.grid(row=1, column=0, padx=PADX, pady=pady, sticky=tk.NSEW)

    def _create_table(self, letter_type: LetterType, entry: tk.Entry) -> tk.Frame:
        """Adds letter buttons and image labels to the frame."""
        table = tk.Frame(self, bg=FRAME_BG)
        self._create_label(table).grid(row=0, column=0, sticky=tk.NSEW)
        rep = repository.get()
        borders = rep.borders[letter_type]
        types = rep.types[letter_type]
        letters = rep.tables[letter_type]
        disabled = rep.disabled[letter_type]

        letter_type_str = 'consonants' if letter_type == LetterType.CONSONANT else 'vowels'
        for i, border in enumerate(borders):
            label = self._create_label(table, f'src/assets/images/borders/{border}.png')
            label.grid(row=i + 1, column=0, sticky=tk.NSEW)

        for j, typ in enumerate(types):
            label = self._create_label(
                table, f'src/assets/images/types/{letter_type_str}/{typ}.png')
            label.grid(row=0, column=j + 1, sticky=tk.NSEW)

        for i, row in enumerate(letters):
            for j, letter in enumerate(row):
                button = CharacterButton(table, letter, entry)
                button.grid(row=i + 1, column=j + 1, sticky=tk.NSEW)

                if letter in disabled:
                    button.config(state='disabled')

        return table

    def _create_label(self, master: tk.Frame, path: str = None) -> tk.Label:
        """Creates a label with an image"""
        label = tk.Label(master, bg=PRESSED_BG, relief=tk.RAISED)
        if path:
            image = Image.open(path).resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            label.configure(image=image_tk)
        return label


class SpecialCharactersFrame(DefaultFrame):
    """A frame containing buttons for special characters."""

    def __init__(self, win: tk.Misc, entry: tk.Entry):
        super().__init__(win)
        label = DefaultLabel(self, text='Special Characters')
        table = self._create_table(['-', ' '], entry)

        label.grid(row=0, column=0, padx=PADX, sticky=tk.W)
        table.grid(row=1, column=0, padx=PADX, pady=pady, sticky=tk.W)

    def _create_table(self, characters: list[str], entry: tk.Entry) -> tk.Frame:
        """Creates and places buttons for special characters."""
        table = tk.Frame(self, bg=FRAME_BG)
        for i, character in enumerate(characters):
            button = CharacterButton(table, character, entry)
            button.grid(row=0, column=i, sticky=tk.NSEW)
        return table
