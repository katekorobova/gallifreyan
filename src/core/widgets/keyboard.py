import tkinter as tk

from PIL import Image, ImageTk

from ...core import repository
from ...core.writing.characters import LetterType
from ...config import (WINDOW_BG, BUTTON_BG, FONT,
                        BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_IMAGE_SIZE)


class CharacterButton(tk.Button):
    """A button representing a single character."""
    def __init__(self, master: tk.Frame, character: str, entry: tk.Entry):
        super().__init__(master, text=character, font=FONT,
                         height=BUTTON_HEIGHT, width=BUTTON_WIDTH,
                         command=lambda: entry.insert(tk.INSERT, character))


class LettersFrame(tk.Frame):
    """A frame containing buttons for letter input."""
    def __init__(self, typ: LetterType, win: tk.Tk, entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self.images = []
        self._create_table(typ, entry)

    def _create_table(self, letter_type: LetterType, entry: tk.Entry):
        """Adds letter buttons and image labels to the frame."""
        tk.Label(self, relief='raised', bg=BUTTON_BG).grid(row=0, column=0, sticky='news')
        rep = repository.get()
        borders = rep.borders[letter_type]
        types = rep.types[letter_type]
        letters = rep.tables[letter_type]
        disabled = rep.disabled[letter_type]

        letter_type_str = 'consonants' if letter_type == LetterType.CONSONANT else 'vowels'
        for i, border in enumerate(borders):
            label = self._create_label(f'src/assets/images/borders/{border}.png')
            label.grid(row=i + 1, column=0, sticky='news')

        for j, typ in enumerate(types):
            label = self._create_label(f'src/assets/images/types/{letter_type_str}/{typ}.png')
            label.grid(row=0, column=j+1)

        self._create_buttons(letters, disabled, entry)

    def _create_label(self, path: str) -> tk.Label:
        """Creates a label with an image"""
        image = Image.open(path).resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
        image_tk = ImageTk.PhotoImage(image)
        self.images.append(image_tk)
        return tk.Label(self, image=image_tk, bg=BUTTON_BG, relief='raised')

    def _create_buttons(self, letters: list[list[str]], disabled: list[str], entry: tk.Entry):
        """Creates buttons for each letter in the grid, disabling specified letters."""
        for i, row in enumerate(letters):
            for j, letter in enumerate(row):
                button = CharacterButton(self, letter, entry)
                button.grid(row=i + 1, column=j + 1, sticky='news')

                if letter in disabled:
                    button.config(state='disabled')


class SpecialCharactersFrame(tk.Frame):
    """A frame containing buttons for special characters."""
    def __init__(self, win: tk.Misc, entry: tk.Entry):
        super().__init__(win, bg=WINDOW_BG)
        self._create_buttons(['-', ' '], entry)

    def _create_buttons(self, characters: list[str], entry: tk.Entry):
        """Creates and places buttons for special characters."""
        for i, character in enumerate(characters):
            button = CharacterButton(self, character, entry)
            button.grid(row=0, column=i, sticky='news')
