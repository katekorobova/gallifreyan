import tkinter as tk

from PIL import Image, ImageTk

from . import DefaultLabel, DefaultWindow, DefaultFrame
from ..utils import Point
from ..writing.characters import CharacterType
from ...config import (PRESSED_BG, ITEM_BG, PRIMARY_FONT, PADX, PADY,
                       BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_IMAGE_SIZE,
                       TEXT_COLOR, DISABLED_TEXT_COLOR, LABEL_TEXT_COLOR, SEPARATOR, SPACE)
from ...core import repository

BORDER_FILE_PATH = 'src/assets/images/borders/{}.png'
TYPE_FILE_PATH = 'src/assets/images/types/{}/{}.png'

padx = (0, PADX)
pady = (0, PADY)


class CharacterButton(tk.Button):
    """A button representing a single character."""

    def __init__(self, master: tk.Misc, entry: tk.Entry, character: str):
        super().__init__(master, text=character, font=PRIMARY_FONT, fg=TEXT_COLOR, bg=ITEM_BG,
                         activeforeground=LABEL_TEXT_COLOR, activebackground=PRESSED_BG,
                         disabledforeground=DISABLED_TEXT_COLOR,
                         width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                         command=lambda: entry.insert(tk.INSERT, character))


class TableFrame(DefaultFrame):
    """A frame containing buttons for letter input."""

    def __init__(self, typ: CharacterType, win: tk.Misc, entry: tk.Entry):
        super().__init__(win)
        self.images = []
        self._create_table(typ, entry)

    def _create_table(self, character_type: CharacterType, entry: tk.Entry) -> None:
        """Adds letter buttons and image labels to the frame."""
        self._create_label().grid(row=0, column=0, sticky=tk.NSEW)
        rep = repository.get()
        borders = rep.borders[character_type]
        types = rep.types[character_type]
        characters = rep.tables[character_type]

        path_dictionary: dict[CharacterType, str] = {
            CharacterType.CONSONANT: 'consonants',
            CharacterType.VOWEL: 'vowels',
            CharacterType.DIGIT: 'digits'
        }

        for i, border in enumerate(borders):
            label = self._create_label(BORDER_FILE_PATH.format(border))
            label.grid(row=i + 1, column=0, sticky=tk.NSEW)

        for j, typ in enumerate(types):
            label = self._create_label(TYPE_FILE_PATH.format(path_dictionary[character_type], typ))
            label.grid(row=0, column=j + 1, sticky=tk.NSEW)

        for i, row in enumerate(characters):
            for j, character in enumerate(row):
                button = CharacterButton(self, entry, character)
                button.grid(row=i + 1, column=j + 1, sticky=tk.NSEW)

                if character in rep.disabled:
                    button.config(state='disabled')

    def _create_label(self, path: str = None) -> tk.Label:
        """Creates a label with an image"""
        label = tk.Label(self, bg=PRESSED_BG, relief=tk.RAISED)
        if path:
            image = Image.open(path).resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            # noinspection PyTypeChecker
            label.configure(image=image_tk)
        return label


class ColumnFrame(DefaultFrame):
    """A frame containing buttons for letter input."""

    def __init__(self, typ: CharacterType, master: tk.Misc, entry: tk.Entry):
        super().__init__(master)
        self.images = []
        self._create_column(typ, entry)

    def _create_column(self, character_type: CharacterType, entry: tk.Entry):
        """Adds letter buttons and image labels to the frame."""
        rep = repository.get()
        borders = rep.borders[character_type]
        characters = rep.columns[character_type]
        descriptions = rep.descriptions[character_type]

        for i, (border, character, description) in enumerate(zip(borders, characters, descriptions)):
            label = self._create_label(BORDER_FILE_PATH.format(border))
            label.grid(row=i, column=0, sticky=tk.NSEW)

            button = CharacterButton(self, entry, character)
            button.grid(row=i, column=1, sticky=tk.NSEW)

            description = DefaultLabel(self, text=description)
            description.grid(row=i, column=2, sticky=tk.W)

            if character in rep.disabled:
                button.config(state='disabled')

    def _create_label(self, path: str = None) -> tk.Label:
        """Creates a label with an image"""
        label = tk.Label(self, bg=PRESSED_BG, relief=tk.RAISED)
        if path:
            image = Image.open(path).resize((BUTTON_IMAGE_SIZE, BUTTON_IMAGE_SIZE))
            image_tk = ImageTk.PhotoImage(image)
            self.images.append(image_tk)
            # noinspection PyTypeChecker
            label.configure(image=image_tk)
        return label


class ConsonantsWindow(DefaultWindow):
    """A toplevel window containing buttons for letter input."""
    def __init__(self, win: tk.Tk, entry: tk.Entry, position: Point = None):
        super().__init__(win, 'Consonants')
        consonants_table = TableFrame(CharacterType.CONSONANT, self, entry)
        consonants_table.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=tk.NSEW)

        if position:
            self.place(position)


class VowelsWindow(DefaultWindow):
    """A toplevel window containing buttons for letter input."""
    def __init__(self, win: tk.Tk, entry: tk.Entry, position: Point = None):
        super().__init__(win, 'Vowels')
        vowels_table = TableFrame(CharacterType.VOWEL, self, entry)
        vowels_table.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=tk.NSEW)

        if position:
            self.place(position)


class NumbersWindow(DefaultWindow):
    """A toplevel window containing buttons for letter input."""
    def __init__(self, win: tk.Tk, entry: tk.Entry, position: Point = None):
        super().__init__(win, 'Numbers')

        digits_table = TableFrame(CharacterType.DIGIT, self, entry)
        marks_column = ColumnFrame(CharacterType.NUMBER_MARK, self, entry)

        digits_table.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=tk.NSEW)
        marks_column.grid(row=0, column=1, padx=padx, pady=PADY, sticky=tk.S)

        if position:
            self.place(position)


class SpecialCharactersWindow(DefaultWindow):
    """A frame containing buttons for special characters."""

    def __init__(self, win: tk.Tk, entry: tk.Entry, position: Point = None):
        super().__init__(win, 'Special Characters')
        table = self._create_table([(SPACE, 'Space'), (SEPARATOR, 'Syllable Separator')], entry)
        table.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=tk.W)

        if position:
            self.place(position)

    def _create_table(self, characters: list[tuple[str, str]], entry: tk.Entry) -> tk.Frame:
        """Creates and places buttons for special characters."""
        table = DefaultFrame(self)
        for i, (character, description) in enumerate(characters):
            button = CharacterButton(table, entry, character)
            label = DefaultLabel(table, text=description)

            button.grid(row=i, column=0, sticky=tk.NSEW)
            label.grid(row=i, column=1, sticky=tk.W)
        return table
